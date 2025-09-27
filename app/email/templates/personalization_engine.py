"""
Personalization Engine для динамической персонализации email шаблонов
"""
import os
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from app.email.templates.template_engine import PersonalizationData, template_engine

logger = logging.getLogger(__name__)


@dataclass
class PersonalizationContext:
    """Контекст персонализации"""
    vc_fund_data: Dict[str, Any]
    startup_data: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    timing_context: Dict[str, Any]


class PersonalizationEngine:
    """
    Движок персонализации для создания динамического контента
    """
    
    def __init__(self):
        self.template_engine = template_engine
        
        # База данных для персонализации
        self.industry_keywords = {
            'technology': ['AI', 'machine learning', 'cloud computing', 'SaaS', 'API'],
            'fintech': ['blockchain', 'digital payments', 'financial services', 'banking', 'lending'],
            'healthtech': ['telemedicine', 'digital health', 'medical devices', 'pharmaceuticals', 'healthcare'],
            'edtech': ['online learning', 'educational technology', 'e-learning', 'student management', 'assessment'],
            'ecommerce': ['online retail', 'marketplace', 'logistics', 'supply chain', 'customer experience'],
            'cybersecurity': ['data protection', 'threat detection', 'identity management', 'network security', 'compliance']
        }
        
        self.stage_descriptions = {
            'pre_seed': 'early-stage concept validation',
            'seed': 'product-market fit development',
            'series_a': 'rapid growth and expansion',
            'series_b': 'market leadership establishment',
            'series_c': 'international expansion and scaling'
        }
        
        self.investment_size_ranges = {
            'pre_seed': '$50K - $500K',
            'seed': '$500K - $3M',
            'series_a': '$3M - $15M',
            'series_b': '$15M - $50M',
            'series_c': '$50M - $200M'
        }
        
        # Персонализированные фразы
        self.personalization_phrases = {
            'greeting_formal': [
                "Dear {partner_name},",
                "Hello {partner_name},",
                "Good day {partner_name},"
            ],
            'greeting_casual': [
                "Hi {partner_name},",
                "Hey {partner_name},",
                "Hello there {partner_name},"
            ],
            'interest_expressions': [
                "We're excited about the potential partnership",
                "We believe there's a compelling strategic fit",
                "We see significant synergies with your portfolio",
                "We're confident this aligns with your investment thesis"
            ],
            'urgency_indicators': [
                "We're currently in discussions with other investors",
                "Our funding round is progressing quickly",
                "We have limited availability for new partnerships",
                "The market opportunity is time-sensitive"
            ]
        }
        
        logger.info("PersonalizationEngine initialized")
    
    def personalize_template(self, template_type: str, 
                           personalization_context: PersonalizationContext) -> PersonalizationData:
        """
        Создание персонализированных данных для шаблона
        """
        try:
            # Базовые данные
            vc_data = personalization_context.vc_fund_data
            startup_data = personalization_context.startup_data
            
            # Создаем базовые данные персонализации
            personalization_data = PersonalizationData(
                # VC данные
                vc_name=vc_data.get('name', 'Investment Partner'),
                fund_name=vc_data.get('name', 'Investment Fund'),
                partner_name=self._get_partner_name(vc_data),
                investment_focus=vc_data.get('focus_industries', []),
                recent_investments=vc_data.get('recent_investments', []),
                relevant_portfolio_company=self._find_relevant_portfolio_company(
                    vc_data, startup_data
                ),
                ticket_size_range=self._get_ticket_size_range(vc_data),
                
                # Startup данные
                startup_name=startup_data.get('name', 'Our Company'),
                startup_industry=startup_data.get('industry', 'Technology'),
                startup_stage=startup_data.get('stage', 'Seed'),
                contact_person=startup_data.get('contact_person', 'The Team'),
                startup_email=startup_data.get('email', 'contact@company.com'),
                pitch_summary=startup_data.get('description', ''),
                
                # Контекстные данные
                previous_interaction=self._get_previous_interaction(
                    personalization_context.interaction_history
                ),
                specific_interest=self._determine_specific_interest(
                    vc_data, startup_data, personalization_context
                ),
                requested_documents=self._get_requested_documents(
                    personalization_context.interaction_history
                ),
                
                # Встреча данные
                meeting_availability=self._get_meeting_availability(
                    personalization_context.timing_context
                ),
                meeting_date=self._get_meeting_date(
                    personalization_context.timing_context
                ),
                meeting_time=self._get_meeting_time(
                    personalization_context.timing_context
                ),
                meeting_type=self._get_meeting_type(vc_data)
            )
            
            # Добавляем динамический контент на основе типа шаблона
            self._enhance_with_template_specific_data(
                personalization_data, template_type, personalization_context
            )
            
            logger.info(f"Personalization completed for template {template_type}")
            return personalization_data
            
        except Exception as e:
            logger.error(f"Error in personalization: {e}")
            # Возвращаем базовые данные в случае ошибки
            return self._get_fallback_personalization_data(personalization_context)
    
    def _get_partner_name(self, vc_data: Dict[str, Any]) -> str:
        """Получение имени партнера"""
        contact_info = vc_data.get('contact_info', {})
        
        # Приоритет: конкретное имя -> общий контакт -> название фонда
        if contact_info.get('partner_name'):
            return contact_info['partner_name']
        elif contact_info.get('name'):
            return contact_info['name']
        elif contact_info.get('title'):
            return f"{contact_info['title']} at {vc_data.get('name', 'the fund')}"
        else:
            return f"Investment Partner at {vc_data.get('name', 'your fund')}"
    
    def _find_relevant_portfolio_company(self, vc_data: Dict[str, Any], 
                                       startup_data: Dict[str, Any]) -> Optional[str]:
        """Поиск релевантной портфельной компании"""
        portfolio_companies = vc_data.get('portfolio_companies', [])
        startup_industry = startup_data.get('industry', '').lower()
        
        # Ищем компании в той же индустрии
        relevant_companies = [
            company for company in portfolio_companies
            if startup_industry in company.get('industry', '').lower()
        ]
        
        if relevant_companies:
            # Возвращаем случайную релевантную компанию
            return random.choice(relevant_companies)['name']
        
        # Если нет прямого совпадения, ищем похожие
        industry_keywords = self.industry_keywords.get(startup_industry, [])
        for company in portfolio_companies:
            company_industry = company.get('industry', '').lower()
            if any(keyword.lower() in company_industry for keyword in industry_keywords):
                return company['name']
        
        return None
    
    def _get_ticket_size_range(self, vc_data: Dict[str, Any]) -> Optional[str]:
        """Получение диапазона инвестиций"""
        min_size = vc_data.get('ticket_size_min')
        max_size = vc_data.get('ticket_size_max')
        
        if min_size and max_size:
            return f"${min_size:,.0f} - ${max_size:,.0f}"
        
        return None
    
    def _get_previous_interaction(self, interaction_history: List[Dict[str, Any]]) -> Optional[str]:
        """Получение информации о предыдущем взаимодействии"""
        if not interaction_history:
            return None
        
        # Берем последнее взаимодействие
        last_interaction = interaction_history[-1]
        interaction_type = last_interaction.get('type', 'communication')
        date = last_interaction.get('date', '')
        
        if interaction_type == 'email':
            return f"email exchange on {date}"
        elif interaction_type == 'meeting':
            return f"meeting on {date}"
        elif interaction_type == 'call':
            return f"phone call on {date}"
        else:
            return f"previous interaction on {date}"
    
    def _determine_specific_interest(self, vc_data: Dict[str, Any], 
                                   startup_data: Dict[str, Any],
                                   context: PersonalizationContext) -> Optional[str]:
        """Определение специфического интереса"""
        startup_industry = startup_data.get('industry', '')
        startup_stage = startup_data.get('stage', '')
        
        # Генерируем специфический интерес на основе данных
        interests = [
            f"your focus on {startup_industry} companies",
            f"your expertise in {startup_stage} stage investments",
            f"the synergies with your existing portfolio",
            f"your track record in {startup_industry} market",
            f"your investment thesis alignment"
        ]
        
        return random.choice(interests)
    
    def _get_requested_documents(self, interaction_history: List[Dict[str, Any]]) -> List[str]:
        """Получение запрошенных документов"""
        documents = []
        
        for interaction in interaction_history:
            if interaction.get('type') == 'document_request':
                requested_docs = interaction.get('documents', [])
                documents.extend(requested_docs)
        
        # Убираем дубликаты
        return list(set(documents))
    
    def _get_meeting_availability(self, timing_context: Dict[str, Any]) -> str:
        """Получение доступности для встреч"""
        timezone = timing_context.get('timezone', 'EST')
        
        # Генерируем доступные времена
        availability_options = [
            f"Monday-Friday, 9 AM - 5 PM {timezone}",
            f"Tuesday-Thursday, 10 AM - 4 PM {timezone}",
            f"Flexible scheduling, {timezone} business hours",
            f"Available most weekdays, {timezone}",
            f"Open availability next week, {timezone}"
        ]
        
        return random.choice(availability_options)
    
    def _get_meeting_date(self, timing_context: Dict[str, Any]) -> Optional[str]:
        """Получение даты встречи"""
        if timing_context.get('scheduled_meeting'):
            return timing_context['scheduled_meeting'].get('date')
        
        # Генерируем предложенную дату (через 3-7 дней)
        days_ahead = random.randint(3, 7)
        proposed_date = datetime.now() + timedelta(days=days_ahead)
        
        return proposed_date.strftime('%Y-%m-%d')
    
    def _get_meeting_time(self, timing_context: Dict[str, Any]) -> Optional[str]:
        """Получение времени встречи"""
        if timing_context.get('scheduled_meeting'):
            return timing_context['scheduled_meeting'].get('time')
        
        # Генерируем предложенное время
        time_options = [
            "10:00 AM",
            "2:00 PM", 
            "3:00 PM",
            "4:00 PM"
        ]
        
        return random.choice(time_options)
    
    def _get_meeting_type(self, vc_data: Dict[str, Any]) -> str:
        """Получение типа встречи"""
        preferences = vc_data.get('meeting_preferences', {})
        
        if preferences.get('prefers_video'):
            return 'video_call'
        elif preferences.get('prefers_in_person'):
            return 'in_person'
        else:
            return random.choice(['video_call', 'in_person', 'phone_call'])
    
    def _enhance_with_template_specific_data(self, personalization_data: PersonalizationData,
                                           template_type: str,
                                           context: PersonalizationContext):
        """Улучшение данных специфичными для шаблона данными"""
        
        if template_type == 'initial_outreach':
            self._enhance_initial_outreach_data(personalization_data, context)
        elif template_type == 'follow_up_interested':
            self._enhance_follow_up_data(personalization_data, context)
        elif template_type == 'follow_up_more_info':
            self._enhance_more_info_data(personalization_data, context)
        elif template_type == 'meeting_confirmation':
            self._enhance_meeting_confirmation_data(personalization_data, context)
        elif template_type == 'thank_you_meeting':
            self._enhance_thank_you_data(personalization_data, context)
    
    def _enhance_initial_outreach_data(self, data: PersonalizationData, context: PersonalizationContext):
        """Улучшение данных для первичного обращения"""
        # Добавляем специфичные для первичного обращения данные
        data.specific_interest = f"your focus on {data.startup_industry} and {data.startup_stage} stage companies"
    
    def _enhance_follow_up_data(self, data: PersonalizationData, context: PersonalizationContext):
        """Улучшение данных для follow-up"""
        # Добавляем информацию о прогрессе
        if not data.specific_interest:
            data.specific_interest = "our recent progress and milestones"
    
    def _enhance_more_info_data(self, data: PersonalizationData, context: PersonalizationContext):
        """Улучшение данных для запроса информации"""
        # Добавляем запрошенные документы
        if not data.requested_documents:
            data.requested_documents = [
                'pitch deck',
                'financial projections',
                'customer references'
            ]
    
    def _enhance_meeting_confirmation_data(self, data: PersonalizationData, context: PersonalizationContext):
        """Улучшение данных для подтверждения встречи"""
        # Устанавливаем детали встречи
        if not data.meeting_date:
            data.meeting_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        if not data.meeting_time:
            data.meeting_time = "2:00 PM"
        if not data.meeting_type:
            data.meeting_type = "video_call"
    
    def _enhance_thank_you_data(self, data: PersonalizationData, context: PersonalizationContext):
        """Улучшение данных для благодарности после встречи"""
        # Добавляем информацию о встрече
        if not data.previous_interaction:
            data.previous_interaction = "productive discussion"
    
    def _get_fallback_personalization_data(self, context: PersonalizationContext) -> PersonalizationData:
        """Получение базовых данных персонализации в случае ошибки"""
        vc_data = context.vc_fund_data
        startup_data = context.startup_data
        
        return PersonalizationData(
            vc_name=vc_data.get('name', 'Investment Partner'),
            fund_name=vc_data.get('name', 'Investment Fund'),
            partner_name=vc_data.get('name', 'Partner'),
            startup_name=startup_data.get('name', 'Our Company'),
            startup_industry=startup_data.get('industry', 'Technology'),
            startup_stage=startup_data.get('stage', 'Seed'),
            contact_person=startup_data.get('contact_person', 'The Team'),
            startup_email=startup_data.get('email', 'contact@company.com')
        )
    
    def get_personalization_score(self, personalization_data: PersonalizationData) -> float:
        """Вычисление оценки персонализации"""
        score = 0.0
        max_score = 10.0
        
        # Проверяем наличие ключевых персонализированных данных
        if personalization_data.partner_name and personalization_data.partner_name != 'Partner':
            score += 1.0
        
        if personalization_data.relevant_portfolio_company:
            score += 2.0
        
        if personalization_data.investment_focus:
            score += 1.5
        
        if personalization_data.ticket_size_range:
            score += 1.0
        
        if personalization_data.specific_interest:
            score += 1.5
        
        if personalization_data.previous_interaction:
            score += 1.0
        
        if personalization_data.meeting_availability:
            score += 1.0
        
        if personalization_data.pitch_summary:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def generate_dynamic_content(self, personalization_data: PersonalizationData, 
                               content_type: str) -> str:
        """Генерация динамического контента"""
        
        if content_type == 'greeting':
            return self._generate_greeting(personalization_data)
        elif content_type == 'interest_expression':
            return self._generate_interest_expression(personalization_data)
        elif content_type == 'portfolio_connection':
            return self._generate_portfolio_connection(personalization_data)
        elif content_type == 'call_to_action':
            return self._generate_call_to_action(personalization_data)
        else:
            return ""
    
    def _generate_greeting(self, data: PersonalizationData) -> str:
        """Генерация приветствия"""
        greetings = self.personalization_phrases['greeting_formal']
        return random.choice(greetings).format(partner_name=data.partner_name)
    
    def _generate_interest_expression(self, data: PersonalizationData) -> str:
        """Генерация выражения интереса"""
        return random.choice(self.personalization_phrases['interest_expressions'])
    
    def _generate_portfolio_connection(self, data: PersonalizationData) -> str:
        """Генерация связи с портфелем"""
        if data.relevant_portfolio_company:
            return f"I noticed that {data.fund_name} has invested in {data.relevant_portfolio_company}, which operates in a complementary space to {data.startup_name}."
        return ""
    
    def _generate_call_to_action(self, data: PersonalizationData) -> str:
        """Генерация призыва к действию"""
        return f"I'd welcome the opportunity to discuss how {data.startup_name} could be a valuable addition to your portfolio."


# Глобальный экземпляр персонализационного движка
personalization_engine = PersonalizationEngine()
