"""
IMAPHandler для получения входящих email
"""
import os
import imaplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re
import uuid

from app.core.config_simple import settings

logger = logging.getLogger(__name__)


class IMAPConnectionError(Exception):
    """Исключение для ошибок IMAP подключения"""
    pass


class IMAPHandler:
    """Обработчик IMAP для получения входящих email"""
    
    def __init__(self):
        self.config = self._load_imap_config()
        self.connection = None
        self._validate_config()
    
    def _load_imap_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию IMAP"""
        return {
            'host': os.getenv('IMAP_HOST') or getattr(settings, 'IMAP_HOST', 'imap.gmail.com'),
            'port': int(os.getenv('IMAP_PORT', '993')),
            'username': os.getenv('IMAP_USERNAME') or getattr(settings, 'IMAP_USERNAME', None),
            'password': os.getenv('IMAP_PASSWORD') or getattr(settings, 'IMAP_PASSWORD', None),
            'use_ssl': os.getenv('IMAP_USE_SSL', 'true').lower() == 'true',
            'mailbox': os.getenv('IMAP_MAILBOX', 'INBOX'),
            'check_interval': int(os.getenv('IMAP_CHECK_INTERVAL', '300'))  # 5 minutes
        }
    
    def _validate_config(self):
        """Валидирует конфигурацию IMAP"""
        if not self.config.get('username') or not self.config.get('password'):
            logger.warning("IMAP credentials not configured")
        if not self.config.get('host'):
            logger.warning("IMAP host not configured")
    
    def connect(self) -> bool:
        """Устанавливает соединение с IMAP сервером"""
        try:
            if not self.config.get('username') or not self.config.get('password'):
                logger.error("IMAP credentials not configured")
                return False
            
            # Создаем соединение
            if self.config['use_ssl']:
                self.connection = imaplib.IMAP4_SSL(self.config['host'], self.config['port'])
            else:
                self.connection = imaplib.IMAP4(self.config['host'], self.config['port'])
            
            # Аутентификация
            self.connection.login(self.config['username'], self.config['password'])
            
            # Выбираем почтовый ящик
            self.connection.select(self.config['mailbox'])
            
            logger.info(f"Successfully connected to IMAP server: {self.config['host']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            self.connection = None
            return False
    
    def disconnect(self):
        """Закрывает соединение с IMAP сервером"""
        try:
            if self.connection:
                self.connection.close()
                self.connection.logout()
                self.connection = None
                logger.info("Disconnected from IMAP server")
        except Exception as e:
            logger.error(f"Error disconnecting from IMAP server: {e}")
    
    def fetch_new_emails(self, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получает новые email с сервера
        
        Args:
            since_date: Дата, с которой искать письма (по умолчанию - за последний час)
        
        Returns:
            Список словарей с данными email
        """
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # Определяем дату поиска
            if since_date is None:
                since_date = datetime.now() - timedelta(hours=1)
            
            # Формируем поисковый запрос
            date_str = since_date.strftime('%d-%b-%Y')
            search_criteria = f'(SINCE "{date_str}" UNSEEN)'
            
            # Ищем письма
            status, messages = self.connection.search(None, search_criteria)
            
            if status != 'OK':
                logger.error("Failed to search for emails")
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            for email_id in email_ids:
                try:
                    email_data = self._fetch_email_by_id(email_id)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            logger.info(f"Fetched {len(emails)} new emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _fetch_email_by_id(self, email_id: bytes) -> Optional[Dict[str, Any]]:
        """Получает email по ID"""
        try:
            # Получаем данные письма
            status, msg_data = self.connection.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                return None
            
            # Парсим email
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Извлекаем основные данные
            email_data = {
                'message_id': self._get_header(email_message, 'Message-ID'),
                'sender_email': self._extract_email_address(self._get_header(email_message, 'From')),
                'sender_name': self._extract_sender_name(self._get_header(email_message, 'From')),
                'recipient_email': self._extract_email_address(self._get_header(email_message, 'To')),
                'subject': self._get_header(email_message, 'Subject'),
                'date': self._parse_email_date(self._get_header(email_message, 'Date')),
                'in_reply_to': self._get_header(email_message, 'In-Reply-To'),
                'references': self._get_header(email_message, 'References'),
                'reply_to': self._get_header(email_message, 'Reply-To'),
                'body': '',
                'html_body': '',
                'attachments': [],
                'headers': dict(email_message.items()),
                'raw_email_id': email_id.decode(),
                'direction': 'inbound',
                'received_at': datetime.now().isoformat()
            }
            
            # Извлекаем содержимое
            body_data = self._extract_email_content(email_message)
            email_data.update(body_data)
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error fetching email by ID {email_id}: {e}")
            return None
    
    def _get_header(self, email_message: email.message.EmailMessage, header_name: str) -> str:
        """Извлекает и декодирует заголовок email"""
        try:
            header_value = email_message.get(header_name, '')
            if header_value:
                # Декодируем заголовок
                decoded_header = decode_header(header_value)
                decoded_parts = []
                
                for part, encoding in decoded_header:
                    if isinstance(part, bytes):
                        if encoding:
                            decoded_parts.append(part.decode(encoding))
                        else:
                            decoded_parts.append(part.decode('utf-8', errors='ignore'))
                    else:
                        decoded_parts.append(str(part))
                
                return ''.join(decoded_parts)
            return ''
        except Exception as e:
            logger.error(f"Error decoding header {header_name}: {e}")
            return header_value or ''
    
    def _extract_email_address(self, from_header: str) -> str:
        """Извлекает email адрес из заголовка From"""
        try:
            # Регулярное выражение для поиска email адреса
            email_pattern = r'<(.+?)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            matches = re.findall(email_pattern, from_header)
            
            if matches:
                # Возвращаем первый найденный email
                for match in matches:
                    email_addr = match[0] if match[0] else match[1]
                    if email_addr:
                        return email_addr.strip()
            
            return from_header.strip()
        except Exception as e:
            logger.error(f"Error extracting email address: {e}")
            return from_header
    
    def _extract_sender_name(self, from_header: str) -> str:
        """Извлекает имя отправителя из заголовка From"""
        try:
            # Удаляем email адрес и извлекаем имя
            email_pattern = r'<.+?>|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            name = re.sub(email_pattern, '', from_header).strip()
            
            # Убираем кавычки и лишние символы
            name = name.strip('"\'<> ')
            
            return name if name else self._extract_email_address(from_header)
        except Exception as e:
            logger.error(f"Error extracting sender name: {e}")
            return ''
    
    def _parse_email_date(self, date_header: str) -> Optional[str]:
        """Парсит дату email"""
        try:
            if date_header:
                # Используем встроенный парсер email даты
                from email.utils import parsedate_to_datetime
                parsed_date = parsedate_to_datetime(date_header)
                return parsed_date.isoformat()
            return None
        except Exception as e:
            logger.error(f"Error parsing email date: {e}")
            return None
    
    def _extract_email_content(self, email_message: email.message.EmailMessage) -> Dict[str, Any]:
        """Извлекает содержимое email (текст, HTML, вложения)"""
        content_data = {
            'body': '',
            'html_body': '',
            'attachments': []
        }
        
        try:
            if email_message.is_multipart():
                # Обрабатываем многочастное сообщение
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get('Content-Disposition', '')
                    
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        # Текстовое содержимое
                        payload = part.get_payload(decode=True)
                        if payload:
                            content_data['body'] += payload.decode('utf-8', errors='ignore')
                    
                    elif content_type == 'text/html' and 'attachment' not in content_disposition:
                        # HTML содержимое
                        payload = part.get_payload(decode=True)
                        if payload:
                            content_data['html_body'] += payload.decode('utf-8', errors='ignore')
                    
                    elif 'attachment' in content_disposition:
                        # Вложение
                        filename = part.get_filename()
                        if filename:
                            content_data['attachments'].append({
                                'filename': filename,
                                'content_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
            else:
                # Простое сообщение
                content_type = email_message.get_content_type()
                payload = email_message.get_payload(decode=True)
                
                if payload:
                    decoded_content = payload.decode('utf-8', errors='ignore')
                    if content_type == 'text/html':
                        content_data['html_body'] = decoded_content
                    else:
                        content_data['body'] = decoded_content
            
            return content_data
            
        except Exception as e:
            logger.error(f"Error extracting email content: {e}")
            return content_data
    
    def mark_as_read(self, email_id: str) -> bool:
        """Отмечает email как прочитанное"""
        try:
            if not self.connection:
                return False
            
            # Отмечаем как прочитанное
            self.connection.store(email_id, '+FLAGS', '\\Seen')
            return True
            
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    def move_to_folder(self, email_id: str, folder_name: str) -> bool:
        """Перемещает email в указанную папку"""
        try:
            if not self.connection:
                return False
            
            # Копируем в новую папку
            self.connection.copy(email_id, folder_name)
            
            # Помечаем для удаления из текущей папки
            self.connection.store(email_id, '+FLAGS', '\\Deleted')
            
            # Выполняем удаление
            self.connection.expunge()
            
            return True
            
        except Exception as e:
            logger.error(f"Error moving email to folder: {e}")
            return False
    
    def search_emails_by_thread(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Ищет все email в треде по thread_id"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # Ищем по Message-ID, In-Reply-To и References
            search_criteria = f'(OR OR (HEADER "Message-ID" "{thread_id}") (HEADER "In-Reply-To" "{thread_id}") (HEADER "References" "{thread_id}"))'
            
            status, messages = self.connection.search(None, search_criteria)
            
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()[:limit]  # Ограничиваем количество
            emails = []
            
            for email_id in email_ids:
                try:
                    email_data = self._fetch_email_by_id(email_id)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            # Сортируем по дате
            emails.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error searching emails by thread: {e}")
            return []
    
    def get_folder_list(self) -> List[str]:
        """Получает список доступных папок"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            status, folders = self.connection.list()
            
            if status != 'OK':
                return []
            
            folder_names = []
            for folder in folders:
                # Парсим имя папки из ответа IMAP
                folder_info = folder.decode('utf-8')
                # Извлекаем имя папки (последняя часть после кавычек)
                folder_name = folder_info.split('"')[-2] if '"' in folder_info else folder_info.split()[-1]
                folder_names.append(folder_name)
            
            return folder_names
            
        except Exception as e:
            logger.error(f"Error getting folder list: {e}")
            return []
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Создаем глобальный экземпляр
imap_handler = IMAPHandler()
