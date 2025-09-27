"""
A/B Testing System для email шаблонов
"""
import os
import logging
import random
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from app.email.templates.template_engine import TemplateVariant, TemplateType
from app.email.templates.personalization_engine import PersonalizationData, personalization_engine

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Статусы A/B тестов"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MetricType(Enum):
    """Типы метрик для A/B тестирования"""
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    REPLY_RATE = "reply_rate"
    MEETING_BOOKED = "meeting_booked"
    CONVERSION_RATE = "conversion_rate"
    ENGAGEMENT_SCORE = "engagement_score"


@dataclass
class TestMetric:
    """Метрика A/B теста"""
    metric_type: MetricType
    variant_id: str
    value: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    p_value: float
    is_significant: bool
    measured_at: datetime


@dataclass
class ABTest:
    """A/B тест"""
    id: str
    name: str
    description: str
    template_types: List[TemplateType]
    variants: List[TemplateVariant]
    status: TestStatus
    traffic_allocation: Dict[str, float]  # variant_id -> percentage
    start_date: datetime
    end_date: Optional[datetime]
    min_sample_size: int
    confidence_level: float
    primary_metric: MetricType
    secondary_metrics: List[MetricType]
    target_audience: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    results: Dict[str, List[TestMetric]]


class ABTestingEngine:
    """
    Движок A/B тестирования для email шаблонов
    """
    
    def __init__(self):
        self.active_tests: Dict[str, ABTest] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.user_assignments: Dict[str, str] = {}  # user_id -> variant_id
        
        # Настройки тестирования
        self.default_confidence_level = 0.95
        self.default_min_sample_size = 100
        self.max_test_duration_days = 30
        
        # Статистические функции
        self.statistical_thresholds = {
            'high_confidence': 0.95,
            'medium_confidence': 0.90,
            'low_confidence': 0.80
        }
        
        logger.info("ABTestingEngine initialized")
    
    def create_ab_test(self, name: str, description: str, 
                      template_types: List[TemplateType],
                      variants: List[TemplateVariant],
                      primary_metric: MetricType = MetricType.REPLY_RATE,
                      secondary_metrics: Optional[List[MetricType]] = None,
                      traffic_allocation: Optional[Dict[str, float]] = None,
                      target_audience: Optional[Dict[str, Any]] = None) -> str:
        """
        Создание нового A/B теста
        """
        try:
            test_id = str(uuid.uuid4())
            
            # Проверяем валидность вариантов
            if len(variants) < 2:
                raise ValueError("A/B test must have at least 2 variants")
            
            # Проверяем распределение трафика
            if traffic_allocation is None:
                # Равномерное распределение
                traffic_per_variant = 1.0 / len(variants)
                traffic_allocation = {
                    variant.id: traffic_per_variant for variant in variants
                }
            
            # Проверяем, что сумма равна 1.0
            total_allocation = sum(traffic_allocation.values())
            if abs(total_allocation - 1.0) > 0.001:
                raise ValueError("Traffic allocation must sum to 1.0")
            
            # Создаем тест
            ab_test = ABTest(
                id=test_id,
                name=name,
                description=description,
                template_types=template_types,
                variants=variants,
                status=TestStatus.DRAFT,
                traffic_allocation=traffic_allocation,
                start_date=datetime.now(),
                end_date=None,
                min_sample_size=self.default_min_sample_size,
                confidence_level=self.default_confidence_level,
                primary_metric=primary_metric,
                secondary_metrics=secondary_metrics or [MetricType.OPEN_RATE, MetricType.CLICK_RATE],
                target_audience=target_audience or {},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                results={}
            )
            
            self.active_tests[test_id] = ab_test
            
            logger.info(f"Created A/B test {test_id}: {name}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    def start_test(self, test_id: str) -> bool:
        """Запуск A/B теста"""
        try:
            if test_id not in self.active_tests:
                raise ValueError(f"A/B test {test_id} not found")
            
            test = self.active_tests[test_id]
            
            if test.status != TestStatus.DRAFT:
                raise ValueError(f"Cannot start test in status {test.status}")
            
            # Устанавливаем дату окончания
            test.end_date = test.start_date + timedelta(days=self.max_test_duration_days)
            test.status = TestStatus.ACTIVE
            test.updated_at = datetime.now()
            
            logger.info(f"Started A/B test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting A/B test {test_id}: {e}")
            return False
    
    def pause_test(self, test_id: str) -> bool:
        """Приостановка A/B теста"""
        try:
            if test_id not in self.active_tests:
                raise ValueError(f"A/B test {test_id} not found")
            
            test = self.active_tests[test_id]
            
            if test.status != TestStatus.ACTIVE:
                raise ValueError(f"Cannot pause test in status {test.status}")
            
            test.status = TestStatus.PAUSED
            test.updated_at = datetime.now()
            
            logger.info(f"Paused A/B test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing A/B test {test_id}: {e}")
            return False
    
    def resume_test(self, test_id: str) -> bool:
        """Возобновление A/B теста"""
        try:
            if test_id not in self.active_tests:
                raise ValueError(f"A/B test {test_id} not found")
            
            test = self.active_tests[test_id]
            
            if test.status != TestStatus.PAUSED:
                raise ValueError(f"Cannot resume test in status {test.status}")
            
            test.status = TestStatus.ACTIVE
            test.updated_at = datetime.now()
            
            logger.info(f"Resumed A/B test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming A/B test {test_id}: {e}")
            return False
    
    def complete_test(self, test_id: str) -> bool:
        """Завершение A/B теста"""
        try:
            if test_id not in self.active_tests:
                raise ValueError(f"A/B test {test_id} not found")
            
            test = self.active_tests[test_id]
            
            if test.status not in [TestStatus.ACTIVE, TestStatus.PAUSED]:
                raise ValueError(f"Cannot complete test in status {test.status}")
            
            # Вычисляем финальные результаты
            final_results = self._calculate_final_results(test)
            self.test_results[test_id] = final_results
            
            test.status = TestStatus.COMPLETED
            test.updated_at = datetime.now()
            
            logger.info(f"Completed A/B test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing A/B test {test_id}: {e}")
            return False
    
    def assign_user_to_variant(self, user_id: str, test_id: str) -> Optional[str]:
        """
        Назначение пользователя к варианту A/B теста
        """
        try:
            if test_id not in self.active_tests:
                return None
            
            test = self.active_tests[test_id]
            
            if test.status != TestStatus.ACTIVE:
                return None
            
            # Проверяем, есть ли уже назначение
            assignment_key = f"{user_id}_{test_id}"
            if assignment_key in self.user_assignments:
                return self.user_assignments[assignment_key]
            
            # Проверяем соответствие целевой аудитории
            if not self._user_matches_target_audience(user_id, test.target_audience):
                return None
            
            # Назначаем вариант на основе распределения трафика
            variant_id = self._select_variant_by_traffic(test.traffic_allocation)
            
            # Сохраняем назначение
            self.user_assignments[assignment_key] = variant_id
            
            logger.debug(f"Assigned user {user_id} to variant {variant_id} in test {test_id}")
            return variant_id
            
        except Exception as e:
            logger.error(f"Error assigning user to variant: {e}")
            return None
    
    def record_metric(self, test_id: str, variant_id: str, 
                     metric_type: MetricType, value: float, sample_size: int) -> bool:
        """
        Запись метрики для варианта A/B теста
        """
        try:
            if test_id not in self.active_tests:
                return False
            
            test = self.active_tests[test_id]
            
            # Создаем метрику
            metric = TestMetric(
                metric_type=metric_type,
                variant_id=variant_id,
                value=value,
                sample_size=sample_size,
                confidence_interval=self._calculate_confidence_interval(value, sample_size),
                p_value=0.0,  # Будет вычислено позже
                is_significant=False,  # Будет вычислено позже
                measured_at=datetime.now()
            )
            
            # Добавляем к результатам теста
            if variant_id not in test.results:
                test.results[variant_id] = []
            
            test.results[variant_id].append(metric)
            
            logger.debug(f"Recorded metric {metric_type.value} for variant {variant_id}: {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
            return False
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Получение результатов A/B теста"""
        try:
            if test_id not in self.active_tests:
                return None
            
            test = self.active_tests[test_id]
            
            # Вычисляем текущие результаты
            current_results = self._calculate_current_results(test)
            
            return {
                'test_info': {
                    'id': test.id,
                    'name': test.name,
                    'description': test.description,
                    'status': test.status.value,
                    'start_date': test.start_date.isoformat(),
                    'end_date': test.end_date.isoformat() if test.end_date else None,
                    'primary_metric': test.primary_metric.value
                },
                'variants': [
                    {
                        'id': variant.id,
                        'name': variant.name,
                        'description': variant.description,
                        'traffic_allocation': test.traffic_allocation.get(variant.id, 0.0)
                    }
                    for variant in test.variants
                ],
                'results': current_results,
                'statistical_significance': self._calculate_statistical_significance(test),
                'recommendation': self._generate_recommendation(test, current_results)
            }
            
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return None
    
    def _select_variant_by_traffic(self, traffic_allocation: Dict[str, float]) -> str:
        """Выбор варианта на основе распределения трафика"""
        rand_value = random.random()
        cumulative_weight = 0.0
        
        for variant_id, weight in traffic_allocation.items():
            cumulative_weight += weight
            if rand_value <= cumulative_weight:
                return variant_id
        
        # Fallback к первому варианту
        return list(traffic_allocation.keys())[0]
    
    def _user_matches_target_audience(self, user_id: str, target_audience: Dict[str, Any]) -> bool:
        """Проверка соответствия пользователя целевой аудитории"""
        # В реальной реализации здесь будет проверка характеристик пользователя
        # Пока возвращаем True для демонстрации
        return True
    
    def _calculate_confidence_interval(self, value: float, sample_size: int) -> Tuple[float, float]:
        """Вычисление доверительного интервала"""
        # Упрощенное вычисление для демонстрации
        # В реальной реализации используется точная статистическая формула
        margin_of_error = 1.96 * (value * (1 - value) / sample_size) ** 0.5
        return (max(0, value - margin_of_error), min(1, value + margin_of_error))
    
    def _calculate_current_results(self, test: ABTest) -> Dict[str, Any]:
        """Вычисление текущих результатов теста"""
        results = {}
        
        for variant in test.variants:
            variant_id = variant.id
            variant_metrics = test.results.get(variant_id, [])
            
            # Вычисляем средние значения метрик
            metric_averages = {}
            for metric_type in [test.primary_metric] + test.secondary_metrics:
                relevant_metrics = [m for m in variant_metrics if m.metric_type == metric_type]
                if relevant_metrics:
                    avg_value = sum(m.value for m in relevant_metrics) / len(relevant_metrics)
                    total_sample_size = sum(m.sample_size for m in relevant_metrics)
                    metric_averages[metric_type.value] = {
                        'value': avg_value,
                        'sample_size': total_sample_size,
                        'confidence_interval': relevant_metrics[-1].confidence_interval
                    }
            
            results[variant_id] = {
                'name': variant.name,
                'description': variant.description,
                'metrics': metric_averages,
                'total_metrics': len(variant_metrics)
            }
        
        return results
    
    def _calculate_statistical_significance(self, test: ABTest) -> Dict[str, Any]:
        """Вычисление статистической значимости"""
        # Упрощенное вычисление для демонстрации
        significance_results = {}
        
        for variant in test.variants:
            variant_id = variant.id
            variant_metrics = test.results.get(variant_id, [])
            
            primary_metrics = [m for m in variant_metrics if m.metric_type == test.primary_metric]
            if len(primary_metrics) >= 2:
                # Простая проверка значимости
                latest_metric = primary_metrics[-1]
                significance_results[variant_id] = {
                    'p_value': 0.05,  # Демо значение
                    'is_significant': latest_metric.sample_size >= test.min_sample_size,
                    'confidence_level': test.confidence_level
                }
            else:
                significance_results[variant_id] = {
                    'p_value': 1.0,
                    'is_significant': False,
                    'confidence_level': test.confidence_level
                }
        
        return significance_results
    
    def _calculate_final_results(self, test: ABTest) -> Dict[str, Any]:
        """Вычисление финальных результатов теста"""
        current_results = self._calculate_current_results(test)
        significance = self._calculate_statistical_significance(test)
        
        # Определяем победителя
        winner = self._determine_winner(test, current_results, significance)
        
        return {
            'test_summary': {
                'total_duration': (test.updated_at - test.start_date).days,
                'total_variants': len(test.variants),
                'winner': winner,
                'statistical_power': self._calculate_statistical_power(test)
            },
            'results': current_results,
            'significance': significance,
            'recommendation': self._generate_recommendation(test, current_results)
        }
    
    def _determine_winner(self, test: ABTest, results: Dict[str, Any], 
                         significance: Dict[str, Any]) -> Optional[str]:
        """Определение победителя A/B теста"""
        primary_metric = test.primary_metric.value
        best_variant = None
        best_value = -1
        
        for variant_id, variant_results in results.items():
            if primary_metric in variant_results['metrics']:
                metric_value = variant_results['metrics'][primary_metric]['value']
                is_significant = significance.get(variant_id, {}).get('is_significant', False)
                
                if is_significant and metric_value > best_value:
                    best_value = metric_value
                    best_variant = variant_id
        
        return best_variant
    
    def _calculate_statistical_power(self, test: ABTest) -> float:
        """Вычисление статистической мощности теста"""
        # Упрощенное вычисление для демонстрации
        total_samples = sum(
            sum(m.sample_size for m in test.results.get(variant.id, []))
            for variant in test.variants
        )
        
        if total_samples >= test.min_sample_size * len(test.variants):
            return 0.8  # Хорошая статистическая мощность
        else:
            return 0.3  # Низкая статистическая мощность
    
    def _generate_recommendation(self, test: ABTest, results: Dict[str, Any]) -> str:
        """Генерация рекомендации по результатам теста"""
        primary_metric = test.primary_metric.value
        
        if not results:
            return "Test is still running. Continue collecting data."
        
        # Находим лучший вариант
        best_variant = None
        best_value = -1
        
        for variant_id, variant_results in results.items():
            if primary_metric in variant_results['metrics']:
                metric_value = variant_results['metrics'][primary_metric]['value']
                if metric_value > best_value:
                    best_value = metric_value
                    best_variant = variant_id
        
        if best_variant:
            variant_name = next(
                v.name for v in test.variants if v.id == best_variant
            )
            return f"Recommend implementing variant '{variant_name}' ({best_variant}) with {primary_metric} of {best_value:.2%}"
        else:
            return "No clear winner found. Consider running the test longer or adjusting variants."
    
    def get_all_tests(self) -> List[Dict[str, Any]]:
        """Получение всех A/B тестов"""
        tests = []
        
        for test in self.active_tests.values():
            tests.append({
                'id': test.id,
                'name': test.name,
                'description': test.description,
                'status': test.status.value,
                'template_types': [t.value for t in test.template_types],
                'variants_count': len(test.variants),
                'start_date': test.start_date.isoformat(),
                'end_date': test.end_date.isoformat() if test.end_date else None,
                'primary_metric': test.primary_metric.value
            })
        
        return tests


# Глобальный экземпляр движка A/B тестирования
ab_testing_engine = ABTestingEngine()
