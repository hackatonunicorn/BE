#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы аутентификации
"""

import requests
import json
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_health():
    """Тест health check"""
    print("🔍 Тестируем health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_health():
    """Тест API health check"""
    print("\n🔍 Тестируем API health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ API Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ API Health check failed: {e}")
        return False

def test_user_registration():
    """Тест регистрации пользователя"""
    print("\n🔍 Тестируем регистрацию пользователя...")
    
    user_data = {
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Test Company",
        "role": "startup"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"✅ Registration: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   User ID: {data['user']['id']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Role: {data['user']['role']}")
            print(f"   Has access token: {'access_token' in data['tokens']}")
            return data['tokens']['access_token']
        else:
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return None

def test_user_login():
    """Тест входа пользователя"""
    print("\n🔍 Тестируем вход пользователя...")
    
    login_data = {
        "email": "admin@example.com",  # Предполагаем, что есть тестовый пользователь
        "password": "admin123",
        "remember_me": False
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"✅ Login: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   User: {data['user']['full_name']}")
            print(f"   Role: {data['user']['role']}")
            print(f"   Has access token: {'access_token' in data['tokens']}")
            return data['tokens']['access_token']
        else:
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return None

def test_protected_endpoint(access_token):
    """Тест защищенного endpoint"""
    print("\n🔍 Тестируем защищенный endpoint...")
    
    if not access_token:
        print("❌ No access token available")
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        print(f"✅ Protected endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   User: {data['full_name']}")
            print(f"   Email: {data['email']}")
            print(f"   Role: {data['role']}")
            print(f"   Active: {data['is_active']}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Protected endpoint failed: {e}")
        return False

def test_web_pages():
    """Тест веб-страниц"""
    print("\n🔍 Тестируем веб-страницы...")
    
    pages = [
        ("/", "Home"),
        ("/login", "Login"),
        ("/register", "Register"),
    ]
    
    results = []
    for path, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}")
            print(f"✅ {name} page: {response.status_code}")
            results.append(True)
        except Exception as e:
            print(f"❌ {name} page failed: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов системы аутентификации")
    print("=" * 50)
    
    # Тест health checks
    health_ok = test_health()
    api_health_ok = test_api_health()
    
    if not health_ok or not api_health_ok:
        print("\n❌ Базовые тесты не прошли. Проверьте, что сервер запущен.")
        return
    
    # Тест веб-страниц
    pages_ok = test_web_pages()
    
    # Тест регистрации
    registration_token = test_user_registration()
    
    # Тест входа
    login_token = test_user_login()
    
    # Тест защищенных endpoints
    token = registration_token or login_token
    protected_ok = test_protected_endpoint(token)
    
    # Результаты
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   Health Check: {'✅' if health_ok else '❌'}")
    print(f"   API Health: {'✅' if api_health_ok else '❌'}")
    print(f"   Web Pages: {'✅' if pages_ok else '❌'}")
    print(f"   Registration: {'✅' if registration_token else '❌'}")
    print(f"   Login: {'✅' if login_token else '❌'}")
    print(f"   Protected Endpoints: {'✅' if protected_ok else '❌'}")
    
    if all([health_ok, api_health_ok, pages_ok, token, protected_ok]):
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n⚠️  Некоторые тесты не прошли. Проверьте логи сервера.")

if __name__ == "__main__":
    main()
