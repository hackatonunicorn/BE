#!/usr/bin/env python3
"""
Скрипт для запуска приложения Startup VC Platform
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("Требуется Python 3.8 или выше")
        sys.exit(1)
    print(f"Python {sys.version.split()[0]}")

def check_dependencies():
    """Проверка зависимостей"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("Основные зависимости установлены")
        return True
    except ImportError as e:
        print(f"Отсутствуют зависимости: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def setup_environment():
    """Настройка окружения"""
    # Создание .env файла если его нет
    env_file = Path(".env")
    if not env_file.exists():
        print("Создаем .env файл...")
        env_content = """# Database
DATABASE_URL=postgresql://user:password@localhost/startup_vc

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Environment
ENVIRONMENT=development
DEBUG=true

# External APIs (optional)
CLAUDE_API_KEY=your-claude-api-key
OPENAI_API_KEY=your-openai-api-key
"""
        env_file.write_text(env_content)
        print(".env файл создан")
    else:
        print(".env файл существует")

def create_directories():
    """Создание необходимых директорий"""
    dirs = ["logs", "uploads", "static"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("Директории созданы")

def run_database_migrations():
    """Запуск миграций базы данных"""
    try:
        print("Запуск миграций базы данных...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Миграции выполнены успешно")
            return True
        else:
            print(f"Ошибка миграций: {result.stderr}")
            return False
    except FileNotFoundError:
        print("Alembic не найден, пропускаем миграции")
        return True

def start_server():
    """Запуск сервера"""
    print("\nЗапуск сервера...")
    print("Приложение будет доступно по адресу: http://localhost:8000")
    print("API документация: http://localhost:8000/docs")
    print("Страница входа: http://localhost:8000/login")
    print("Страница регистрации: http://localhost:8000/register")
    print("\nДля остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        subprocess.run([
            "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    except Exception as e:
        print(f"\nОшибка запуска сервера: {e}")

def main():
    """Основная функция"""
    print("Startup VC Platform - Starting Application")
    print("=" * 50)
    
    # Проверки
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    # Настройка
    setup_environment()
    create_directories()
    
    # Миграции (опционально)
    run_database_migrations()
    
    # Запуск
    start_server()

if __name__ == "__main__":
    main()
