"""
Intelligent Matching Engine для сопоставления стартапов и венчурных фондов
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import math
from collections import defaultdict

from app.core.database import get_db
from app.data.models import Startup, VCFund, Communication
from app.data.repositories import (
    startup_repository, vc_fund_repository, communication_repository
)

logger = logging.getLogger(__name__)


class MatchQuality(Enum):
    """Качество сопоставления"""
    EXCELLENT = "excellent"  # 90-100%
    VERY_GOOD = "very_good"  # 80-89%
    GOOD = "good"  # 70-79%
    FAIR = "fair"  # 60-69%
    POOR = "poor"  # <60%


class ExclusionReason(Enum):
    """Причины исключения фонда"""
    RECENT_PITCH = "recent_pitch"
    GEOGRAPHY_MISMATCH = "geography_mismatch"
    STAGE_MISMATCH = "stage_mismatch"
    INDUSTRY_MISMATCH = "industry_mismatch"
    TICKET_SIZE_MISMATCH = "ticket_size_mismatch"
    CUSTOM_RULE = "custom_rule"
    FUND_INACTIVE = "fund_inactive"
    STARTUP_BLACKLISTED = "startup_blacklisted"


@dataclass
class MatchScore:
    """Оценка сопоставления"""
    total_score: float
    industry_score: float
    stage_score: float
    geography_score: float
    ticket_size_score: float
    quality: MatchQuality
    weighted_criteria: Dict[str, float]
    bonus_points: float = 0.0
    penalty_points: float = 0.0


@dataclass
class MatchingResult:
    """Результат сопоставления"""
    fund_id: int
    fund_name: str
    match_score: MatchScore
    explanation: Dict[str, Any]
    exclusion_reasons: List[ExclusionReason]
    is_eligible: bool
    last_pitch_date: Optional[datetime] = None
    custom_rules_applied: List[str] = None


@dataclass
class MatchingCriteria:
    """Критерии сопоставления"""
    industry_weight: float = 0.40
    stage_weight: float = 0.30
    geography_weight: float = 0.20
    ticket_size_weight: float = 0.10
    
    def __post_init__(self):
        # Нормализуем веса
        total_weight = (self.industry_weight + self.stage_weight + 
                       self.geography_weight + self.ticket_size_weight)
        
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(f"Weights don't sum to 1.0: {total_weight}")
            # Нормализуем
            self.industry_weight /= total_weight
            self.stage_weight /= total_weight
            self.geography_weight /= total_weight
            self.ticket_size_weight /= total_weight


class MatchingEngine:
    """
    Интеллектуальный движок сопоставления стартапов и венчурных фондов
    """
    
    def __init__(self):
        self.criteria = MatchingCriteria()
        
        # Настройки
        self.exclusion_window_days = int(os.getenv('MATCHING_EXCLUSION_DAYS', '90'))  # 90 дней
        self.min_match_score = float(os.getenv('MIN_MATCH_SCORE', '0.6'))  # 60%
        self.max_results = int(os.getenv('MAX_MATCHING_RESULTS', '50'))
        
        # Кэш для оптимизации
        self.funds_cache = {}
        self.startups_cache = {}
        self.communications_cache = {}
        
        # Пользовательские правила
        self.custom_rules = {}
        
        # Статистика
        self.matching_stats = {
            'total_matches': 0,
            'successful_matches': 0,
            'excluded_funds': 0,
            'average_score': 0.0
        }
        
        logger.info("MatchingEngine initialized")
    
    async def find_matching_funds(self, startup_id: int, limit: int = 10, 
                                exclude_recent: bool = True) -> List[MatchingResult]:
        """
        Поиск подходящих венчурных фондов для стартапа
        """
        try:
            logger.info(f"Finding matching funds for startup {startup_id}")
            
            # Получаем данные стартапа
            startup_data = await self._get_startup_data(startup_id)
            if not startup_data:
                logger.error(f"Startup {startup_id} not found")
                return []
            
            # Получаем все активные фонды
            all_funds = await self._get_all_funds()
            if not all_funds:
                logger.error("No funds found")
                return []
            
            # Применяем фильтры исключения
            if exclude_recent:
                eligible_funds = await self.apply_exclusion_filters(all_funds, startup_id)
            else:
                eligible_funds = all_funds
            
            # Вычисляем оценки сопоставления
            matching_results = []
            for fund in eligible_funds:
                match_score = await self.calculate_match_score(startup_data, fund)
                explanation = await self.get_matching_explanation(startup_id, fund['id'])
                
                result = MatchingResult(
                    fund_id=fund['id'],
                    fund_name=fund['name'],
                    match_score=match_score,
                    explanation=explanation,
                    exclusion_reasons=[],
                    is_eligible=match_score.total_score >= self.min_match_score
                )
                
                matching_results.append(result)
            
            # Сортируем по оценке сопоставления
            matching_results.sort(key=lambda x: x.match_score.total_score, reverse=True)
            
            # Ограничиваем количество результатов
            top_results = matching_results[:limit]
            
            # Обновляем статистику
            await self._update_matching_stats(top_results)
            
            logger.info(f"Found {len(top_results)} matching funds for startup {startup_id}")
            return top_results
            
        except Exception as e:
            logger.error(f"Error finding matching funds for startup {startup_id}: {e}")
            return []
    
    async def calculate_match_score(self, startup_data: Dict[str, Any], 
                                  fund_data: Dict[str, Any]) -> MatchScore:
        """
        Вычисление оценки сопоставления между стартапом и фондом
        """
        try:
            # Вычисляем оценки по каждому критерию
            industry_score = self._calculate_industry_score(startup_data, fund_data)
            stage_score = self._calculate_stage_score(startup_data, fund_data)
            geography_score = self._calculate_geography_score(startup_data, fund_data)
            ticket_size_score = self._calculate_ticket_size_score(startup_data, fund_data)
            
            # Вычисляем взвешенную общую оценку
            total_score = (
                industry_score * self.criteria.industry_weight +
                stage_score * self.criteria.stage_weight +
                geography_score * self.criteria.geography_weight +
                ticket_size_score * self.criteria.ticket_size_weight
            )
            
            # Применяем бонусы и штрафы
            bonus_points = self._calculate_bonus_points(startup_data, fund_data)
            penalty_points = self._calculate_penalty_points(startup_data, fund_data)
            
            final_score = min(1.0, max(0.0, total_score + bonus_points - penalty_points))
            
            # Определяем качество сопоставления
            quality = self._determine_match_quality(final_score)
            
            return MatchScore(
                total_score=final_score,
                industry_score=industry_score,
                stage_score=stage_score,
                geography_score=geography_score,
                ticket_size_score=ticket_size_score,
                quality=quality,
                weighted_criteria={
                    'industry': industry_score * self.criteria.industry_weight,
                    'stage': stage_score * self.criteria.stage_weight,
                    'geography': geography_score * self.criteria.geography_weight,
                    'ticket_size': ticket_size_score * self.criteria.ticket_size_weight
                },
                bonus_points=bonus_points,
                penalty_points=penalty_points
            )
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return MatchScore(
                total_score=0.0,
                industry_score=0.0,
                stage_score=0.0,
                geography_score=0.0,
                ticket_size_score=0.0,
                quality=MatchQuality.POOR,
                weighted_criteria={}
            )
    
    async def apply_exclusion_filters(self, funds_list: List[Dict[str, Any]], 
                                    startup_id: int) -> List[Dict[str, Any]]:
        """
        Применение фильтров исключения к списку фондов
        """
        try:
            filtered_funds = []
            exclusion_window = datetime.now() - timedelta(days=self.exclusion_window_days)
            
            # Получаем историю коммуникаций стартапа
            recent_communications = await self._get_recent_communications(startup_id, exclusion_window)
            contacted_fund_ids = {comm['vc_fund_id'] for comm in recent_communications}
            
            for fund in funds_list:
                # Проверяем недавние питчи
                if fund['id'] in contacted_fund_ids:
                    logger.debug(f"Excluding fund {fund['id']} - recent pitch")
                    continue
                
                # Проверяем пользовательские правила
                custom_excluded, reasons = await self._check_custom_rules(fund, startup_id)
                if custom_excluded:
                    logger.debug(f"Excluding fund {fund['id']} - custom rules: {reasons}")
                    continue
                
                # Проверяем базовые критерии
                if not self._meets_basic_criteria(fund):
                    logger.debug(f"Excluding fund {fund['id']} - doesn't meet basic criteria")
                    continue
                
                filtered_funds.append(fund)
            
            logger.info(f"Filtered {len(funds_list)} funds to {len(filtered_funds)} eligible funds")
            return filtered_funds
            
        except Exception as e:
            logger.error(f"Error applying exclusion filters: {e}")
            return funds_list
    
    async def get_matching_explanation(self, startup_id: int, fund_id: int) -> Dict[str, Any]:
        """
        Получение объяснения сопоставления
        """
        try:
            startup_data = await self._get_startup_data(startup_id)
            fund_data = await self._get_fund_data(fund_id)
            
            if not startup_data or not fund_data:
                return {"error": "Data not found"}
            
            explanation = {
                "startup_profile": {
                    "name": startup_data.get('name'),
                    "industry": startup_data.get('industry'),
                    "stage": startup_data.get('stage'),
                    "geography": startup_data.get('geography', 'Unknown'),
                    "funding_needed": startup_data.get('funding_needed')
                },
                "fund_profile": {
                    "name": fund_data.get('name'),
                    "focus_industries": fund_data.get('focus_industries', []),
                    "investment_stages": fund_data.get('investment_stages', []),
                    "geography": fund_data.get('geography'),
                    "ticket_size_range": f"{fund_data.get('ticket_size_min', 0):,.0f} - {fund_data.get('ticket_size_max', 0):,.0f}"
                },
                "match_analysis": {
                    "industry_match": self._analyze_industry_match(startup_data, fund_data),
                    "stage_match": self._analyze_stage_match(startup_data, fund_data),
                    "geography_match": self._analyze_geography_match(startup_data, fund_data),
                    "ticket_size_match": self._analyze_ticket_size_match(startup_data, fund_data)
                },
                "recommendation": self._generate_recommendation(startup_data, fund_data),
                "next_steps": self._suggest_next_steps(startup_data, fund_data)
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error getting matching explanation: {e}")
            return {"error": str(e)}
    
    def _calculate_industry_score(self, startup_data: Dict[str, Any], 
                                fund_data: Dict[str, Any]) -> float:
        """Вычисление оценки совпадения по индустрии"""
        startup_industry = startup_data.get('industry', '').lower()
        fund_industries = [ind.lower() for ind in fund_data.get('focus_industries', [])]
        
        if not fund_industries:
            return 0.0
        
        # Точное совпадение
        if startup_industry in fund_industries:
            return 1.0
        
        # Частичное совпадение (поиск подстрок)
        for fund_industry in fund_industries:
            if startup_industry in fund_industry or fund_industry in startup_industry:
                return 0.8
        
        # Семантическое совпадение (можно расширить с помощью ML)
        semantic_matches = {
            'technology': ['software', 'saas', 'ai', 'ml', 'tech'],
            'fintech': ['financial', 'payment', 'banking', 'fintech'],
            'healthcare': ['health', 'medical', 'pharma', 'biotech'],
            'ecommerce': ['retail', 'marketplace', 'commerce', 'shopping']
        }
        
        for category, keywords in semantic_matches.items():
            if (startup_industry == category and any(k in fund_industries for k in keywords)) or \
               (startup_industry in keywords and category in fund_industries):
                return 0.6
        
        return 0.0
    
    def _calculate_stage_score(self, startup_data: Dict[str, Any], 
                             fund_data: Dict[str, Any]) -> float:
        """Вычисление оценки совпадения по стадии"""
        startup_stage = startup_data.get('stage', '').lower()
        fund_stages = [stage.lower() for stage in fund_data.get('investment_stages', [])]
        
        if not fund_stages:
            return 0.0
        
        # Точное совпадение
        if startup_stage in fund_stages:
            return 1.0
        
        # Соседние стадии (более гибкое сопоставление)
        stage_hierarchy = ['pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'growth']
        stage_index = next((i for i, stage in enumerate(stage_hierarchy) if stage == startup_stage), -1)
        
        if stage_index >= 0:
            for fund_stage in fund_stages:
                fund_index = next((i for i, stage in enumerate(stage_hierarchy) if stage == fund_stage), -1)
                if fund_index >= 0:
                    # Соседние стадии получают 0.8, через одну - 0.6
                    distance = abs(stage_index - fund_index)
                    if distance == 1:
                        return 0.8
                    elif distance == 2:
                        return 0.6
        
        return 0.0
    
    def _calculate_geography_score(self, startup_data: Dict[str, Any], 
                                 fund_data: Dict[str, Any]) -> float:
        """Вычисление оценки совпадения по географии"""
        startup_geography = startup_data.get('geography', '').lower()
        fund_geography = fund_data.get('geography', '').lower()
        
        if not startup_geography or not fund_geography:
            return 0.5  # Нейтральная оценка при отсутствии данных
        
        # Точное совпадение
        if startup_geography == fund_geography:
            return 1.0
        
        # Региональные совпадения
        regional_matches = {
            'north_america': ['usa', 'canada', 'united states', 'us'],
            'europe': ['uk', 'germany', 'france', 'netherlands', 'sweden'],
            'asia': ['singapore', 'japan', 'korea', 'china', 'india'],
            'global': ['international', 'worldwide']
        }
        
        for region, countries in regional_matches.items():
            if (startup_geography in countries and fund_geography == region) or \
               (startup_geography == region and fund_geography in countries):
                return 0.8
        
        # Частичное совпадение (поиск подстрок)
        if startup_geography in fund_geography or fund_geography in startup_geography:
            return 0.6
        
        return 0.0
    
    def _calculate_ticket_size_score(self, startup_data: Dict[str, Any], 
                                   fund_data: Dict[str, Any]) -> float:
        """Вычисление оценки совпадения по размеру инвестиции"""
        startup_funding_needed = startup_data.get('funding_needed', 0)
        fund_min = fund_data.get('ticket_size_min', 0)
        fund_max = fund_data.get('ticket_size_max', float('inf'))
        
        if startup_funding_needed == 0 or fund_min == 0:
            return 0.5  # Нейтральная оценка при отсутствии данных
        
        # Проверяем попадание в диапазон
        if fund_min <= startup_funding_needed <= fund_max:
            return 1.0
        
        # Проверяем близость к диапазону
        if startup_funding_needed < fund_min:
            ratio = startup_funding_needed / fund_min
            if ratio >= 0.5:  # В пределах 50% от минимума
                return 0.8
            elif ratio >= 0.25:  # В пределах 25% от минимума
                return 0.6
        elif startup_funding_needed > fund_max:
            ratio = fund_max / startup_funding_needed
            if ratio >= 0.5:  # В пределах 50% от максимума
                return 0.8
            elif ratio >= 0.25:  # В пределах 25% от максимума
                return 0.6
        
        return 0.0
    
    def _calculate_bonus_points(self, startup_data: Dict[str, Any], 
                              fund_data: Dict[str, Any]) -> float:
        """Вычисление бонусных очков"""
        bonus = 0.0
        
        # Бонус за релевантный портфель
        startup_industry = startup_data.get('industry', '').lower()
        portfolio_companies = fund_data.get('portfolio_companies', [])
        
        relevant_companies = [
            company for company in portfolio_companies
            if startup_industry in company.get('industry', '').lower()
        ]
        
        if relevant_companies:
            bonus += 0.1 * min(len(relevant_companies), 3)  # До 0.3 бонуса
        
        # Бонус за успешные инвестиции в той же индустрии
        successful_exits = [
            company for company in portfolio_companies
            if (startup_industry in company.get('industry', '').lower() and 
                company.get('exit_status') == 'successful')
        ]
        
        if successful_exits:
            bonus += 0.05 * len(successful_exits)  # До 0.15 бонуса
        
        return min(bonus, 0.2)  # Максимум 20% бонуса
    
    def _calculate_penalty_points(self, startup_data: Dict[str, Any], 
                                fund_data: Dict[str, Any]) -> float:
        """Вычисление штрафных очков"""
        penalty = 0.0
        
        # Штраф за неактивность фонда
        last_investment = fund_data.get('last_investment_date')
        if last_investment:
            days_since_investment = (datetime.now() - last_investment).days
            if days_since_investment > 365:  # Более года без инвестиций
                penalty += 0.1
        
        # Штраф за переполненный портфель
        portfolio_size = len(fund_data.get('portfolio_companies', []))
        max_portfolio_size = fund_data.get('max_portfolio_size', 50)
        
        if portfolio_size > max_portfolio_size * 0.9:  # 90% заполнен
            penalty += 0.05
        
        return min(penalty, 0.15)  # Максимум 15% штрафа
    
    def _determine_match_quality(self, score: float) -> MatchQuality:
        """Определение качества сопоставления"""
        if score >= 0.90:
            return MatchQuality.EXCELLENT
        elif score >= 0.80:
            return MatchQuality.VERY_GOOD
        elif score >= 0.70:
            return MatchQuality.GOOD
        elif score >= 0.60:
            return MatchQuality.FAIR
        else:
            return MatchQuality.POOR
    
    async def _check_custom_rules(self, fund: Dict[str, Any], startup_id: int) -> Tuple[bool, List[str]]:
        """Проверка пользовательских правил"""
        exclusion_reasons = []
        
        # Проверяем правила фонда
        fund_custom_rules = self.custom_rules.get(fund['id'], [])
        for rule in fund_custom_rules:
            if await self._evaluate_rule(rule, fund, startup_id):
                exclusion_reasons.append(rule.get('reason', 'Custom rule violation'))
        
        return len(exclusion_reasons) > 0, exclusion_reasons
    
    async def _evaluate_rule(self, rule: Dict[str, Any], fund: Dict[str, Any], 
                           startup_id: int) -> bool:
        """Оценка пользовательского правила"""
        rule_type = rule.get('type')
        
        if rule_type == 'exclude_industry':
            startup_data = await self._get_startup_data(startup_id)
            if startup_data:
                excluded_industries = rule.get('industries', [])
                if startup_data.get('industry') in excluded_industries:
                    return True
        
        elif rule_type == 'exclude_stage':
            startup_data = await self._get_startup_data(startup_id)
            if startup_data:
                excluded_stages = rule.get('stages', [])
                if startup_data.get('stage') in excluded_stages:
                    return True
        
        elif rule_type == 'minimum_funding':
            startup_data = await self._get_startup_data(startup_id)
            if startup_data:
                min_funding = rule.get('minimum_amount', 0)
                if startup_data.get('funding_needed', 0) < min_funding:
                    return True
        
        return False
    
    def _meets_basic_criteria(self, fund: Dict[str, Any]) -> bool:
        """Проверка базовых критериев фонда"""
        # Фонд должен быть активным
        if not fund.get('is_active', True):
            return False
        
        # Фонд должен иметь минимальные требования
        if not fund.get('focus_industries'):
            return False
        
        return True
    
    async def batch_process_startups(self, startup_ids: List[int], 
                                   limit_per_startup: int = 10) -> Dict[int, List[MatchingResult]]:
        """
        Пакетная обработка нескольких стартапов
        """
        try:
            logger.info(f"Batch processing {len(startup_ids)} startups")
            
            results = {}
            
            # Обрабатываем стартапы параллельно
            tasks = []
            for startup_id in startup_ids:
                task = self.find_matching_funds(startup_id, limit_per_startup)
                tasks.append((startup_id, task))
            
            # Ждем завершения всех задач
            for startup_id, task in tasks:
                try:
                    matches = await task
                    results[startup_id] = matches
                except Exception as e:
                    logger.error(f"Error processing startup {startup_id}: {e}")
                    results[startup_id] = []
            
            logger.info(f"Batch processing completed for {len(results)} startups")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return {}
    
    async def _get_startup_data(self, startup_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных стартапа"""
        try:
            if startup_id in self.startups_cache:
                return self.startups_cache[startup_id]
            
            db = next(get_db())
            startup = db.query(Startup).filter(Startup.id == startup_id).first()
            
            if not startup:
                return None
            
            startup_data = {
                'id': startup.id,
                'name': startup.name,
                'industry': startup.industry,
                'stage': startup.stage,
                'geography': getattr(startup, 'geography', 'Unknown'),
                'funding_needed': getattr(startup, 'funding_needed', 0),
                'description': startup.description,
                'email': startup.email,
                'contact_person': startup.contact_person
            }
            
            # Кэшируем на 5 минут
            self.startups_cache[startup_id] = startup_data
            
            return startup_data
            
        except Exception as e:
            logger.error(f"Error getting startup data for {startup_id}: {e}")
            return None
    
    async def _get_fund_data(self, fund_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных фонда"""
        try:
            if fund_id in self.funds_cache:
                return self.funds_cache[fund_id]
            
            db = next(get_db())
            fund = db.query(VCFund).filter(VCFund.id == fund_id).first()
            
            if not fund:
                return None
            
            fund_data = {
                'id': fund.id,
                'name': fund.name,
                'focus_industries': fund.focus_industries or [],
                'investment_stages': fund.investment_stages or [],
                'geography': fund.geography,
                'ticket_size_min': fund.ticket_size_min,
                'ticket_size_max': fund.ticket_size_max,
                'email': fund.email,
                'contact_info': fund.contact_info or {},
                'is_active': getattr(fund, 'is_active', True),
                'portfolio_companies': getattr(fund, 'portfolio_companies', []),
                'last_investment_date': getattr(fund, 'last_investment_date', None),
                'max_portfolio_size': getattr(fund, 'max_portfolio_size', 50)
            }
            
            # Кэшируем на 5 минут
            self.funds_cache[fund_id] = fund_data
            
            return fund_data
            
        except Exception as e:
            logger.error(f"Error getting fund data for {fund_id}: {e}")
            return None
    
    async def _get_all_funds(self) -> List[Dict[str, Any]]:
        """Получение всех активных фондов"""
        try:
            if self.funds_cache.get('all_funds'):
                return self.funds_cache['all_funds']
            
            db = next(get_db())
            funds = db.query(VCFund).filter(VCFund.is_active == True).all()
            
            funds_data = []
            for fund in funds:
                fund_data = {
                    'id': fund.id,
                    'name': fund.name,
                    'focus_industries': fund.focus_industries or [],
                    'investment_stages': fund.investment_stages or [],
                    'geography': fund.geography,
                    'ticket_size_min': fund.ticket_size_min,
                    'ticket_size_max': fund.ticket_size_max,
                    'is_active': getattr(fund, 'is_active', True)
                }
                funds_data.append(fund_data)
            
            # Кэшируем на 2 минуты
            self.funds_cache['all_funds'] = funds_data
            
            return funds_data
            
        except Exception as e:
            logger.error(f"Error getting all funds: {e}")
            return []
    
    async def _get_recent_communications(self, startup_id: int, 
                                      since_date: datetime) -> List[Dict[str, Any]]:
        """Получение недавних коммуникаций стартапа"""
        try:
            cache_key = f"communications_{startup_id}_{since_date.isoformat()}"
            if cache_key in self.communications_cache:
                return self.communications_cache[cache_key]
            
            db = next(get_db())
            communications = db.query(Communication).filter(
                Communication.startup_id == startup_id,
                Communication.created_at >= since_date
            ).all()
            
            communications_data = [
                {
                    'id': comm.id,
                    'vc_fund_id': comm.vc_fund_id,
                    'status': comm.status,
                    'created_at': comm.created_at
                }
                for comm in communications
            ]
            
            # Кэшируем на 1 минуту
            self.communications_cache[cache_key] = communications_data
            
            return communications_data
            
        except Exception as e:
            logger.error(f"Error getting recent communications: {e}")
            return []
    
    def _analyze_industry_match(self, startup_data: Dict[str, Any], 
                              fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ совпадения по индустрии"""
        startup_industry = startup_data.get('industry')
        fund_industries = fund_data.get('focus_industries', [])
        
        match_type = "no_match"
        confidence = 0.0
        
        if startup_industry in fund_industries:
            match_type = "exact_match"
            confidence = 1.0
        elif any(startup_industry in ind or ind in startup_industry for ind in fund_industries):
            match_type = "partial_match"
            confidence = 0.8
        
        return {
            "startup_industry": startup_industry,
            "fund_industries": fund_industries,
            "match_type": match_type,
            "confidence": confidence
        }
    
    def _analyze_stage_match(self, startup_data: Dict[str, Any], 
                           fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ совпадения по стадии"""
        startup_stage = startup_data.get('stage')
        fund_stages = fund_data.get('investment_stages', [])
        
        match_type = "no_match"
        confidence = 0.0
        
        if startup_stage in fund_stages:
            match_type = "exact_match"
            confidence = 1.0
        else:
            # Проверяем соседние стадии
            stage_hierarchy = ['pre_seed', 'seed', 'series_a', 'series_b', 'series_c']
            startup_index = next((i for i, stage in enumerate(stage_hierarchy) if stage == startup_stage), -1)
            
            if startup_index >= 0:
                for fund_stage in fund_stages:
                    fund_index = next((i for i, stage in enumerate(stage_hierarchy) if stage == fund_stage), -1)
                    if fund_index >= 0:
                        distance = abs(startup_index - fund_index)
                        if distance == 1:
                            match_type = "adjacent_match"
                            confidence = 0.8
                        elif distance == 2:
                            match_type = "near_match"
                            confidence = 0.6
        
        return {
            "startup_stage": startup_stage,
            "fund_stages": fund_stages,
            "match_type": match_type,
            "confidence": confidence
        }
    
    def _analyze_geography_match(self, startup_data: Dict[str, Any], 
                               fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ совпадения по географии"""
        startup_geography = startup_data.get('geography', 'Unknown')
        fund_geography = fund_data.get('geography')
        
        match_type = "no_match"
        confidence = 0.0
        
        if startup_geography == fund_geography:
            match_type = "exact_match"
            confidence = 1.0
        elif startup_geography in fund_geography or fund_geography in startup_geography:
            match_type = "partial_match"
            confidence = 0.6
        
        return {
            "startup_geography": startup_geography,
            "fund_geography": fund_geography,
            "match_type": match_type,
            "confidence": confidence
        }
    
    def _analyze_ticket_size_match(self, startup_data: Dict[str, Any], 
                                 fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ совпадения по размеру инвестиции"""
        startup_funding = startup_data.get('funding_needed', 0)
        fund_min = fund_data.get('ticket_size_min', 0)
        fund_max = fund_data.get('ticket_size_max', 0)
        
        match_type = "no_match"
        confidence = 0.0
        
        if startup_funding == 0 or fund_min == 0:
            match_type = "no_data"
            confidence = 0.5
        elif fund_min <= startup_funding <= fund_max:
            match_type = "exact_match"
            confidence = 1.0
        elif startup_funding < fund_min:
            ratio = startup_funding / fund_min
            if ratio >= 0.5:
                match_type = "near_minimum"
                confidence = 0.8
            elif ratio >= 0.25:
                match_type = "below_minimum"
                confidence = 0.6
        else:
            ratio = fund_max / startup_funding
            if ratio >= 0.5:
                match_type = "near_maximum"
                confidence = 0.8
            elif ratio >= 0.25:
                match_type = "above_maximum"
                confidence = 0.6
        
        return {
            "startup_funding_needed": startup_funding,
            "fund_min_ticket": fund_min,
            "fund_max_ticket": fund_max,
            "match_type": match_type,
            "confidence": confidence
        }
    
    def _generate_recommendation(self, startup_data: Dict[str, Any], 
                               fund_data: Dict[str, Any]) -> str:
        """Генерация рекомендации"""
        recommendations = []
        
        # Анализируем совпадения
        industry_match = self._analyze_industry_match(startup_data, fund_data)
        stage_match = self._analyze_stage_match(startup_data, fund_data)
        
        if industry_match['match_type'] == 'exact_match':
            recommendations.append("Perfect industry alignment")
        elif industry_match['match_type'] == 'partial_match':
            recommendations.append("Strong industry relevance")
        
        if stage_match['match_type'] == 'exact_match':
            recommendations.append("Ideal investment stage match")
        elif stage_match['match_type'] == 'adjacent_match':
            recommendations.append("Good stage compatibility")
        
        if not recommendations:
            recommendations.append("Consider for portfolio diversification")
        
        return ". ".join(recommendations) + "."
    
    def _suggest_next_steps(self, startup_data: Dict[str, Any], 
                          fund_data: Dict[str, Any]) -> List[str]:
        """Предложение следующих шагов"""
        next_steps = [
            "Prepare personalized pitch deck",
            "Research fund's portfolio companies",
            "Identify mutual connections",
            "Schedule initial meeting"
        ]
        
        # Добавляем специфичные шаги на основе анализа
        industry_match = self._analyze_industry_match(startup_data, fund_data)
        if industry_match['match_type'] == 'exact_match':
            next_steps.insert(0, "Highlight industry expertise and market knowledge")
        
        return next_steps
    
    async def _update_matching_stats(self, results: List[MatchingResult]):
        """Обновление статистики сопоставления"""
        try:
            self.matching_stats['total_matches'] += len(results)
            
            successful_matches = [r for r in results if r.is_eligible]
            self.matching_stats['successful_matches'] += len(successful_matches)
            
            if results:
                avg_score = sum(r.match_score.total_score for r in results) / len(results)
                self.matching_stats['average_score'] = avg_score
            
        except Exception as e:
            logger.error(f"Error updating matching stats: {e}")
    
    def add_custom_rule(self, fund_id: int, rule: Dict[str, Any]):
        """Добавление пользовательского правила для фонда"""
        if fund_id not in self.custom_rules:
            self.custom_rules[fund_id] = []
        
        self.custom_rules[fund_id].append(rule)
        logger.info(f"Added custom rule for fund {fund_id}: {rule.get('type')}")
    
    def get_matching_stats(self) -> Dict[str, Any]:
        """Получение статистики сопоставления"""
        return self.matching_stats.copy()


# Глобальный экземпляр движка сопоставления
matching_engine = MatchingEngine()
