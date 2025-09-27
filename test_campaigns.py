#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API кампаний
"""

import requests
import json
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def get_auth_headers():
    """Получить заголовки аутентификации"""
    # Попробуем использовать существующий токен или создать нового пользователя
    try:
        # Сначала попробуем залогиниться
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123",
            "remember_me": False
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["tokens"]["access_token"]
            return {"Authorization": f"Bearer {token}"}
    except:
        pass
    
    # Если не удалось залогиниться, создадим нового пользователя
    register_data = {
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Test Company",
        "role": "startup"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code == 201:
        token = response.json()["tokens"]["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    raise Exception("Не удалось получить токен аутентификации")

def test_campaign_options():
    """Тест получения опций для создания кампаний"""
    print("🔍 Тестируем получение опций кампаний...")
    try:
        response = requests.get(f"{API_BASE}/campaigns/options")
        print(f"✅ Campaign options: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Industries: {len(data['industries'])}")
            print(f"   Funding stages: {len(data['funding_stages'])}")
            print(f"   Team sizes: {len(data['team_sizes'])}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Campaign options failed: {e}")
        return False

def test_create_campaign(headers):
    """Тест создания кампании"""
    print("\n🔍 Тестируем создание кампании...")
    
    campaign_data = {
        "name": "Test Campaign",
        "description": "Test campaign for fundraising",
        "company_name": "Test Tech Inc.",
        "company_website": "https://testtech.com",
        "industry": "saas",
        "current_funding_stage": "seed",
        "team_size": "6-20",
        "location": "San Francisco, CA",
        "target_raise_amount": 1000000.0,
        "fundraising_timeline": "6-12 months",
        "use_of_funds": ["product_development", "team_expansion"],
        "previous_funding": "friends_family"
    }
    
    try:
        response = requests.post(f"{API_BASE}/campaigns/", json=campaign_data, headers=headers)
        print(f"✅ Create campaign: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   Campaign ID: {data['id']}")
            print(f"   Name: {data['name']}")
            print(f"   Status: {data['status']}")
            print(f"   Company: {data['company_name']}")
            return data['id']
        else:
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Create campaign failed: {e}")
        return None

def test_get_campaigns(headers):
    """Тест получения списка кампаний"""
    print("\n🔍 Тестируем получение списка кампаний...")
    
    try:
        response = requests.get(f"{API_BASE}/campaigns/", headers=headers)
        print(f"✅ Get campaigns: {response.status_code}")
        
        if response.status_code == 200:
            campaigns = response.json()
            print(f"   Found {len(campaigns)} campaigns")
            for campaign in campaigns:
                print(f"   - {campaign['name']} ({campaign['status']})")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Get campaigns failed: {e}")
        return False

def test_get_campaign(headers, campaign_id):
    """Тест получения конкретной кампании"""
    print("\n🔍 Тестируем получение кампании по ID...")
    
    try:
        response = requests.get(f"{API_BASE}/campaigns/{campaign_id}", headers=headers)
        print(f"✅ Get campaign: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Name: {data['name']}")
            print(f"   Company: {data['company_name']}")
            print(f"   Industry: {data['industry']}")
            print(f"   Target raise: ${data['target_raise_amount']:,}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Get campaign failed: {e}")
        return False

def test_update_campaign(headers, campaign_id):
    """Тест обновления кампании"""
    print("\n🔍 Тестируем обновление кампании...")
    
    update_data = {
        "name": "Updated Test Campaign",
        "description": "Updated description",
        "target_raise_amount": 1500000.0
    }
    
    try:
        response = requests.put(f"{API_BASE}/campaigns/{campaign_id}", json=update_data, headers=headers)
        print(f"✅ Update campaign: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Updated name: {data['name']}")
            print(f"   Updated target: ${data['target_raise_amount']:,}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Update campaign failed: {e}")
        return False

def test_update_campaign_status(headers, campaign_id):
    """Тест обновления статуса кампании"""
    print("\n🔍 Тестируем обновление статуса кампании...")
    
    status_data = {"status": "active"}
    
    try:
        response = requests.patch(f"{API_BASE}/campaigns/{campaign_id}/status", json=status_data, headers=headers)
        print(f"✅ Update campaign status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   New status: {data['status']}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Update campaign status failed: {e}")
        return False

def test_campaign_stats(headers):
    """Тест получения статистики кампаний"""
    print("\n🔍 Тестируем получение статистики кампаний...")
    
    try:
        response = requests.get(f"{API_BASE}/campaigns/stats", headers=headers)
        print(f"✅ Get campaign stats: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Total campaigns: {data['total_campaigns']}")
            print(f"   Active campaigns: {data['active_campaigns']}")
            print(f"   Draft campaigns: {data['draft_campaigns']}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Get campaign stats failed: {e}")
        return False

def test_delete_campaign(headers, campaign_id):
    """Тест удаления кампании"""
    print("\n🔍 Тестируем удаление кампании...")
    
    try:
        response = requests.delete(f"{API_BASE}/campaigns/{campaign_id}", headers=headers)
        print(f"✅ Delete campaign: {response.status_code}")
        
        if response.status_code == 204:
            print("   Campaign deleted successfully")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Delete campaign failed: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов API кампаний")
    print("=" * 50)
    
    try:
        # Получаем токен аутентификации
        headers = get_auth_headers()
        print("✅ Получен токен аутентификации")
        
        # Тест опций кампаний
        options_ok = test_campaign_options()
        
        # Тест создания кампании
        campaign_id = test_create_campaign(headers)
        
        if campaign_id:
            # Тест получения списка кампаний
            list_ok = test_get_campaigns(headers)
            
            # Тест получения конкретной кампании
            get_ok = test_get_campaign(headers, campaign_id)
            
            # Тест обновления кампании
            update_ok = test_update_campaign(headers, campaign_id)
            
            # Тест обновления статуса
            status_ok = test_update_campaign_status(headers, campaign_id)
            
            # Тест статистики
            stats_ok = test_campaign_stats(headers)
            
            # Тест удаления кампании
            delete_ok = test_delete_campaign(headers, campaign_id)
        else:
            list_ok = get_ok = update_ok = status_ok = stats_ok = delete_ok = False
        
        # Результаты
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Campaign Options: {'✅' if options_ok else '❌'}")
        print(f"   Create Campaign: {'✅' if campaign_id else '❌'}")
        print(f"   Get Campaigns List: {'✅' if list_ok else '❌'}")
        print(f"   Get Campaign: {'✅' if get_ok else '❌'}")
        print(f"   Update Campaign: {'✅' if update_ok else '❌'}")
        print(f"   Update Status: {'✅' if status_ok else '❌'}")
        print(f"   Campaign Stats: {'✅' if stats_ok else '❌'}")
        print(f"   Delete Campaign: {'✅' if delete_ok else '❌'}")
        
        if all([options_ok, campaign_id, list_ok, get_ok, update_ok, status_ok, stats_ok, delete_ok]):
            print("\n🎉 Все тесты прошли успешно!")
        else:
            print("\n⚠️  Некоторые тесты не прошли. Проверьте логи сервера.")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
