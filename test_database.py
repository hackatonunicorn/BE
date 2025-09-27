#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы с базой данных
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import check_db_connection
from app.data.models import Base, Startup, VCFund, Communication, Meeting
from app.data.repositories import (
    startup_repository, 
    vc_fund_repository, 
    communication_repository, 
    meeting_repository
)

def test_database_connection():
    """Тест подключения к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    if check_db_connection():
        print("✅ Подключение к базе данных успешно!")
        return True
    else:
        print("❌ Ошибка подключения к базе данных!")
        return False

def test_models():
    """Тест создания таблиц"""
    print("\n📋 Тестирование моделей...")
    
    try:
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы успешно созданы!")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def test_repositories():
    """Тест репозиториев"""
    print("\n🏪 Тестирование репозиториев...")
    
    try:
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Тест статистики (должны работать даже с пустой БД)
        startup_stats = startup_repository.get_statistics(db)
        print(f"📊 Статистика стартапов: {startup_stats}")
        
        vc_stats = vc_fund_repository.get_statistics(db)
        print(f"📊 Статистика ВК: {vc_stats}")
        
        comm_stats = communication_repository.get_communication_statistics(db)
        print(f"📊 Статистика коммуникаций: {comm_stats}")
        
        meeting_stats = meeting_repository.get_meeting_statistics(db)
        print(f"📊 Статистика встреч: {meeting_stats}")
        
        db.close()
        print("✅ Репозитории работают корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования репозиториев: {e}")
        return False

def test_sample_data():
    """Тест работы с образцовыми данными"""
    print("\n📝 Тестирование образцовых данных...")
    
    try:
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Получаем образцовые данные
        startups = startup_repository.get_multi(db, limit=5)
        print(f"🚀 Найдено стартапов: {len(startups)}")
        
        vcs = vc_fund_repository.get_multi(db, limit=5)
        print(f"💰 Найдено ВК фондов: {len(vcs)}")
        
        communications = communication_repository.get_multi(db, limit=5)
        print(f"📧 Найдено коммуникаций: {len(communications)}")
        
        meetings = meeting_repository.get_multi(db, limit=5)
        print(f"🤝 Найдено встреч: {len(meetings)}")
        
        # Детали первого стартапа, если есть
        if startups:
            startup = startups[0]
            print(f"\n📋 Детали стартапа '{startup.name}':")
            print(f"   Индустрия: {startup.industry}")
            print(f"   Стадия: {startup.stage}")
            print(f"   Email: {startup.email}")
            print(f"   Контакт: {startup.contact_person}")
        
        # Детали первого ВК, если есть
        if vcs:
            vc = vcs[0]
            print(f"\n💼 Детали ВК '{vc.name}':")
            print(f"   География: {vc.geography}")
            print(f"   Фокус индустрии: {vc.focus_industries}")
            print(f"   Стадии инвестиций: {vc.investment_stages}")
            print(f"   Размер чека: ${vc.ticket_size_min:,} - ${vc.ticket_size_max:,}")
        
        db.close()
        print("\n✅ Образцовые данные успешно загружены!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка работы с образцовыми данными: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Тестирование системы базы данных")
    print("=" * 50)
    
    success = True
    
    # Тест подключения
    success &= test_database_connection()
    
    # Тест моделей
    success &= test_models()
    
    # Тест репозиториев
    success &= test_repositories()
    
    # Тест образцовых данных
    success &= test_sample_data()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("\n📝 Следующие шаги:")
        print("1. Запустите Docker Compose: docker-compose up -d")
        print("2. Примените миграции: docker-compose exec web alembic upgrade head")
        print("3. Загрузите тестовые данные: docker-compose exec db psql -U postgres -d startup_vc_platform -f /docker-entrypoint-initdb.d/init.sql")
        print("4. Запустите API: python run.py")
        print("5. Откройте документацию: http://localhost:8000/docs")
    else:
        print("❌ Некоторые тесты не прошли. Проверьте конфигурацию.")
    
    return success

if __name__ == "__main__":
    main()
