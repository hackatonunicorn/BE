"""
ResponseClassifier для анализа ответов венчурных фондов
"""
import os
import re
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

# Импорты для AI
try:
    import anthropic
except ImportError:
    anthropic = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class ResponsePatternAnalyzer:
    """Анализатор паттернов в ответах для rule-based классификации"""
    
    def __init__(self):
        # Паттерны для каждого типа ответа
        self.patterns = {
            'interested': [
                # Положительные индикаторы
                r'interested?\s+in\s+learning\s+more',
                r'would\s+like\s+to\s+discuss',
                r'schedule\s+a\s+(call|meeting)',
                r'sounds\s+(interesting|promising)',
                r'fits?\s+our\s+(thesis|investment\s+criteria)',
                r'excited\s+to\s+learn\s+more',
                r'please\s+send\s+(more\s+info|deck|materials)',
                r'move\s+forward',
                r'next\s+steps',
                r'potential\s+(fit|investment)',
                r'aligned\s+with\s+our\s+portfolio',
                r'compelling\s+(opportunity|business)',
                r'impressive\s+(traction|growth)',
                r'strong\s+(team|execution)',
                r'when\s+can\s+we\s+(meet|call)',
                r'available\s+for\s+a\s+(call|meeting)'
            ],
            'not_interested': [
                # Отрицательные индикаторы
                r'not\s+a\s+(fit|good\s+fit)',
                r'outside\s+our\s+(focus|thesis|mandate)',
                r'pass\s+on\s+this\s+(opportunity|deal)',
                r'pursuing\s+other\s+opportunities',
                r'doesn\'?t\s+align\s+with',
                r'not\s+investing\s+in',
                r'stage\s+is\s+(too\s+early|too\s+late)',
                r'geography\s+(doesn\'?t\s+work|outside)',
                r'portfolio\s+conflict',
                r'already\s+invested\s+in\s+similar',
                r'thank\s+you\s+for\s+thinking\s+of\s+us,?\s+but',
                r'wish\s+you\s+the\s+best',
                r'good\s+luck\s+with\s+your\s+fundraising',
                r'not\s+the\s+right\s+time',
                r'pausing\s+new\s+investments',
                r'fully\s+deployed',
                r'appreciate\s+you\s+reaching\s+out,?\s+but'
            ],
            'request_more_info': [
                # Запросы дополнительной информации
                r'send\s+(us\s+)?(your\s+)?(pitch\s+deck|deck|materials)',
                r'more\s+(information|details|data)',
                r'financial\s+(statements|metrics|projections)',
                r'business\s+plan',
                r'due\s+diligence\s+materials',
                r'customer\s+(references|testimonials)',
                r'competitive\s+analysis',
                r'market\s+research',
                r'team\s+(bios|background)',
                r'product\s+demo',
                r'unit\s+economics',
                r'revenue\s+model',
                r'cap\s+table',
                r'term\s+sheet',
                r'can\s+you\s+(provide|share|send)',
                r'would\s+like\s+to\s+(see|review)',
                r'need\s+(more\s+)?info(rmation)?',
                r'tell\s+us\s+more\s+about'
            ],
            'meeting_request': [
                # Явные запросы встреч
                r'schedule\s+a\s+(call|meeting|demo)',
                r'set\s+up\s+a\s+(call|meeting)',
                r'available\s+for\s+a\s+(call|meeting)',
                r'when\s+are\s+you\s+free',
                r'coffee\s+(chat|meeting)',
                r'office\s+hours',
                r'partner\s+meeting',
                r'present\s+to\s+our\s+team',
                r'come\s+in\s+for\s+a\s+meeting',
                r'video\s+(call|conference)',
                r'zoom\s+(call|meeting)',
                r'calendly',
                r'my\s+calendar',
                r'book\s+some\s+time',
                r'let\'?s\s+(chat|talk|meet)',
                r'pitch\s+(presentation|session)'
            ],
            'out_of_office': [
                # Автоответы
                r'out\s+of\s+(the\s+)?office',
                r'away\s+from\s+(the\s+)?office',
                r'on\s+(vacation|holiday|leave)',
                r'auto(matic)?\s+(reply|response)',
                r'currently\s+(traveling|unavailable)',
                r'limited\s+email\s+access',
                r'will\s+respond\s+when\s+I\s+return',
                r'back\s+in\s+the\s+office',
                r'returning\s+on',
                r'will\s+be\s+back',
                r'automatic\s+message'
            ],
            'unclear': [
                # Неопределенные ответы
                r'will\s+(review|consider|discuss)',
                r'under\s+review',
                r'looking\s+into\s+it',
                r'get\s+back\s+to\s+you',
                r'internal\s+discussion',
                r'team\s+review',
                r'need\s+to\s+(think|discuss)',
                r'evaluate\s+internally',
                r'circulating\s+internally',
                r'on\s+our\s+radar',
                r'interesting',
                r'noted'
            ]
        }
    
    def analyze_patterns(self, text: str) -> Dict[str, Any]:
        """Анализирует текст на основе паттернов"""
        text_lower = text.lower()
        scores = {}
        matches = {}
        
        for category, patterns in self.patterns.items():
            category_score = 0
            category_matches = []
            
            for pattern in patterns:
                matches_found = re.findall(pattern, text_lower)
                if matches_found:
                    category_score += len(matches_found)
                    category_matches.extend(matches_found)
            
            if category_score > 0:
                scores[category] = category_score
                matches[category] = category_matches
        
        return {
            'scores': scores,
            'matches': matches,
            'total_patterns_found': sum(scores.values())
        }


class ResponseExtractor:
    """Извлечение ключевой информации из ответов"""
    
    @staticmethod
    def extract_meeting_info(text: str) -> Dict[str, Any]:
        """Извлекает информацию о встречах"""
        meeting_info = {}
        
        # Поиск времени и дат
        date_patterns = [
            r'next\s+(week|month|tuesday|wednesday|thursday|friday|monday)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            r'this\s+(week|month)'
        ]
        
        time_patterns = [
            r'\d{1,2}:\d{2}\s*(am|pm)',
            r'\d{1,2}\s*(am|pm)',
            r'morning|afternoon|evening',
            r'early|late|mid'
        ]
        
        # Типы встреч
        meeting_types = [
            r'video\s+(call|conference)',
            r'phone\s+call',
            r'in[\-\s]?person',
            r'office\s+visit',
            r'coffee',
            r'lunch',
            r'pitch\s+(presentation|session)',
            r'demo'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                meeting_info.setdefault('dates', []).extend(matches)
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                meeting_info.setdefault('times', []).extend(matches)
        
        for pattern in meeting_types:
            matches = re.findall(pattern, text.lower())
            if matches:
                meeting_info.setdefault('types', []).extend(matches)
        
        return meeting_info
    
    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Any]:
        """Извлекает контактную информацию"""
        contact_info = {}
        
        # Email адреса
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['emails'] = emails
        
        # Телефоны
        phone_patterns = [
            r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
            r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                phones = ['-'.join(match) for match in matches]
                contact_info.setdefault('phones', []).extend(phones)
        
        # Календарные ссылки
        calendar_patterns = [
            r'calendly\.com/[\w\-/]+',
            r'calendar\.google\.com/[\w\-/?=&]+',
            r'outlook\.live\.com/[\w\-/?=&]+',
            r'cal\.com/[\w\-/]+'
        ]
        
        for pattern in calendar_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info.setdefault('calendar_links', []).extend(matches)
        
        return contact_info
    
    @staticmethod
    def extract_requirements(text: str) -> List[str]:
        """Извлекает требования и запросы"""
        requirements = []
        
        requirement_patterns = [
            r'need\s+(to\s+)?(see|review|understand)\s+([^.]+)',
            r'require\s+([^.]+)',
            r'must\s+(have|provide|show)\s+([^.]+)',
            r'looking\s+for\s+([^.]+)',
            r'would\s+like\s+(to\s+)?(see|know|understand)\s+([^.]+)',
            r'can\s+you\s+(provide|send|share)\s+([^.?]+)',
            r'please\s+(send|provide|share)\s+([^.?]+)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        req = ' '.join([m for m in match if m]).strip()
                    else:
                        req = match.strip()
                    if req and len(req) > 3:
                        requirements.append(req)
        
        return list(set(requirements))  # Убираем дубликаты
    
    @staticmethod
    def extract_concerns(text: str) -> List[str]:
        """Извлекает озабоченности и возражения"""
        concerns = []
        
        concern_patterns = [
            r'concerned\s+about\s+([^.]+)',
            r'worry\s+about\s+([^.]+)',
            r'issue\s+with\s+([^.]+)',
            r'problem\s+with\s+([^.]+)',
            r'challenge\s+(is|would\s+be)\s+([^.]+)',
            r'risk\s+(is|of)\s+([^.]+)',
            r'hesitant\s+about\s+([^.]+)',
            r'unclear\s+(on|about)\s+([^.]+)'
        ]
        
        for pattern in concern_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        concern = ' '.join([m for m in match if m]).strip()
                    else:
                        concern = match.strip()
                    if concern and len(concern) > 3:
                        concerns.append(concern)
        
        return list(set(concerns))


class ResponseClassifier:
    """Классификатор ответов венчурных фондов"""
    
    def __init__(self, claude_api_key: Optional[str] = None):
        self.claude_api_key = claude_api_key or os.getenv('CLAUDE_API_KEY') or getattr(settings, 'CLAUDE_API_KEY', None)
        
        self.client = None
        if self.claude_api_key and anthropic:
            try:
                self.client = anthropic.Anthropic(api_key=self.claude_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
        
        self.pattern_analyzer = ResponsePatternAnalyzer()
        self.extractor = ResponseExtractor()
        
        # Пороги уверенности для каждой категории
        self.confidence_thresholds = {
            'interested': 0.8,
            'not_interested': 0.85,
            'request_more_info': 0.75,
            'meeting_request': 0.9,
            'out_of_office': 0.95,
            'unclear': 0.6
        }
    
    def _create_classification_prompt(self, email_text: str, context: Dict[str, Any] = None) -> str:
        """Создает промпт для классификации ответа"""
        
        context_info = ""
        if context:
            startup_name = context.get('startup_name', 'the startup')
            vc_name = context.get('vc_name', 'the VC fund')
            context_info = f"\nContext: This is a response from {vc_name} to an outreach email from {startup_name}."
        
        return f"""
Analyze the following email response from a venture capital fund and classify it into one of these categories:

1. **interested** - Shows genuine interest in the opportunity, wants to learn more or move forward
2. **not_interested** - Clearly declines the opportunity, passes on the deal
3. **request_more_info** - Asks for additional information, materials, or clarification
4. **meeting_request** - Specifically requests or suggests a meeting, call, or presentation
5. **out_of_office** - Automatic out-of-office reply
6. **unclear** - Vague response that doesn't clearly indicate intent

{context_info}

EMAIL CONTENT:
{email_text}

Provide your analysis in the following JSON format:
{{
    "classification": "one of the 6 categories above",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this classification was chosen",
    "key_indicators": ["list", "of", "key", "phrases", "that", "support", "classification"],
    "extracted_info": {{
        "meeting_details": {{"dates": [], "times": [], "types": []}},
        "contact_info": {{"emails": [], "phones": [], "calendar_links": []}},
        "requirements": ["list of specific requests or requirements"],
        "concerns": ["list of concerns or objections mentioned"],
        "sentiment": "positive/negative/neutral",
        "urgency": "high/medium/low"
    }},
    "suggested_action": "recommended next step based on classification",
    "requires_human_review": false
}}

Focus on:
- Overall tone and sentiment
- Specific language indicating interest level
- Requests for information or meetings
- Timeline indicators
- Clear accept/reject signals

Be precise with confidence scores - use 0.9+ only for very clear cases.
"""
    
    async def classify_response_with_claude(self, email_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Классифицирует ответ с помощью Claude API"""
        if not self.client:
            logger.warning("Claude client not available, using rule-based classification")
            return self._rule_based_classification(email_text, context)
        
        try:
            prompt = self._create_classification_prompt(email_text, context)
            
            response = await asyncio.create_task(
                asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-3-sonnet-20240229",
                    max_tokens=1500,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            
            content = response.content[0].text if response.content else ""
            
            # Парсим JSON ответ
            try:
                # Ищем JSON в ответе
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    result = json.loads(json_content)
                    
                    # Валидируем результат
                    result = self._validate_classification_result(result)
                    result['analysis_method'] = 'claude_ai'
                    result['analyzed_at'] = datetime.now().isoformat()
                    
                    logger.info(f"Successfully classified response with Claude: {result['classification']}")
                    return result
                else:
                    raise ValueError("No valid JSON found in Claude response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.debug(f"Claude response content: {content}")
                return self._rule_based_classification(email_text, context)
                
        except Exception as e:
            logger.error(f"Error classifying response with Claude: {e}")
            return self._rule_based_classification(email_text, context)
    
    def _rule_based_classification(self, email_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Классификация на основе правил (fallback)"""
        logger.info("Performing rule-based response classification")
        
        # Анализируем паттерны
        pattern_analysis = self.pattern_analyzer.analyze_patterns(email_text)
        scores = pattern_analysis['scores']
        
        # Определяем классификацию
        if not scores:
            classification = 'unclear'
            confidence = 0.3
        else:
            # Находим категорию с наибольшим счетом
            classification = max(scores.keys(), key=lambda x: scores[x])
            
            # Рассчитываем уверенность
            max_score = scores[classification]
            total_score = sum(scores.values())
            
            # Базовая уверенность на основе доминирования категории
            if total_score > 0:
                dominance = max_score / total_score
                confidence = min(0.95, dominance * 0.8 + 0.3)
            else:
                confidence = 0.3
            
            # Корректируем уверенность для специфичных категорий
            if classification == 'out_of_office' and max_score >= 1:
                confidence = 0.95
            elif classification == 'meeting_request' and max_score >= 2:
                confidence = 0.9
            elif classification == 'not_interested' and max_score >= 2:
                confidence = 0.85
        
        # Извлекаем дополнительную информацию
        meeting_info = self.extractor.extract_meeting_info(email_text)
        contact_info = self.extractor.extract_contact_info(email_text)
        requirements = self.extractor.extract_requirements(email_text)
        concerns = self.extractor.extract_concerns(email_text)
        
        # Определяем sentiment
        sentiment = self._analyze_sentiment(email_text, pattern_analysis)
        
        # Определяем urgency
        urgency = self._analyze_urgency(email_text)
        
        # Предлагаем действие
        suggested_action = self._suggest_action(classification, confidence)
        
        # Определяем нужен ли человеческий обзор
        requires_human_review = self._needs_human_review(classification, confidence, email_text)
        
        result = {
            'classification': classification,
            'confidence': confidence,
            'reasoning': f"Rule-based classification based on {pattern_analysis['total_patterns_found']} pattern matches",
            'key_indicators': pattern_analysis['matches'].get(classification, []),
            'extracted_info': {
                'meeting_details': meeting_info,
                'contact_info': contact_info,
                'requirements': requirements,
                'concerns': concerns,
                'sentiment': sentiment,
                'urgency': urgency
            },
            'suggested_action': suggested_action,
            'requires_human_review': requires_human_review,
            'analysis_method': 'rule_based',
            'analyzed_at': datetime.now().isoformat(),
            'pattern_scores': scores
        }
        
        return result
    
    def _analyze_sentiment(self, text: str, pattern_analysis: Dict[str, Any]) -> str:
        """Анализирует тональность сообщения"""
        scores = pattern_analysis['scores']
        
        positive_indicators = scores.get('interested', 0) + scores.get('meeting_request', 0)
        negative_indicators = scores.get('not_interested', 0)
        neutral_indicators = scores.get('request_more_info', 0) + scores.get('unclear', 0)
        
        if positive_indicators > negative_indicators and positive_indicators > neutral_indicators:
            return 'positive'
        elif negative_indicators > positive_indicators:
            return 'negative'
        else:
            return 'neutral'
    
    def _analyze_urgency(self, text: str) -> str:
        """Анализирует срочность ответа"""
        urgency_patterns = {
            'high': [
                r'urgent', r'asap', r'immediately', r'right away', r'this week',
                r'tomorrow', r'today', r'quickly', r'time[\-\s]sensitive'
            ],
            'medium': [
                r'soon', r'next week', r'this month', r'within.*days',
                r'at your earliest convenience', r'when possible'
            ]
        }
        
        text_lower = text.lower()
        
        for urgency_level, patterns in urgency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return urgency_level
        
        return 'low'
    
    def _suggest_action(self, classification: str, confidence: float) -> str:
        """Предлагает следующее действие"""
        action_map = {
            'interested': 'Send pitch deck and propose meeting times',
            'not_interested': 'Update CRM status and focus on other prospects',
            'request_more_info': 'Prepare and send requested materials',
            'meeting_request': 'Confirm meeting details and send calendar invite',
            'out_of_office': 'Schedule follow-up after return date',
            'unclear': 'Send clarifying follow-up email'
        }
        
        action = action_map.get(classification, 'Review manually and determine next steps')
        
        if confidence < 0.7:
            action = f"Low confidence classification - {action.lower()} after human review"
        
        return action
    
    def _needs_human_review(self, classification: str, confidence: float, text: str) -> bool:
        """Определяет нужен ли человеческий обзор"""
        # Низкая уверенность
        if confidence < 0.7:
            return True
        
        # Сложные случаи
        if classification == 'unclear':
            return True
        
        # Короткие сообщения (могут быть неточными)
        if len(text.split()) < 10:
            return True
        
        # Содержит важные детали, которые нужно проанализировать
        important_keywords = [
            'terms', 'valuation', 'timeline', 'partner', 'board',
            'due diligence', 'term sheet', 'investment committee'
        ]
        
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in important_keywords):
            return True
        
        return False
    
    def _validate_classification_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует и очищает результат классификации"""
        valid_classifications = ['interested', 'not_interested', 'request_more_info', 
                               'meeting_request', 'out_of_office', 'unclear']
        
        # Проверяем классификацию
        if result.get('classification') not in valid_classifications:
            result['classification'] = 'unclear'
        
        # Проверяем уверенность
        confidence = result.get('confidence', 0.5)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            result['confidence'] = 0.5
        else:
            result['confidence'] = float(confidence)
        
        # Убеждаемся в структуре extracted_info
        if 'extracted_info' not in result:
            result['extracted_info'] = {}
        
        extracted_info = result['extracted_info']
        if 'meeting_details' not in extracted_info:
            extracted_info['meeting_details'] = {'dates': [], 'times': [], 'types': []}
        if 'contact_info' not in extracted_info:
            extracted_info['contact_info'] = {'emails': [], 'phones': [], 'calendar_links': []}
        if 'requirements' not in extracted_info:
            extracted_info['requirements'] = []
        if 'concerns' not in extracted_info:
            extracted_info['concerns'] = []
        if 'sentiment' not in extracted_info:
            extracted_info['sentiment'] = 'neutral'
        if 'urgency' not in extracted_info:
            extracted_info['urgency'] = 'low'
        
        # Убеждаемся в других полях
        if 'suggested_action' not in result:
            result['suggested_action'] = self._suggest_action(result['classification'], result['confidence'])
        
        if 'requires_human_review' not in result:
            result['requires_human_review'] = result['confidence'] < 0.7
        
        return result
    
    async def classify_response(self, email_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Основной метод для классификации ответа"""
        try:
            if not email_text or not email_text.strip():
                raise ValueError("Email text is empty")
            
            # Очищаем текст
            cleaned_text = email_text.strip()
            
            # Классифицируем с помощью Claude или правил
            result = await self.classify_response_with_claude(cleaned_text, context)
            
            # Добавляем метаданные
            result['original_text_length'] = len(email_text)
            result['cleaned_text_length'] = len(cleaned_text)
            
            logger.info(f"Response classified as: {result['classification']} (confidence: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying response: {e}")
            # Возвращаем безопасный fallback
            return {
                'classification': 'unclear',
                'confidence': 0.1,
                'reasoning': f"Error during classification: {str(e)}",
                'key_indicators': [],
                'extracted_info': {
                    'meeting_details': {'dates': [], 'times': [], 'types': []},
                    'contact_info': {'emails': [], 'phones': [], 'calendar_links': []},
                    'requirements': [],
                    'concerns': [],
                    'sentiment': 'neutral',
                    'urgency': 'low'
                },
                'suggested_action': 'Manual review required due to classification error',
                'requires_human_review': True,
                'analysis_method': 'error_fallback',
                'analyzed_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def classify_response_sync(self, email_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Синхронная версия классификации для использования в API"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.classify_response(email_text, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error in sync response classification: {e}")
            return self._rule_based_classification(email_text, context)


# Создаем глобальный экземпляр для использования
response_classifier = ResponseClassifier()
