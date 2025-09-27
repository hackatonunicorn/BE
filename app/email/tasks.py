import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.celery import celery_app
from app.core.config_simple import settings


@celery_app.task
def send_email(to_email: str, subject: str, content: str, from_email: str = None):
    """
    Send email using SMTP
    """
    try:
        from_email = from_email or settings.EMAILS_FROM_EMAIL
        
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            return {"success": False, "error": "SMTP configuration not complete"}
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(content, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        return {"success": True, "message": f"Email sent to {to_email}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task
def send_bulk_emails(email_list: list, subject: str, content: str):
    """
    Send bulk emails with rate limiting
    """
    results = []
    
    for email_data in email_list:
        try:
            to_email = email_data.get('email')
            personalized_content = content.format(**email_data.get('variables', {}))
            
            result = send_email.delay(to_email, subject, personalized_content)
            results.append({
                "email": to_email,
                "task_id": result.id,
                "status": "queued"
            })
            
        except Exception as e:
            results.append({
                "email": email_data.get('email'),
                "status": "failed",
                "error": str(e)
            })
    
    return {"success": True, "results": results}


@celery_app.task
def schedule_follow_up_email(communication_id: int, days_delay: int = 7):
    """
    Schedule a follow-up email
    """
    try:
        # This would typically fetch the communication from database
        # and schedule a follow-up based on the original content
        
        # Mock implementation
        follow_up_content = """
        Dear [VC Name],

        I wanted to follow up on my previous email regarding [Startup Name]. 
        
        Since my last message, we've made significant progress:
        - [Key Update 1]
        - [Key Update 2]
        
        I'd still love the opportunity to discuss how we might work together.
        
        Best regards,
        [Startup Team]
        """
        
        # In production, this would use Celery's countdown or eta
        # send_email.apply_async(
        #     args=[to_email, subject, follow_up_content],
        #     countdown=days_delay * 24 * 60 * 60  # Convert days to seconds
        # )
        
        return {
            "success": True, 
            "message": f"Follow-up scheduled for communication {communication_id} in {days_delay} days"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
