"""
Модуль для предварительной обработки текста для анализа питч-деков
"""
import re
import string
from typing import List, Dict, Any, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """Класс для обработки и анализа текста"""
    
    def __init__(self):
        # Ключевые слова для различных категорий
        self.industry_keywords = {
            'technology': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'software', 'saas', 'platform', 'api', 'cloud', 'digital', 'tech'],
            'fintech': ['fintech', 'finance', 'banking', 'payment', 'blockchain', 'crypto', 'insurance', 'lending', 'trading', 'wallet'],
            'healthtech': ['health', 'medical', 'healthcare', 'telemedicine', 'biotech', 'pharma', 'clinical', 'patient', 'diagnosis', 'therapy'],
            'cleantech': ['clean', 'green', 'sustainable', 'energy', 'solar', 'wind', 'renewable', 'carbon', 'environment', 'climate'],
            'edtech': ['education', 'learning', 'edtech', 'school', 'university', 'course', 'training', 'skill', 'knowledge'],
            'ecommerce': ['ecommerce', 'marketplace', 'retail', 'shopping', 'store', 'commerce', 'selling', 'buying'],
            'media': ['media', 'content', 'entertainment', 'streaming', 'video', 'audio', 'social', 'creator', 'publishing']
        }
        
        self.stage_keywords = {
            'idea': ['idea', 'concept', 'planning', 'prototype', 'mvp', 'minimum viable product'],
            'seed': ['seed', 'pre-seed', 'angel', 'friends and family', 'early stage', 'startup'],
            'series_a': ['series a', 'series-a', 'growth', 'scaling', 'expansion', 'market validation'],
            'series_b': ['series b', 'series-b', 'scale-up', 'market leader', 'profitability'],
            'series_c': ['series c', 'series-c', 'mature', 'established', 'ipo preparation', 'acquisition']
        }
        
        self.metric_patterns = {
            'revenue': r'(?:revenue|sales|income|earnings)[:\s]*\$?([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?',
            'users': r'(?:users?|customers?|clients?)[:\s]*([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?',
            'growth': r'(?:growth|increase|growing)[:\s]*([0-9]+(?:\.[0-9]+)?)%',
            'margin': r'(?:margin|profit)[:\s]*([0-9]+(?:\.[0-9]+)?)%',
            'market_size': r'(?:market size|tam|total addressable market)[:\s]*\$?([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?'
        }
        
        self.funding_patterns = [
            r'raising\s+\$([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?',
            r'seeking\s+\$([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?',
            r'funding\s+\$([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?',
            r'\$([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?\s+round'
        ]

    def clean_text(self, text: str) -> str:
        """Очистка и нормализация текста"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы, оставляя буквы, цифры и базовую пунктуацию
        text = re.sub(r'[^\w\s\$%.,!?()-]', ' ', text)
        
        # Приводим к нижнему регистру для анализа
        text = text.lower().strip()
        
        return text

    def extract_sentences(self, text: str) -> List[str]:
        """Разделение текста на предложения"""
        # Простое разделение по точкам, восклицательным и вопросительным знакам
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def extract_numbers_with_units(self, text: str) -> List[Dict[str, Any]]:
        """Извлечение чисел с единицами измерения"""
        numbers = []
        
        # Паттерн для чисел с валютой и единицами
        pattern = r'\$?([0-9,]+(?:\.[0-9]+)?)\s*([kmb]?)(?:illion)?\s*([%]?)'
        
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            value_str = match.group(1).replace(',', '')
            try:
                value = float(value_str)
                unit = match.group(2) or ''
                percent = match.group(3) == '%'
                
                # Конвертируем единицы
                if unit == 'k':
                    value *= 1000
                elif unit == 'm':
                    value *= 1000000
                elif unit == 'b':
                    value *= 1000000000
                
                numbers.append({
                    'value': value,
                    'original': match.group(0),
                    'is_percentage': percent,
                    'position': match.start()
                })
            except ValueError:
                continue
        
        return numbers

    def detect_industry(self, text: str) -> Dict[str, Any]:
        """Определение индустрии на основе ключевых слов"""
        text_cleaned = self.clean_text(text)
        industry_scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            score = 0
            found_keywords = []
            
            for keyword in keywords:
                count = text_cleaned.count(keyword.lower())
                if count > 0:
                    score += count
                    found_keywords.append(keyword)
            
            if score > 0:
                industry_scores[industry] = {
                    'score': score,
                    'keywords': found_keywords
                }
        
        if industry_scores:
            best_industry = max(industry_scores.keys(), key=lambda x: industry_scores[x]['score'])
            return {
                'industry': best_industry,
                'confidence': industry_scores[best_industry]['score'],
                'keywords_found': industry_scores[best_industry]['keywords'],
                'all_scores': industry_scores
            }
        
        return {'industry': 'unknown', 'confidence': 0, 'keywords_found': [], 'all_scores': {}}

    def detect_stage(self, text: str) -> Dict[str, Any]:
        """Определение стадии развития компании"""
        text_cleaned = self.clean_text(text)
        stage_scores = {}
        
        for stage, keywords in self.stage_keywords.items():
            score = 0
            found_keywords = []
            
            for keyword in keywords:
                count = text_cleaned.count(keyword.lower())
                if count > 0:
                    score += count
                    found_keywords.append(keyword)
            
            if score > 0:
                stage_scores[stage] = {
                    'score': score,
                    'keywords': found_keywords
                }
        
        if stage_scores:
            best_stage = max(stage_scores.keys(), key=lambda x: stage_scores[x]['score'])
            return {
                'stage': best_stage,
                'confidence': stage_scores[best_stage]['score'],
                'keywords_found': stage_scores[best_stage]['keywords'],
                'all_scores': stage_scores
            }
        
        return {'stage': 'unknown', 'confidence': 0, 'keywords_found': [], 'all_scores': {}}

    def extract_funding_amount(self, text: str) -> Optional[Dict[str, Any]]:
        """Извлечение суммы привлекаемого финансирования"""
        text_cleaned = self.clean_text(text)
        
        for pattern in self.funding_patterns:
            match = re.search(pattern, text_cleaned)
            if match:
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    unit = match.group(2) if len(match.groups()) > 1 else ''
                    
                    # Конвертируем единицы
                    if unit == 'k':
                        value *= 1000
                    elif unit == 'm':
                        value *= 1000000
                    elif unit == 'b':
                        value *= 1000000000
                    
                    return {
                        'amount': int(value),
                        'original_text': match.group(0),
                        'confidence': 'high'
                    }
                except (ValueError, IndexError):
                    continue
        
        return None

    def extract_key_metrics(self, text: str) -> Dict[str, Any]:
        """Извлечение ключевых метрик"""
        text_cleaned = self.clean_text(text)
        metrics = {}
        
        for metric_name, pattern in self.metric_patterns.items():
            matches = re.finditer(pattern, text_cleaned)
            for match in matches:
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    unit = match.group(2) if len(match.groups()) > 1 else ''
                    
                    # Конвертируем единицы для числовых значений
                    if unit == 'k':
                        value *= 1000
                    elif unit == 'm':
                        value *= 1000000
                    elif unit == 'b':
                        value *= 1000000000
                    
                    metrics[metric_name] = {
                        'value': value,
                        'original_text': match.group(0),
                        'unit': unit
                    }
                    break  # Берем первое найденное значение
                except (ValueError, IndexError):
                    continue
        
        return metrics

    def extract_team_info(self, text: str) -> Dict[str, Any]:
        """Извлечение информации о команде"""
        text_cleaned = self.clean_text(text)
        team_info = {}
        
        # Паттерны для поиска информации о команде
        team_patterns = {
            'team_size': r'(?:team|staff|employees?)[:\s]*([0-9]+)',
            'founders': r'(?:founder|co-founder|ceo|cto|cfo)[:\s]*([a-zA-Z\s]+)',
            'experience': r'(?:years?|experience)[:\s]*([0-9]+)',
            'background': r'(?:background|experience|worked at)[:\s]*([a-zA-Z\s,]+)'
        }
        
        for info_type, pattern in team_patterns.items():
            matches = re.finditer(pattern, text_cleaned)
            found_items = []
            
            for match in matches:
                found_items.append(match.group(1).strip())
            
            if found_items:
                team_info[info_type] = found_items
        
        return team_info

    def extract_business_model_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов бизнес-модели"""
        business_model_keywords = [
            'subscription', 'saas', 'freemium', 'marketplace', 'commission',
            'advertising', 'licensing', 'franchise', 'b2b', 'b2c',
            'recurring revenue', 'one-time payment', 'transaction fee'
        ]
        
        text_cleaned = self.clean_text(text)
        found_keywords = []
        
        for keyword in business_model_keywords:
            if keyword in text_cleaned:
                found_keywords.append(keyword)
        
        return found_keywords

    def extract_competitive_advantages(self, text: str) -> List[str]:
        """Извлечение конкурентных преимуществ"""
        advantage_keywords = [
            'patent', 'proprietary', 'unique', 'exclusive', 'first to market',
            'network effect', 'scale', 'cost advantage', 'technology advantage',
            'brand', 'expertise', 'partnership', 'innovation'
        ]
        
        text_cleaned = self.clean_text(text)
        found_advantages = []
        
        for advantage in advantage_keywords:
            if advantage in text_cleaned:
                found_advantages.append(advantage)
        
        return found_advantages

    def analyze_text_structure(self, text: str) -> Dict[str, Any]:
        """Анализ структуры текста"""
        sentences = self.extract_sentences(text)
        words = text.split()
        
        return {
            'total_characters': len(text),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'has_financial_data': bool(re.search(r'\$[0-9,]+', text)),
            'has_percentages': bool(re.search(r'[0-9]+%', text)),
            'readability_score': self._calculate_readability_score(text)
        }

    def _calculate_readability_score(self, text: str) -> float:
        """Простой расчет читаемости текста"""
        words = text.split()
        sentences = self.extract_sentences(text)
        
        if not words or not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Простая формула: короткие предложения = выше читаемость
        if avg_sentence_length <= 15:
            return 8.0
        elif avg_sentence_length <= 20:
            return 6.0
        elif avg_sentence_length <= 25:
            return 4.0
        else:
            return 2.0

    def preprocess_for_ai_analysis(self, text: str) -> str:
        """Предварительная обработка текста для AI анализа"""
        # Очищаем текст
        cleaned = self.clean_text(text)
        
        # Разбиваем на предложения и берем наиболее информативные
        sentences = self.extract_sentences(cleaned)
        
        # Фильтруем слишком короткие предложения
        meaningful_sentences = [s for s in sentences if len(s.split()) >= 5]
        
        # Ограничиваем длину для эффективного анализа (примерно 2000 слов)
        result_text = ' '.join(meaningful_sentences)
        words = result_text.split()
        
        if len(words) > 2000:
            result_text = ' '.join(words[:2000])
        
        return result_text


# Создаем глобальный экземпляр для использования
text_processor = TextProcessor()
