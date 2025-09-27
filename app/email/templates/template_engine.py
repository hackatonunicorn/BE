"""
Template Engine для email шаблонов с персонализацией и A/B тестированием
"""
import os
import logging
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, UndefinedError

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Типы шаблонов"""
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP_INTERESTED = "follow_up_interested"
    FOLLOW_UP_MORE_INFO = "follow_up_more_info"
    MEETING_CONFIRMATION = "meeting_confirmation"
    THANK_YOU_MEETING = "thank_you_meeting"
    REJECTION_FOLLOW_UP = "rejection_follow_up"
    DOCUMENT_REQUEST = "document_request"


class TemplateFormat(Enum):
    """Форматы шаблонов"""
    HTML = "html"
    TEXT = "txt"
    BOTH = "both"


class TemplateLanguage(Enum):
    """Языки шаблонов"""
    ENGLISH = "en"
    RUSSIAN = "ru"
    SPANISH = "es"


@dataclass
class TemplateVariant:
    """Вариант шаблона для A/B тестирования"""
    id: str
    name: str
    description: str
    weight: float  # Вес для распределения трафика (0.0 - 1.0)
    template_data: Dict[str, Any]
    created_at: datetime
    is_active: bool = True
    performance_metrics: Optional[Dict[str, Any]] = None


@dataclass
class PersonalizationData:
    """Данные для персонализации шаблонов"""
    # VC Fund данные
    vc_name: str
    fund_name: str
    partner_name: Optional[str] = None
    investment_focus: List[str] = None
    recent_investments: List[str] = None
    relevant_portfolio_company: Optional[str] = None
    ticket_size_range: Optional[str] = None
    
    # Startup данные
    startup_name: str
    startup_industry: str
    startup_stage: str
    contact_person: str
    startup_email: str
    pitch_summary: Optional[str] = None
    
    # Встреча данные
    meeting_availability: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_type: Optional[str] = None
    
    # Контекстные данные
    previous_interaction: Optional[str] = None
    specific_interest: Optional[str] = None
    requested_documents: List[str] = None
    
    def __post_init__(self):
        if self.investment_focus is None:
            self.investment_focus = []
        if self.recent_investments is None:
            self.recent_investments = []
        if self.requested_documents is None:
            self.requested_documents = []


@dataclass
class TemplateResult:
    """Результат рендеринга шаблона"""
    template_type: TemplateType
    variant_id: str
    format: TemplateFormat
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    personalization_score: float = 0.0
    ab_test_id: Optional[str] = None
    rendered_at: datetime = None
    
    def __post_init__(self):
        if self.rendered_at is None:
            self.rendered_at = datetime.now()


class TemplateEngine:
    """
    Движок для рендеринга email шаблонов с персонализацией и A/B тестированием
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        # Путь к шаблонам
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Инициализация Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Добавляем пользовательские фильтры
        self.jinja_env.filters.update({
            'format_currency': self._format_currency,
            'format_date': self._format_date,
            'format_list': self._format_list,
            'capitalize_first': self._capitalize_first,
            'truncate_words': self._truncate_words
        })
        
        # Кэш шаблонов
        self.template_cache = {}
        
        # A/B тестирование
        self.ab_tests = {}
        self.ab_test_results = {}
        
        # Статистика использования шаблонов
        self.template_stats = {}
        
        logger.info(f"TemplateEngine initialized with templates directory: {self.templates_dir}")
    
    def render_template(self, template_type: TemplateType, 
                       personalization_data: PersonalizationData,
                       format_type: TemplateFormat = TemplateFormat.BOTH,
                       variant_id: Optional[str] = None,
                       ab_test_id: Optional[str] = None) -> TemplateResult:
        """
        Рендеринг шаблона с персонализацией
        """
        try:
            # Выбираем вариант шаблона
            selected_variant = self._select_template_variant(
                template_type, variant_id, ab_test_id
            )
            
            # Подготавливаем данные для рендеринга
            render_data = self._prepare_render_data(personalization_data, selected_variant)
            
            # Рендерим шаблон
            result = self._render_template_variant(
                template_type, selected_variant, render_data, format_type
            )
            
            # Вычисляем оценку персонализации
            personalization_score = self._calculate_personalization_score(
                personalization_data, render_data
            )
            
            result.personalization_score = personalization_score
            result.ab_test_id = ab_test_id
            
            # Обновляем статистику
            self._update_template_stats(template_type, selected_variant.id, result)
            
            logger.info(f"Successfully rendered template {template_type.value} variant {selected_variant.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error rendering template {template_type.value}: {e}")
            raise
    
    def _select_template_variant(self, template_type: TemplateType, 
                               variant_id: Optional[str] = None,
                               ab_test_id: Optional[str] = None) -> TemplateVariant:
        """Выбор варианта шаблона для A/B тестирования"""
        
        # Если указан конкретный вариант
        if variant_id:
            variant = self._get_template_variant(template_type, variant_id)
            if variant:
                return variant
        
        # A/B тестирование
        if ab_test_id and ab_test_id in self.ab_tests:
            return self._select_ab_test_variant(template_type, ab_test_id)
        
        # Выбор по умолчанию (вариант с наибольшим весом)
        variants = self._get_template_variants(template_type)
        if not variants:
            raise ValueError(f"No variants found for template type {template_type.value}")
        
        # Выбираем активный вариант с наибольшим весом
        active_variants = [v for v in variants if v.is_active]
        if not active_variants:
            raise ValueError(f"No active variants found for template type {template_type.value}")
        
        return max(active_variants, key=lambda x: x.weight)
    
    def _select_ab_test_variant(self, template_type: TemplateType, ab_test_id: str) -> TemplateVariant:
        """Выбор варианта для A/B тестирования"""
        ab_test = self.ab_tests[ab_test_id]
        
        if template_type not in ab_test.get('template_types', []):
            # Fallback к обычному выбору
            return self._select_template_variant(template_type)
        
        # Распределение трафика на основе весов
        variants = ab_test.get('variants', [])
        if not variants:
            raise ValueError(f"No variants in A/B test {ab_test_id}")
        
        # Простое рандомное распределение (можно заменить на более сложную логику)
        rand_value = random.random()
        cumulative_weight = 0.0
        
        for variant in variants:
            cumulative_weight += variant.weight
            if rand_value <= cumulative_weight:
                return variant
        
        # Fallback к последнему варианту
        return variants[-1]
    
    def _prepare_render_data(self, personalization_data: PersonalizationData, 
                           variant: TemplateVariant) -> Dict[str, Any]:
        """Подготовка данных для рендеринга"""
        
        # Базовые данные
        render_data = {
            'vc_name': personalization_data.vc_name,
            'fund_name': personalization_data.fund_name,
            'partner_name': personalization_data.partner_name or personalization_data.vc_name,
            'startup_name': personalization_data.startup_name,
            'startup_industry': personalization_data.startup_industry,
            'startup_stage': personalization_data.startup_stage,
            'contact_person': personalization_data.contact_person,
            'startup_email': personalization_data.startup_email,
            
            # Инвестиционные данные
            'investment_focus': personalization_data.investment_focus,
            'recent_investments': personalization_data.recent_investments,
            'relevant_portfolio_company': personalization_data.relevant_portfolio_company,
            'ticket_size_range': personalization_data.ticket_size_range,
            
            # Встреча
            'meeting_availability': personalization_data.meeting_availability,
            'meeting_date': personalization_data.meeting_date,
            'meeting_time': personalization_data.meeting_time,
            'meeting_type': personalization_data.meeting_type,
            
            # Контекст
            'pitch_summary': personalization_data.pitch_summary,
            'previous_interaction': personalization_data.previous_interaction,
            'specific_interest': personalization_data.specific_interest,
            'requested_documents': personalization_data.requested_documents,
            
            # Системные данные
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'current_year': datetime.now().year,
            'variant_name': variant.name,
            'variant_description': variant.description
        }
        
        # Добавляем данные из варианта шаблона
        if variant.template_data:
            render_data.update(variant.template_data)
        
        return render_data
    
    def _render_template_variant(self, template_type: TemplateType, 
                               variant: TemplateVariant, 
                               render_data: Dict[str, Any],
                               format_type: TemplateFormat) -> TemplateResult:
        """Рендеринг конкретного варианта шаблона"""
        
        result = TemplateResult(
            template_type=template_type,
            variant_id=variant.id,
            format=format_type
        )
        
        # Рендерим subject
        subject_template = self._get_template(f"{template_type.value}/subject.j2")
        if subject_template:
            result.subject = subject_template.render(**render_data)
        else:
            result.subject = f"Partnership Opportunity - {render_data['startup_name']}"
        
        # Рендерим HTML контент
        if format_type in [TemplateFormat.HTML, TemplateFormat.BOTH]:
            html_template = self._get_template(f"{template_type.value}/body.html")
            if html_template:
                result.html_content = html_template.render(**render_data)
        
        # Рендерим текстовый контент
        if format_type in [TemplateFormat.TEXT, TemplateFormat.BOTH]:
            text_template = self._get_template(f"{template_type.value}/body.txt")
            if text_template:
                result.text_content = text_template.render(**render_data)
        
        return result
    
    def _get_template(self, template_path: str) -> Optional[Template]:
        """Получение шаблона из кэша или загрузка"""
        try:
            if template_path not in self.template_cache:
                self.template_cache[template_path] = self.jinja_env.get_template(template_path)
            
            return self.template_cache[template_path]
            
        except TemplateError as e:
            logger.warning(f"Template {template_path} not found: {e}")
            return None
    
    def _calculate_personalization_score(self, personalization_data: PersonalizationData, 
                                       render_data: Dict[str, Any]) -> float:
        """Вычисление оценки персонализации (0.0 - 1.0)"""
        score = 0.0
        max_score = 0.0
        
        # Проверяем наличие ключевых персонализированных данных
        personalization_checks = [
            ('partner_name', 0.2),
            ('relevant_portfolio_company', 0.2),
            ('investment_focus', 0.15),
            ('recent_investments', 0.15),
            ('specific_interest', 0.15),
            ('pitch_summary', 0.15)
        ]
        
        for field, weight in personalization_checks:
            max_score += weight
            if render_data.get(field):
                if isinstance(render_data[field], list):
                    if len(render_data[field]) > 0:
                        score += weight
                else:
                    score += weight
        
        return score / max_score if max_score > 0 else 0.0
    
    def _update_template_stats(self, template_type: TemplateType, variant_id: str, result: TemplateResult):
        """Обновление статистики использования шаблонов"""
        stats_key = f"{template_type.value}_{variant_id}"
        
        if stats_key not in self.template_stats:
            self.template_stats[stats_key] = {
                'total_renders': 0,
                'avg_personalization_score': 0.0,
                'last_rendered': None
            }
        
        stats = self.template_stats[stats_key]
        stats['total_renders'] += 1
        stats['last_rendered'] = datetime.now().isoformat()
        
        # Обновляем среднюю оценку персонализации
        total_score = stats['avg_personalization_score'] * (stats['total_renders'] - 1)
        stats['avg_personalization_score'] = (total_score + result.personalization_score) / stats['total_renders']
    
    def create_ab_test(self, test_id: str, name: str, description: str, 
                      template_types: List[TemplateType], variants: List[TemplateVariant]) -> bool:
        """Создание A/B теста"""
        try:
            self.ab_tests[test_id] = {
                'id': test_id,
                'name': name,
                'description': description,
                'template_types': template_types,
                'variants': variants,
                'created_at': datetime.now().isoformat(),
                'is_active': True
            }
            
            logger.info(f"Created A/B test {test_id} with {len(variants)} variants")
            return True
            
        except Exception as e:
            logger.error(f"Error creating A/B test {test_id}: {e}")
            return False
    
    def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Получение результатов A/B теста"""
        return self.ab_test_results.get(test_id)
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Получение статистики использования шаблонов"""
        return self.template_stats
    
    # Jinja2 фильтры
    def _format_currency(self, value: Any, currency: str = 'USD') -> str:
        """Форматирование валюты"""
        try:
            if isinstance(value, (int, float)):
                if currency == 'USD':
                    return f"${value:,.0f}"
                else:
                    return f"{value:,.0f} {currency}"
            return str(value)
        except:
            return str(value)
    
    def _format_date(self, date_str: str, format_str: str = '%B %d, %Y') -> str:
        """Форматирование даты"""
        try:
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime(format_str)
            return str(date_str)
        except:
            return str(date_str)
    
    def _format_list(self, items: List[str], separator: str = ', ', last_separator: str = ' and ') -> str:
        """Форматирование списка"""
        if not items:
            return ""
        
        if len(items) == 1:
            return items[0]
        
        if len(items) == 2:
            return f"{items[0]}{last_separator}{items[1]}"
        
        return f"{separator.join(items[:-1])}{last_separator}{items[-1]}"
    
    def _capitalize_first(self, text: str) -> str:
        """Капитализация первой буквы"""
        if not text:
            return text
        return text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    
    def _truncate_words(self, text: str, max_words: int = 50) -> str:
        """Обрезка текста по количеству слов"""
        if not text:
            return text
        
        words = text.split()
        if len(words) <= max_words:
            return text
        
        return ' '.join(words[:max_words]) + '...'
    
    def _get_template_variant(self, template_type: TemplateType, variant_id: str) -> Optional[TemplateVariant]:
        """Получение конкретного варианта шаблона"""
        # В реальной реализации это будет загрузка из базы данных
        # Пока возвращаем None для демонстрации
        return None
    
    def _get_template_variants(self, template_type: TemplateType) -> List[TemplateVariant]:
        """Получение всех вариантов шаблона"""
        # В реальной реализации это будет загрузка из базы данных
        # Пока возвращаем пустой список для демонстрации
        return []


# Глобальный экземпляр движка шаблонов
template_engine = TemplateEngine()
