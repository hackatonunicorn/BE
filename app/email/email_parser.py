"""
EmailParser для парсинга и анализа содержимого email
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
from email.utils import parseaddr
import html2text

# Импорт для анализа ответов
try:
    from app.ai.response_classifier import response_classifier
except ImportError:
    response_classifier = None

logger = logging.getLogger(__name__)


class EmailParser:
    """Парсер для анализа и извлечения информации из email"""
    
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # No line wrapping
    
    def parse_email_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Полный парсинг email с извлечением всей необходимой информации
        
        Args:
            email_data: Данные email из IMAP handler
        
        Returns:
            Словарь с распарсенными данными
        """
        try:
            parsed_data = {
                'message_id': email_data.get('message_id', ''),
                'sender_email': email_data.get('sender_email', ''),
                'sender_name': email_data.get('sender_name', ''),
                'recipient_email': email_data.get('recipient_email', ''),
                'subject': email_data.get('subject', ''),
                'body': email_data.get('body', ''),
                'html_body': email_data.get('html_body', ''),
                'date': email_data.get('date'),
                'headers': email_data.get('headers', {}),
                'attachments': email_data.get('attachments', []),
                'direction': email_data.get('direction', 'inbound'),
                'thread_info': self._extract_thread_info(email_data),
                'reply_context': self._extract_reply_context(email_data),
                'contact_info': self._extract_contact_info(email_data),
                'auto_reply_detected': self._detect_auto_reply(email_data),
                'bounce_detected': self._detect_bounce(email_data),
                'classification': None,
                'extracted_entities': {},
                'clean_body': '',
                'quoted_text': '',
                'signature': ''
            }
            
            # Очищаем и анализируем содержимое
            content_analysis = self._analyze_email_content(email_data)
            parsed_data.update(content_analysis)
            
            # Классифицируем ответ (если это входящий email)
            if parsed_data['direction'] == 'inbound' and response_classifier:
                classification = self._classify_response(parsed_data)
                parsed_data['classification'] = classification
            
            # Извлекаем сущности
            entities = self._extract_entities(parsed_data['clean_body'])
            parsed_data['extracted_entities'] = entities
            
            logger.info(f"Successfully parsed email: {parsed_data['message_id']}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return email_data  # Возвращаем исходные данные при ошибке
    
    def _extract_thread_info(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает информацию о треде email"""
        headers = email_data.get('headers', {})
        
        return {
            'message_id': email_data.get('message_id', ''),
            'in_reply_to': headers.get('In-Reply-To', ''),
            'references': headers.get('References', ''),
            'thread_topic': headers.get('Thread-Topic', ''),
            'thread_index': headers.get('Thread-Index', ''),
            'is_reply': bool(headers.get('In-Reply-To') or headers.get('References')),
            'conversation_id': self._generate_conversation_id(email_data)
        }
    
    def _generate_conversation_id(self, email_data: Dict[str, Any]) -> str:
        """Генерирует ID разговора для группировки email"""
        headers = email_data.get('headers', {})
        
        # Используем In-Reply-To или References если есть
        if headers.get('In-Reply-To'):
            return headers['In-Reply-To'].strip('<>')
        
        if headers.get('References'):
            # Берем первый Message-ID из References
            refs = headers['References'].strip().split()
            if refs:
                return refs[0].strip('<>')
        
        # Если это новый тред, используем текущий Message-ID
        message_id = email_data.get('message_id', '').strip('<>')
        return message_id or str(uuid.uuid4())
    
    def _extract_reply_context(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает контекст ответа из email"""
        body = email_data.get('body', '')
        html_body = email_data.get('html_body', '')
        
        # Если есть HTML, конвертируем в текст
        if html_body and not body:
            body = self.html_converter.handle(html_body)
        
        # Ищем паттерны ответа
        reply_patterns = [
            r'On .+ wrote:',
            r'From: .+\nSent: .+\nTo: .+\nSubject: .+',
            r'-----Original Message-----',
            r'> .*',  # Quoted text
            r'От: .+\nОтправлено: .+\nКому: .+\nТема: .+',  # Russian
        ]
        
        original_message = ''
        for pattern in reply_patterns:
            match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
            if match:
                original_message = body[match.start():]
                break
        
        return {
            'has_quoted_text': bool(original_message),
            'quoted_text': original_message,
            'original_sender': self._extract_original_sender(original_message),
            'original_date': self._extract_original_date(original_message),
            'original_subject': self._extract_original_subject(original_message)
        }
    
    def _extract_original_sender(self, quoted_text: str) -> str:
        """Извлекает отправителя оригинального сообщения"""
        patterns = [
            r'From: (.+?)[\n\r]',
            r'От: (.+?)[\n\r]',
            r'On .+ (.+?) wrote:',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, quoted_text)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_original_date(self, quoted_text: str) -> str:
        """Извлекает дату оригинального сообщения"""
        patterns = [
            r'Sent: (.+?)[\n\r]',
            r'Отправлено: (.+?)[\n\r]',
            r'On (.+?) .+ wrote:',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, quoted_text)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_original_subject(self, quoted_text: str) -> str:
        """Извлекает тему оригинального сообщения"""
        patterns = [
            r'Subject: (.+?)[\n\r]',
            r'Тема: (.+?)[\n\r]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, quoted_text)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_contact_info(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает контактную информацию из email"""
        body = email_data.get('body', '') + ' ' + email_data.get('html_body', '')
        headers = email_data.get('headers', {})
        
        # Извлекаем телефоны
        phone_patterns = [
            r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
            r'\+?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, body)
            for match in matches:
                if isinstance(match, tuple):
                    phone = '-'.join(match)
                else:
                    phone = match
                phones.append(phone)
        
        # Извлекаем календарные ссылки
        calendar_patterns = [
            r'calendly\.com/[\w\-/]+',
            r'calendar\.google\.com/[\w\-/?=&]+',
            r'outlook\.live\.com/[\w\-/?=&]+',
            r'cal\.com/[\w\-/]+'
        ]
        
        calendar_links = []
        for pattern in calendar_patterns:
            matches = re.findall(pattern, body)
            calendar_links.extend(matches)
        
        # Извлекаем социальные сети
        social_patterns = [
            r'linkedin\.com/in/[\w\-]+',
            r'twitter\.com/[\w\-]+',
            r'github\.com/[\w\-]+'
        ]
        
        social_links = []
        for pattern in social_patterns:
            matches = re.findall(pattern, body)
            social_links.extend(matches)
        
        return {
            'sender_email': email_data.get('sender_email', ''),
            'sender_name': email_data.get('sender_name', ''),
            'reply_to': headers.get('Reply-To', ''),
            'phones': list(set(phones)),
            'calendar_links': list(set(calendar_links)),
            'social_links': list(set(social_links)),
            'company_domain': self._extract_company_domain(email_data.get('sender_email', ''))
        }
    
    def _extract_company_domain(self, email: str) -> str:
        """Извлекает домен компании из email"""
        try:
            if '@' in email:
                domain = email.split('@')[1].lower()
                # Исключаем общие email провайдеры
                common_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
                if domain not in common_providers:
                    return domain
            return ''
        except:
            return ''
    
    def _detect_auto_reply(self, email_data: Dict[str, Any]) -> bool:
        """Определяет, является ли email автоответом"""
        headers = email_data.get('headers', {})
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        # Проверяем заголовки
        auto_reply_headers = [
            'Auto-Submitted',
            'X-Auto-Response-Suppress',
            'X-Autorespond',
            'X-Autoreply'
        ]
        
        for header in auto_reply_headers:
            if headers.get(header):
                return True
        
        # Проверяем тему
        auto_reply_subjects = [
            'out of office', 'out of the office', 'away', 'vacation',
            'automatic reply', 'auto reply', 'autoreply',
            'currently unavailable', 'not available'
        ]
        
        for pattern in auto_reply_subjects:
            if pattern in subject:
                return True
        
        # Проверяем содержимое
        auto_reply_content = [
            'automatic response', 'auto-generated', 'away from office',
            'currently out of office', 'will respond when', 'limited email access'
        ]
        
        for pattern in auto_reply_content:
            if pattern in body:
                return True
        
        return False
    
    def _detect_bounce(self, email_data: Dict[str, Any]) -> bool:
        """Определяет, является ли email уведомлением о недоставке"""
        headers = email_data.get('headers', {})
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        sender = email_data.get('sender_email', '').lower()
        
        # Проверяем отправителя
        bounce_senders = [
            'mailer-daemon', 'postmaster', 'noreply', 'no-reply',
            'delivery-failure', 'bounce'
        ]
        
        for bounce_sender in bounce_senders:
            if bounce_sender in sender:
                return True
        
        # Проверяем тему
        bounce_subjects = [
            'delivery failure', 'undelivered mail', 'returned mail',
            'mail delivery failed', 'bounced', 'permanent failure'
        ]
        
        for pattern in bounce_subjects:
            if pattern in subject:
                return True
        
        # Проверяем содержимое
        bounce_content = [
            'delivery failed', 'message could not be delivered',
            'recipient address rejected', 'user unknown',
            'mailbox unavailable', 'smtp error'
        ]
        
        for pattern in bounce_content:
            if pattern in body:
                return True
        
        return False
    
    def _analyze_email_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует и очищает содержимое email"""
        body = email_data.get('body', '')
        html_body = email_data.get('html_body', '')
        
        # Конвертируем HTML в текст если нужно
        if html_body and not body:
            body = self.html_converter.handle(html_body)
        
        # Разделяем на чистый текст, цитируемый текст и подпись
        clean_body, quoted_text, signature = self._split_email_content(body)
        
        return {
            'clean_body': clean_body,
            'quoted_text': quoted_text,
            'signature': signature,
            'word_count': len(clean_body.split()),
            'has_html': bool(html_body),
            'content_language': self._detect_language(clean_body)
        }
    
    def _split_email_content(self, body: str) -> Tuple[str, str, str]:
        """Разделяет email на чистый текст, цитируемый текст и подпись"""
        lines = body.split('\n')
        clean_lines = []
        quoted_lines = []
        signature_lines = []
        
        in_quoted = False
        in_signature = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Определяем начало цитируемого текста
            if (line_stripped.startswith('>') or 
                'wrote:' in line_stripped or
                '-----Original Message-----' in line_stripped or
                'From:' in line_stripped and 'Sent:' in '\n'.join(lines[i:i+3])):
                in_quoted = True
            
            # Определяем начало подписи
            if (line_stripped == '--' or 
                (len(line_stripped) == 0 and i > len(lines) * 0.7) or
                ('Best regards' in line_stripped or 'Sincerely' in line_stripped) and i > len(lines) * 0.5):
                in_signature = True
                in_quoted = False
            
            # Распределяем строки
            if in_signature:
                signature_lines.append(line)
            elif in_quoted:
                quoted_lines.append(line)
            else:
                clean_lines.append(line)
        
        return (
            '\n'.join(clean_lines).strip(),
            '\n'.join(quoted_lines).strip(),
            '\n'.join(signature_lines).strip()
        )
    
    def _detect_language(self, text: str) -> str:
        """Определяет язык текста (упрощенная версия)"""
        # Простое определение языка по ключевым словам
        russian_words = ['что', 'как', 'где', 'когда', 'почему', 'который', 'также', 'может']
        english_words = ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'they']
        
        text_lower = text.lower()
        
        russian_count = sum(1 for word in russian_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if russian_count > english_count:
            return 'ru'
        elif english_count > 0:
            return 'en'
        else:
            return 'unknown'
    
    def _classify_response(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Классифицирует ответ ВК используя ResponseClassifier"""
        try:
            if not response_classifier:
                return None
            
            # Подготавливаем контекст
            context = {
                'sender_email': parsed_data.get('sender_email', ''),
                'sender_name': parsed_data.get('sender_name', ''),
                'subject': parsed_data.get('subject', ''),
                'is_auto_reply': parsed_data.get('auto_reply_detected', False)
            }
            
            # Если это автоответ, сразу классифицируем
            if context['is_auto_reply']:
                return {
                    'classification': 'out_of_office',
                    'confidence': 0.95,
                    'reasoning': 'Auto-reply detected'
                }
            
            # Классифицируем обычный ответ
            clean_body = parsed_data.get('clean_body', '')
            if len(clean_body) > 10:  # Минимальная длина для анализа
                classification = response_classifier.classify_response_sync(clean_body, context)
                return classification
            
            return None
            
        except Exception as e:
            logger.error(f"Error classifying response: {e}")
            return None
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Извлекает именованные сущности из текста"""
        entities = {
            'dates': [],
            'money': [],
            'companies': [],
            'people': [],
            'locations': [],
            'urls': [],
            'emails': []
        }
        
        try:
            # Даты
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b(next|this)\s+(week|month|monday|tuesday|wednesday|thursday|friday)\b'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['dates'].extend(matches)
            
            # Деньги
            money_patterns = [
                r'\$[\d,]+(?:\.\d{2})?(?:[KMB])?',
                r'[\d,]+(?:\.\d{2})?\s*(?:USD|dollars?|million|billion)'
            ]
            
            for pattern in money_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['money'].extend(matches)
            
            # URLs
            url_pattern = r'https?://[^\s]+'
            entities['urls'] = re.findall(url_pattern, text)
            
            # Email адреса
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            entities['emails'] = re.findall(email_pattern, text)
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
        
        return entities
    
    def extract_thread_id_from_reply(self, email_data: Dict[str, Any], original_thread_id: str) -> str:
        """Извлекает thread_id из ответа, связывая с оригинальным письмом"""
        thread_info = self._extract_thread_info(email_data)
        
        # Если есть In-Reply-To, используем его
        if thread_info['in_reply_to']:
            return thread_info['in_reply_to'].strip('<>')
        
        # Если есть References, используем первый или последний
        if thread_info['references']:
            refs = thread_info['references'].strip().split()
            if refs:
                # Проверяем, есть ли оригинальный thread_id в references
                for ref in refs:
                    if original_thread_id in ref:
                        return original_thread_id
                # Если нет, возвращаем первый
                return refs[0].strip('<>')
        
        # Если ничего нет, используем conversation_id
        return thread_info['conversation_id']
    
    def is_bounce_email(self, email_data: Dict[str, Any]) -> bool:
        """Проверяет, является ли email уведомлением о недоставке"""
        return self._detect_bounce(email_data)
    
    def is_auto_reply(self, email_data: Dict[str, Any]) -> bool:
        """Проверяет, является ли email автоответом"""
        return self._detect_auto_reply(email_data)


# Создаем глобальный экземпляр
email_parser = EmailParser()
