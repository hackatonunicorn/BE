#!/usr/bin/env python3
"""
Простой тест для проверки запуска приложения
"""

import urllib.request
import json

def test_health():
    """Тест health check"""
    try:
        with urllib.request.urlopen('http://localhost:8000/health') as response:
            data = json.loads(response.read().decode())
            print("Health Check: SUCCESS")
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Version: {data.get('version', 'unknown')}")
            return True
    except Exception as e:
        print(f"Health Check: FAILED - {e}")
        return False

def test_api_health():
    """Тест API health check"""
    try:
        with urllib.request.urlopen('http://localhost:8000/api/health') as response:
            data = json.loads(response.read().decode())
            print("API Health Check: SUCCESS")
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Database: {data.get('database', 'unknown')}")
            return True
    except Exception as e:
        print(f"API Health Check: FAILED - {e}")
        return False

def test_campaigns_options():
    """Тест получения опций кампаний"""
    try:
        with urllib.request.urlopen('http://localhost:8000/api/campaigns/options') as response:
            data = json.loads(response.read().decode())
            print("Campaign Options: SUCCESS")
            print(f"Industries: {len(data.get('industries', []))}")
            print(f"Funding Stages: {len(data.get('funding_stages', []))}")
            return True
    except Exception as e:
        print(f"Campaign Options: FAILED - {e}")
        return False

def main():
    print("Testing Startup VC Platform")
    print("=" * 40)
    
    health_ok = test_health()
    api_health_ok = test_api_health()
    campaigns_ok = test_campaigns_options()
    
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"API Health: {'PASS' if api_health_ok else 'FAIL'}")
    print(f"Campaigns API: {'PASS' if campaigns_ok else 'FAIL'}")
    
    if all([health_ok, api_health_ok, campaigns_ok]):
        print("\nSUCCESS: All tests passed!")
        print("\nApplication is running at:")
        print("- Main app: http://localhost:8000")
        print("- API docs: http://localhost:8000/docs")
        print("- Login: http://localhost:8000/login")
        print("- Register: http://localhost:8000/register")
    else:
        print("\nSOME TESTS FAILED: Check server logs")

if __name__ == "__main__":
    main()
