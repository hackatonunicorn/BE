"""
EmailGenerator class for generating personalized emails using Claude API
"""
import os
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime
import json

# Импорты для AI
try:
    import anthropic
except ImportError:
    anthropic = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateManager:
    """Менеджер для работы с шаблонами писем"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "email_templates"
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Загружает все шаблоны из папки"""
        try:
            for template_file in self.templates_dir.glob("*.txt"):
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates[template_name] = f.read()
                logger.info(f"Loaded email template: {template_name}")
        except Exception as e:
            logger.error(f"Error loading email templates: {e}")
    
    def get_template(self, template_name: str) -> Optional[str]:
        """Получает шаблон по имени"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """Возвращает список доступных шаблонов"""
        return list(self.templates.keys())


class EmailPersonalizer:
    """Класс для персонализации писем"""
    
    @staticmethod
    def extract_vc_contact_info(vc_fund_data: Dict[str, Any]) -> Dict[str, str]:
        """Извлекает контактную информацию о ВК"""
        contact_info = vc_fund_data.get('contact_info', {})
        
        if isinstance(contact_info, dict):
            return {
                'recipient_name': contact_info.get('partner_name', vc_fund_data.get('name', 'Investment Team')),
                'recipient_title': contact_info.get('title', 'Partner'),
                'fund_name': vc_fund_data.get('name', 'Your Fund')
            }
        else:
            return {
                'recipient_name': vc_fund_data.get('name', 'Investment Team'),
                'recipient_title': 'Team',
                'fund_name': vc_fund_data.get('name', 'Your Fund')
            }
    
    @staticmethod
    def extract_startup_info(startup_data: Dict[str, Any]) -> Dict[str, str]:
        """Извлекает информацию о стартапе"""
        return {
            'startup_name': startup_data.get('name', 'Our Company'),
            'sender_name': startup_data.get('contact_person', 'Founder'),
            'sender_title': 'Founder & CEO',  # Можно сделать настраиваемым
            'industry': startup_data.get('industry', 'Technology'),
            'stage': startup_data.get('stage', 'Early Stage'),
            'description': startup_data.get('description', 'Innovative solution'),
            'email': startup_data.get('email', ''),
            'contact_information': startup_data.get('email', '')
        }
    
    @staticmethod
    def create_alignment_context(startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any]) -> Dict[str, str]:
        """Создает контекст для выравнивания интересов стартапа и ВК"""
        startup_industry = startup_data.get('industry', '')
        vc_focus = vc_fund_data.get('focus_industries', [])
        startup_stage = startup_data.get('stage', '')
        vc_stages = vc_fund_data.get('investment_stages', [])
        
        # Проверяем совпадения
        industry_match = startup_industry in vc_focus if isinstance(vc_focus, list) else False
        stage_match = startup_stage in vc_stages if isinstance(vc_stages, list) else False
        
        alignment_reasons = []
        if industry_match:
            alignment_reasons.append(f"focus on {startup_industry}")
        if stage_match:
            alignment_reasons.append(f"{startup_stage} stage investments")
        
        geography = vc_fund_data.get('geography', '')
        if geography:
            alignment_reasons.append(f"presence in {geography}")
        
        return {
            'alignment_reasons': ', '.join(alignment_reasons) if alignment_reasons else 'strategic fit',
            'industry_focus_match': 'perfect' if industry_match else 'complementary',
            'stage_alignment': 'exact' if stage_match else 'suitable'
        }


class EmailGenerator:
    """Генератор персонализированных писем с использованием Claude API"""
    
    def __init__(self, claude_api_key: Optional[str] = None):
        self.claude_api_key = claude_api_key or os.getenv('CLAUDE_API_KEY') or getattr(settings, 'CLAUDE_API_KEY', None)
        
        self.client = None
        if self.claude_api_key and anthropic:
            try:
                self.client = anthropic.Anthropic(api_key=self.claude_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
        
        self.template_manager = EmailTemplateManager()
        self.personalizer = EmailPersonalizer()
    
    def _create_email_generation_prompt(self, 
                                      email_type: str,
                                      startup_data: Dict[str, Any], 
                                      vc_fund_data: Dict[str, Any],
                                      additional_context: str = "") -> str:
        """Создает промпт для генерации письма"""
        
        startup_info = self.personalizer.extract_startup_info(startup_data)
        vc_info = self.personalizer.extract_vc_contact_info(vc_fund_data)
        alignment = self.personalizer.create_alignment_context(startup_data, vc_fund_data)
        
        base_prompt = f"""
Generate a professional {email_type} email from a startup to a venture capital fund.

STARTUP INFORMATION:
- Company: {startup_info['startup_name']}
- Industry: {startup_info['industry']}
- Stage: {startup_info['stage']}
- Description: {startup_info['description']}
- Founder: {startup_info['sender_name']}

VC FUND INFORMATION:
- Fund: {vc_info['fund_name']}
- Contact: {vc_info['recipient_name']} ({vc_info['recipient_title']})
- Focus Industries: {', '.join(vc_fund_data.get('focus_industries', []))}
- Investment Stages: {', '.join(vc_fund_data.get('investment_stages', []))}
- Geography: {vc_fund_data.get('geography', 'Global')}
- Ticket Size: ${vc_fund_data.get('ticket_size_min', 0):,} - ${vc_fund_data.get('ticket_size_max', 0):,}

ALIGNMENT FACTORS:
- Alignment reasons: {alignment['alignment_reasons']}
- Industry focus: {alignment['industry_focus_match']} match
- Stage alignment: {alignment['stage_alignment']} fit

{additional_context}

EMAIL REQUIREMENTS:
1. Professional, concise tone
2. Clear value proposition
3. Specific to this VC's focus areas
4. Include relevant traction/metrics if available
5. Strong but respectful call-to-action
6. Maximum 250 words
7. Subject line should be compelling and specific

Generate both subject line and email body. Format as:
SUBJECT: [subject line]

BODY:
[email content]
"""
        return base_prompt
    
    async def generate_initial_email(self, startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any]) -> Dict[str, str]:
        """Генерирует первичное письмо стартапа к ВК"""
        
        additional_context = """
EMAIL TYPE: Initial Outreach
PURPOSE: Introduce the startup and gauge investment interest
TONE: Professional, confident, but not pushy
STRUCTURE:
1. Brief personal greeting
2. Company introduction (1-2 sentences)
3. Why this VC is a good fit
4. Key traction points or achievements
5. Clear ask for meeting/call
6. Professional closing
"""
        
        if self.client:
            return await self._generate_with_claude("initial outreach", startup_data, vc_fund_data, additional_context)
        else:
            return self._generate_template_based("initial_outreach", startup_data, vc_fund_data)
    
    async def generate_follow_up(self, 
                               previous_context: Dict[str, Any], 
                               vc_response: str = "", 
                               intent: str = "follow_up") -> Dict[str, str]:
        """Генерирует follow-up письмо"""
        
        startup_data = previous_context.get('startup_data', {})
        vc_fund_data = previous_context.get('vc_fund_data', {})
        
        additional_context = f"""
EMAIL TYPE: Follow-up
PREVIOUS CONTEXT: {previous_context.get('summary', 'Previous email sent')}
VC RESPONSE: {vc_response or 'No response received'}
INTENT: {intent}
PURPOSE: Re-engage and provide additional value
TONE: Persistent but respectful, add new information
STRUCTURE:
1. Reference previous communication
2. Provide update or new information
3. Reiterate value proposition
4. Specific ask with timeline
5. Professional closing
"""
        
        if self.client:
            return await self._generate_with_claude("follow-up", startup_data, vc_fund_data, additional_context)
        else:
            return self._generate_template_based("follow_up", startup_data, vc_fund_data)
    
    async def generate_meeting_request(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Генерирует запрос на встречу"""
        
        startup_data = context.get('startup_data', {})
        vc_fund_data = context.get('vc_fund_data', {})
        meeting_purpose = context.get('purpose', 'pitch presentation')
        
        additional_context = f"""
EMAIL TYPE: Meeting Request
PURPOSE: {meeting_purpose}
TONE: Professional, specific about meeting logistics
STRUCTURE:
1. Thank for previous interest/response
2. Propose specific meeting agenda
3. Offer multiple time options
4. Mention any materials to share
5. Confirm logistics (location/video call)
6. Professional closing
"""
        
        if self.client:
            return await self._generate_with_claude("meeting request", startup_data, vc_fund_data, additional_context)
        else:
            return self._generate_template_based("meeting_request", startup_data, vc_fund_data)
    
    async def _generate_with_claude(self, 
                                  email_type: str,
                                  startup_data: Dict[str, Any], 
                                  vc_fund_data: Dict[str, Any],
                                  additional_context: str) -> Dict[str, str]:
        """Генерирует письмо с помощью Claude API"""
        try:
            prompt = self._create_email_generation_prompt(email_type, startup_data, vc_fund_data, additional_context)
            
            response = await asyncio.create_task(
                asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            
            content = response.content[0].text if response.content else ""
            
            # Парсим ответ
            if "SUBJECT:" in content and "BODY:" in content:
                subject_start = content.find("SUBJECT:") + 8
                body_start = content.find("BODY:") + 5
                
                subject = content[subject_start:body_start-5].strip()
                body = content[body_start:].strip()
                
                return {
                    'subject': subject,
                    'body': body,
                    'generated_by': 'claude_ai',
                    'generated_at': datetime.now().isoformat()
                }
            else:
                # Если формат не совпадает, используем весь ответ как body
                return {
                    'subject': f"Partnership Opportunity - {startup_data.get('name', 'Our Company')}",
                    'body': content,
                    'generated_by': 'claude_ai',
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating email with Claude: {e}")
            return self._generate_template_based(email_type.replace(" ", "_"), startup_data, vc_fund_data)
    
    def _generate_template_based(self, template_name: str, startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any]) -> Dict[str, str]:
        """Генерирует письмо на основе шаблона (fallback)"""
        
        template = self.template_manager.get_template(template_name)
        if not template:
            template = self.template_manager.get_template("initial_outreach")
        
        if not template:
            return {
                'subject': f"Partnership Opportunity - {startup_data.get('name', 'Our Company')}",
                'body': self._create_basic_email(startup_data, vc_fund_data),
                'generated_by': 'template_fallback',
                'generated_at': datetime.now().isoformat()
            }
        
        # Извлекаем данные для подстановки
        startup_info = self.personalizer.extract_startup_info(startup_data)
        vc_info = self.personalizer.extract_vc_contact_info(vc_fund_data)
        alignment = self.personalizer.create_alignment_context(startup_data, vc_fund_data)
        
        # Создаем контекст для подстановки
        context = {
            **startup_info,
            **vc_info,
            **alignment,
            'subject': f"Partnership Opportunity - {startup_info['startup_name']}",
            'opening_line': f"I'm writing to introduce {startup_info['startup_name']}, a {startup_info['stage']} {startup_info['industry']} company.",
            'problem_statement': f"We're addressing a significant challenge in the {startup_info['industry']} space.",
            'solution_overview': startup_info['description'],
            'market_opportunity': f"The {startup_info['industry']} market presents substantial growth opportunities.",
            'traction_highlights': "We've gained significant traction with early customers and strong product-market fit.",
            'funding_request': f"We're currently raising our {startup_info['stage']} round to accelerate growth.",
            'call_to_action': "I'd love to schedule a brief call to discuss how we might work together.",
            'sender_signature': f"{startup_info['sender_name']}\n{startup_info['sender_title']}",
            'follow_up_opener': f"I wanted to follow up on my previous email regarding {startup_info['startup_name']}.",
            'progress_update': "Since our last communication, we've made significant progress.",
            'additional_context': "I believe this makes us an even stronger fit for your portfolio.",
            'specific_ask': "Would you be available for a 20-minute call this week?",
            'closing_line': "Thank you for your time and consideration.",
            'meeting_opener': f"Thank you for your interest in {startup_info['startup_name']}.",
            'meeting_purpose': "I'd like to schedule a meeting to present our business in detail.",
            'proposed_agenda': "We can cover our business model, market opportunity, and growth strategy.",
            'time_availability': "I'm available most days this week and next.",
            'meeting_logistics': "We can meet in person or via video call, whatever works best for you.",
            'confirmation_request': "Please let me know what time works best for your schedule.",
            'sharing_opener': f"As requested, I'm sharing our investor deck for {startup_info['startup_name']}.",
            'deck_overview': "The deck provides a comprehensive overview of our business opportunity.",
            'key_highlights': "Key highlights include our market traction and financial projections.",
            'next_steps': "I'm happy to walk through the deck with you in detail.",
            'availability': "I'm available for a call at your convenience.",
            'update_opener': f"I wanted to share some exciting updates about {startup_info['startup_name']}.",
            'milestone_updates': "We've achieved several key milestones since our last conversation.",
            'metrics_update': "Our key metrics continue to show strong growth.",
            'upcoming_plans': "We have exciting plans for the coming months.",
            'continued_interest': "I hope this reinforces your interest in our company."
        }
        
        # Подставляем значения в шаблон
        try:
            filled_template = template.format(**context)
            
            # Извлекаем subject line, если есть
            lines = filled_template.split('\n')
            subject = context['subject']
            body = filled_template
            
            if lines[0].startswith('Subject:'):
                subject = lines[0].replace('Subject:', '').strip()
                body = '\n'.join(lines[1:]).strip()
            
            return {
                'subject': subject,
                'body': body,
                'generated_by': 'template_based',
                'generated_at': datetime.now().isoformat()
            }
            
        except KeyError as e:
            logger.error(f"Template formatting error: {e}")
            return {
                'subject': context['subject'],
                'body': self._create_basic_email(startup_data, vc_fund_data),
                'generated_by': 'basic_fallback',
                'generated_at': datetime.now().isoformat()
            }
    
    def _create_basic_email(self, startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any]) -> str:
        """Создает базовое письмо без шаблона"""
        startup_info = self.personalizer.extract_startup_info(startup_data)
        vc_info = self.personalizer.extract_vc_contact_info(vc_fund_data)
        
        return f"""Dear {vc_info['recipient_name']},

I hope this email finds you well. I'm {startup_info['sender_name']}, {startup_info['sender_title']} at {startup_info['startup_name']}.

{startup_info['startup_name']} is a {startup_info['stage']} {startup_info['industry']} company. {startup_info['description']}

Given {vc_info['fund_name']}'s focus on {', '.join(vc_fund_data.get('focus_industries', ['technology']))}, I believe there could be a strong strategic fit between our vision and your investment thesis.

I would love the opportunity to discuss how we can create value together. Would you be available for a brief call in the coming weeks?

Best regards,
{startup_info['sender_name']}
{startup_info['sender_title']}
{startup_info['startup_name']}
{startup_info['contact_information']}"""

    async def generate_pitch_deck_email(self, startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any]) -> Dict[str, str]:
        """Генерирует письмо для отправки питч-дека"""
        additional_context = """
EMAIL TYPE: Pitch Deck Sharing
PURPOSE: Share investor materials and schedule presentation
TONE: Professional, confident about the opportunity
STRUCTURE:
1. Thank for interest shown
2. Attach/reference pitch deck
3. Highlight key points from deck
4. Suggest next steps (meeting/call)
5. Offer to answer questions
"""
        
        if self.client:
            return await self._generate_with_claude("pitch deck sharing", startup_data, vc_fund_data, additional_context)
        else:
            return self._generate_template_based("pitch_deck_sharing", startup_data, vc_fund_data)
    
    async def generate_update_email(self, startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any], updates: List[str]) -> Dict[str, str]:
        """Генерирует письмо с обновлениями"""
        updates_text = '\n'.join(f"- {update}" for update in updates)
        
        additional_context = f"""
EMAIL TYPE: Company Update
PURPOSE: Share progress and maintain investor interest
RECENT UPDATES:
{updates_text}
TONE: Exciting but professional, show momentum
STRUCTURE:
1. Greeting and context
2. Key updates and milestones
3. Metrics and traction
4. Future plans
5. Continued engagement ask
"""
        
        if self.client:
            return await self._generate_with_claude("company update", startup_data, vc_fund_data, additional_context)
        else:
            return self._generate_template_based("update_email", startup_data, vc_fund_data)
    
    def get_available_templates(self) -> List[str]:
        """Возвращает список доступных шаблонов"""
        return self.template_manager.list_templates()
    
    def generate_email_sync(self, email_type: str, startup_data: Dict[str, Any], vc_fund_data: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """Синхронная версия генерации письма для использования в API"""
        try:
            if email_type == "initial_outreach":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.generate_initial_email(startup_data, vc_fund_data))
                loop.close()
                return result
            elif email_type == "follow_up":
                previous_context = kwargs.get('previous_context', {})
                vc_response = kwargs.get('vc_response', '')
                intent = kwargs.get('intent', 'follow_up')
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.generate_follow_up(previous_context, vc_response, intent))
                loop.close()
                return result
            elif email_type == "meeting_request":
                context = kwargs.get('context', {})
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.generate_meeting_request(context))
                loop.close()
                return result
            else:
                # Fallback to template-based generation
                return self._generate_template_based(email_type, startup_data, vc_fund_data)
        except Exception as e:
            logger.error(f"Error in sync email generation: {e}")
            return {
                'subject': f"Partnership Opportunity - {startup_data.get('name', 'Our Company')}",
                'body': self._create_basic_email(startup_data, vc_fund_data),
                'generated_by': 'error_fallback',
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }


# Создаем глобальный экземпляр для использования
email_generator = EmailGenerator()
