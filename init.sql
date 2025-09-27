-- Initialize database with sample data for development

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sample startups
INSERT INTO startups (name, industry, stage, description, email, contact_person, pitch_deck_path, pitch_analysis_result) VALUES
('TechStartup', 'Technology', 'Seed', 'AI-powered customer service automation platform that helps businesses reduce response times by 80%', 'contact@techstartup.com', 'John Smith', 'uploads/techstartup_pitch.pdf', 
'{"market_size": "50B", "competitive_advantages": ["AI technology", "Team experience"], "funding_needs": "2M", "risk_factors": ["Market competition", "Technical challenges"]}'),

('GreenTech Solutions', 'CleanTech', 'Series A', 'Sustainable energy management platform for commercial buildings using IoT sensors and machine learning', 'info@greentech.com', 'Sarah Johnson', 'uploads/greentech_pitch.pdf',
'{"market_size": "120B", "competitive_advantages": ["Proprietary algorithms", "Strong partnerships"], "funding_needs": "5M", "risk_factors": ["Regulatory changes", "Hardware dependencies"]}'),

('HealthTech Innovations', 'HealthTech', 'Seed', 'Telemedicine platform connecting patients with specialists in underserved areas', 'team@healthtech.com', 'Dr. Michael Chen', NULL, NULL),

('FinTech Pro', 'FinTech', 'Series A', 'Blockchain-based payment solution for cross-border transactions', 'founders@fintechpro.com', 'Alex Rodriguez', 'uploads/fintech_pitch.pdf',
'{"market_size": "200B", "competitive_advantages": ["Blockchain security", "Low transaction costs"], "funding_needs": "10M", "risk_factors": ["Regulatory uncertainty", "Market adoption"]}');

-- Sample VC Funds
INSERT INTO vc_funds (name, focus_industries, investment_stages, geography, ticket_size_min, ticket_size_max, email, contact_info, matching_criteria) VALUES
('Innovation Ventures', 
'["Technology", "AI/ML", "SaaS"]', 
'["Seed", "Series A"]', 
'Silicon Valley, CA', 
500000, 
5000000, 
'investments@innovationvc.com',
'{"partner_name": "David Wilson", "title": "Managing Partner", "email": "david@innovationvc.com", "phone": "+1-415-555-0123"}',
'{"min_revenue": 100000, "team_size_min": 5, "preferred_sectors": ["B2B Software", "AI"], "geographic_preference": ["US West Coast"]}'),

('Green Capital Partners', 
'["CleanTech", "Sustainability", "Energy"]', 
'["Series A", "Series B"]', 
'San Francisco, CA', 
2000000, 
15000000, 
'deals@greencapital.com',
'{"partner_name": "Lisa Thompson", "title": "Investment Director", "email": "lisa@greencapital.com", "phone": "+1-415-555-0234"}',
'{"min_revenue": 1000000, "sustainability_focus": true, "geographic_preference": ["US", "Europe"]}'),

('Digital Health Ventures', 
'["HealthTech", "Biotech", "Digital Health"]', 
'["Seed", "Series A", "Series B"]', 
'Boston, MA', 
1000000, 
20000000, 
'investments@healthvc.com',
'{"partner_name": "Dr. Robert Kim", "title": "General Partner", "email": "robert@healthvc.com", "phone": "+1-617-555-0345"}',
'{"healthcare_expertise": true, "regulatory_experience": true, "geographic_preference": ["US East Coast", "Europe"]}'),

('FinTech Capital', 
'["FinTech", "Blockchain", "Payments", "Financial Services"]', 
'["Series A", "Series B", "Series C"]', 
'New York, NY', 
5000000, 
50000000, 
'deals@fintechcap.com',
'{"partner_name": "Maria Garcia", "title": "Senior Partner", "email": "maria@fintechcap.com", "phone": "+1-212-555-0456"}',
'{"fintech_focus": true, "min_revenue": 5000000, "geographic_preference": ["Global"], "crypto_friendly": true}');

-- Sample communications
INSERT INTO communications (startup_id, vc_fund_id, status, email_thread_id, last_message_at, generated_emails, escalated_to_human) VALUES
(1, 1, 'in_progress', 'thread_001_techstartup_innovation', NOW() - INTERVAL '5 days', 
'[{"type": "initial_outreach", "subject": "Partnership Opportunity - TechStartup", "sent_at": "2024-01-10T10:00:00Z", "status": "sent"}]', false),

(2, 2, 'meeting_scheduled', 'thread_002_greentech_green', NOW() - INTERVAL '2 days', 
'[{"type": "initial_outreach", "subject": "Partnership Opportunity - GreenTech Solutions", "sent_at": "2024-01-12T14:30:00Z", "status": "sent"}, {"type": "follow_up", "subject": "Follow-up: GreenTech Partnership", "sent_at": "2024-01-15T09:00:00Z", "status": "replied"}]', false),

(3, 3, 'initiated', 'thread_003_healthtech_digital', NOW() - INTERVAL '1 day', 
'[{"type": "initial_outreach", "subject": "Partnership Opportunity - HealthTech Innovations", "sent_at": "2024-01-16T16:00:00Z", "status": "sent"}]', false),

(4, 4, 'closed', 'thread_004_fintech_capital', NOW() - INTERVAL '30 days', 
'[{"type": "initial_outreach", "subject": "Partnership Opportunity - FinTech Pro", "sent_at": "2023-12-15T11:00:00Z", "status": "sent"}, {"type": "follow_up", "subject": "Follow-up: FinTech Partnership", "sent_at": "2023-12-22T10:00:00Z", "status": "no_response"}, {"type": "escalation", "reason": "No response after multiple attempts", "escalated_at": "2024-01-05T15:00:00Z"}]', true);

-- Sample meetings
INSERT INTO meetings (communication_id, scheduled_at, meeting_link, status, notes) VALUES
(2, NOW() + INTERVAL '3 days', 'https://zoom.us/j/123456789', 'scheduled', 'Initial pitch meeting with GreenTech Solutions'),
(2, NOW() - INTERVAL '7 days', 'https://zoom.us/j/987654321', 'completed', 'Great initial meeting. Interested in due diligence process. Next steps: financial review and team interviews.'),
(4, NOW() - INTERVAL '45 days', 'https://meet.google.com/abc-defg-hij', 'cancelled', 'Meeting cancelled due to misaligned investment criteria');
