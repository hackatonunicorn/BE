"""
VC Fund Data Importer - Import and validation of venture capital fund data
"""
import os
import csv
import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.data.models import VCFund, Communication
from app.data.repositories import vc_fund_repository

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Результат импорта"""
    total_records: int
    successful_imports: int
    failed_imports: int
    duplicates_found: int
    duplicates_merged: int
    validation_errors: List[Dict[str, Any]]
    import_id: str
    started_at: datetime
    completed_at: datetime
    file_path: str
    backup_path: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ValidationError:
    """Ошибка валидации"""
    row_number: int
    field: str
    value: Any
    error_message: str
    severity: str = "error"  # error, warning, info


class VCFundDataValidator:
    """Валидатор данных VC фондов"""
    
    REQUIRED_FIELDS = ["name", "focus_industries", "investment_stages", "geography", "email"]
    VALID_INDUSTRIES = [
        "Technology", "Healthcare", "Fintech", "E-commerce", "AI/ML", 
        "Biotech", "CleanTech", "EdTech", "Gaming", "SaaS", "B2B", "B2C"
    ]
    VALID_STAGES = [
        "Pre-Seed", "Seed", "Series A", "Series B", "Series C", 
        "Series D", "Growth", "Late Stage"
    ]
    VALID_GEOGRAPHIES = [
        "North America", "Europe", "Asia", "Latin America", "Africa", 
        "Global", "United States", "United Kingdom", "Germany", "France"
    ]
    
    def validate_fund_data(self, fund_dict: Dict[str, Any], row_number: int = 0) -> List[ValidationError]:
        """Валидация данных фонда"""
        errors = []
        
        # Проверка обязательных полей
        for field in self.REQUIRED_FIELDS:
            if not fund_dict.get(field):
                errors.append(ValidationError(
                    row_number=row_number,
                    field=field,
                    value=fund_dict.get(field),
                    error_message=f"Required field '{field}' is missing or empty"
                ))
        
        # Валидация названия фонда
        name = fund_dict.get("name", "").strip()
        if name and len(name) < 2:
            errors.append(ValidationError(
                row_number=row_number,
                field="name",
                value=name,
                error_message="Fund name must be at least 2 characters long"
            ))
        
        # Валидация email
        email = fund_dict.get("email", "").strip()
        if email and "@" not in email:
            errors.append(ValidationError(
                row_number=row_number,
                field="email",
                value=email,
                error_message="Invalid email format"
            ))
        
        # Валидация отраслей
        industries = fund_dict.get("focus_industries", [])
        if isinstance(industries, str):
            industries = [i.strip() for i in industries.split(",")]
        
        for industry in industries:
            if industry and industry not in self.VALID_INDUSTRIES:
                errors.append(ValidationError(
                    row_number=row_number,
                    field="focus_industries",
                    value=industry,
                    error_message=f"Invalid industry: '{industry}'. Valid options: {', '.join(self.VALID_INDUSTRIES)}",
                    severity="warning"
                ))
        
        # Валидация стадий инвестирования
        stages = fund_dict.get("investment_stages", [])
        if isinstance(stages, str):
            stages = [s.strip() for s in stages.split(",")]
        
        for stage in stages:
            if stage and stage not in self.VALID_STAGES:
                errors.append(ValidationError(
                    row_number=row_number,
                    field="investment_stages",
                    value=stage,
                    error_message=f"Invalid investment stage: '{stage}'. Valid options: {', '.join(self.VALID_STAGES)}",
                    severity="warning"
                ))
        
        # Валидация географии
        geography = fund_dict.get("geography", "").strip()
        if geography and geography not in self.VALID_GEOGRAPHIES:
            errors.append(ValidationError(
                row_number=row_number,
                field="geography",
                value=geography,
                error_message=f"Invalid geography: '{geography}'. Valid options: {', '.join(self.VALID_GEOGRAPHIES)}",
                severity="warning"
            ))
        
        # Валидация размера инвестиций
        ticket_size_min = fund_dict.get("ticket_size_min")
        ticket_size_max = fund_dict.get("ticket_size_max")
        
        if ticket_size_min is not None:
            try:
                min_val = float(ticket_size_min)
                if min_val < 0:
                    errors.append(ValidationError(
                        row_number=row_number,
                        field="ticket_size_min",
                        value=ticket_size_min,
                        error_message="Minimum ticket size cannot be negative"
                    ))
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    row_number=row_number,
                    field="ticket_size_min",
                    value=ticket_size_min,
                    error_message="Invalid minimum ticket size format"
                ))
        
        if ticket_size_max is not None:
            try:
                max_val = float(ticket_size_max)
                if max_val < 0:
                    errors.append(ValidationError(
                        row_number=row_number,
                        field="ticket_size_max",
                        value=ticket_size_max,
                        error_message="Maximum ticket size cannot be negative"
                    ))
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    row_number=row_number,
                    field="ticket_size_max",
                    value=ticket_size_max,
                    error_message="Invalid maximum ticket size format"
                ))
        
        # Проверка логики размеров инвестиций
        if ticket_size_min is not None and ticket_size_max is not None:
            try:
                min_val = float(ticket_size_min)
                max_val = float(ticket_size_max)
                if min_val > max_val:
                    errors.append(ValidationError(
                        row_number=row_number,
                        field="ticket_size_min",
                        value=ticket_size_min,
                        error_message="Minimum ticket size cannot be greater than maximum ticket size"
                    ))
            except (ValueError, TypeError):
                pass
        
        return errors


class DuplicateDetector:
    """Детектор дубликатов фондов"""
    
    def find_duplicates(self, fund_data: Dict[str, Any], existing_funds: List[VCFund]) -> List[Tuple[VCFund, float]]:
        """Поиск потенциальных дубликатов"""
        duplicates = []
        fund_name = fund_data.get("name", "").strip().lower()
        fund_email = fund_data.get("email", "").strip().lower()
        
        for existing_fund in existing_funds:
            similarity_score = self._calculate_similarity(fund_data, existing_fund)
            
            # Порог схожести для дубликатов
            if similarity_score >= 0.8:
                duplicates.append((existing_fund, similarity_score))
        
        # Сортируем по убыванию схожести
        duplicates.sort(key=lambda x: x[1], reverse=True)
        return duplicates
    
    def _calculate_similarity(self, fund_data: Dict[str, Any], existing_fund: VCFund) -> float:
        """Вычисление схожести между фондами"""
        score = 0.0
        weight_sum = 0.0
        
        # Сравнение названий (вес 40%)
        name_weight = 0.4
        name_similarity = self._name_similarity(
            fund_data.get("name", "").strip().lower(),
            existing_fund.name.strip().lower()
        )
        score += name_similarity * name_weight
        weight_sum += name_weight
        
        # Сравнение email (вес 30%)
        email_weight = 0.3
        if fund_data.get("email") and existing_fund.email:
            email_similarity = 1.0 if fund_data.get("email").strip().lower() == existing_fund.email.strip().lower() else 0.0
        else:
            email_similarity = 0.0
        score += email_similarity * email_weight
        weight_sum += email_weight
        
        # Сравнение географии (вес 20%)
        geography_weight = 0.2
        if fund_data.get("geography") and existing_fund.geography:
            geography_similarity = 1.0 if fund_data.get("geography").strip().lower() == existing_fund.geography.strip().lower() else 0.0
        else:
            geography_similarity = 0.0
        score += geography_similarity * geography_weight
        weight_sum += geography_weight
        
        # Сравнение отраслей (вес 10%)
        industries_weight = 0.1
        fund_industries = set()
        if fund_data.get("focus_industries"):
            if isinstance(fund_data["focus_industries"], str):
                fund_industries = set(i.strip().lower() for i in fund_data["focus_industries"].split(","))
            elif isinstance(fund_data["focus_industries"], list):
                fund_industries = set(i.strip().lower() for i in fund_data["focus_industries"])
        
        existing_industries = set()
        if existing_fund.focus_industries:
            existing_industries = set(i.strip().lower() for i in existing_fund.focus_industries)
        
        if fund_industries and existing_industries:
            intersection = len(fund_industries.intersection(existing_industries))
            union = len(fund_industries.union(existing_industries))
            industries_similarity = intersection / union if union > 0 else 0.0
        else:
            industries_similarity = 0.0
        
        score += industries_similarity * industries_weight
        weight_sum += industries_weight
        
        return score / weight_sum if weight_sum > 0 else 0.0
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Вычисление схожести названий"""
        if not name1 or not name2:
            return 0.0
        
        # Точное совпадение
        if name1 == name2:
            return 1.0
        
        # Проверка на подстроки
        if name1 in name2 or name2 in name1:
            return 0.9
        
        # Простая проверка на общие слова
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return intersection / union if union > 0 else 0.0
        
        return 0.0


class VCFundImporter:
    """Импортер данных VC фондов"""
    
    def __init__(self):
        self.validator = VCFundDataValidator()
        self.duplicate_detector = DuplicateDetector()
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def import_vc_funds(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ImportResult:
        """
        Импорт VC фондов из файла
        
        Args:
            file_path: Путь к файлу для импорта
            options: Дополнительные опции импорта
        
        Returns:
            ImportResult: Результат импорта
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        import_id = str(uuid.uuid4())
        started_at = datetime.now()
        
        logger.info(f"Starting VC fund import from {file_path}, import ID: {import_id}")
        
        # Создаем backup базы данных
        backup_path = self._create_backup()
        
        # Читаем данные из файла
        try:
            fund_data_list = self._read_file(file_path)
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return ImportResult(
                total_records=0,
                successful_imports=0,
                failed_imports=0,
                duplicates_found=0,
                duplicates_merged=0,
                validation_errors=[{"error": str(e), "row": 0}],
                import_id=import_id,
                started_at=started_at,
                completed_at=datetime.now(),
                file_path=file_path,
                backup_path=backup_path
            )
        
        total_records = len(fund_data_list)
        successful_imports = 0
        failed_imports = 0
        duplicates_found = 0
        duplicates_merged = 0
        validation_errors = []
        
        # Получаем существующие фонды для проверки дубликатов
        db = next(get_db())
        existing_funds = db.query(VCFund).all()
        
        for row_number, fund_data in enumerate(fund_data_list, 1):
            try:
                # Валидация данных
                validation_errors_for_row = self.validator.validate_fund_data(fund_data, row_number)
                
                # Проверяем критические ошибки
                critical_errors = [e for e in validation_errors_for_row if e.severity == "error"]
                if critical_errors:
                    validation_errors.extend([{
                        "row": row_number,
                        "field": e.field,
                        "value": e.value,
                        "error": e.error_message,
                        "severity": e.severity
                    } for e in critical_errors])
                    failed_imports += 1
                    continue
                
                # Добавляем предупреждения
                warnings = [e for e in validation_errors_for_row if e.severity == "warning"]
                validation_errors.extend([{
                    "row": row_number,
                    "field": e.field,
                    "value": e.value,
                    "error": e.error_message,
                    "severity": e.severity
                } for e in warnings])
                
                # Проверка дубликатов
                duplicates = self.duplicate_detector.find_duplicates(fund_data, existing_funds)
                
                if duplicates:
                    duplicates_found += 1
                    
                    # Опция автоматического слияния
                    if options and options.get("auto_merge_duplicates"):
                        best_match = duplicates[0][0]
                        self._merge_fund_data(fund_data, best_match, db)
                        duplicates_merged += 1
                        successful_imports += 1
                    else:
                        # Пропускаем дубликат
                        validation_errors.append({
                            "row": row_number,
                            "field": "duplicate",
                            "value": fund_data.get("name"),
                            "error": f"Duplicate found: {duplicates[0][0].name} (similarity: {duplicates[0][1]:.2f})",
                            "severity": "warning"
                        })
                        failed_imports += 1
                else:
                    # Создаем новый фонд
                    new_fund = self._create_fund_from_data(fund_data)
                    db.add(new_fund)
                    db.commit()
                    successful_imports += 1
                    
                    # Добавляем в список существующих фондов для следующих итераций
                    existing_funds.append(new_fund)
                
            except Exception as e:
                logger.error(f"Error processing row {row_number}: {e}")
                validation_errors.append({
                    "row": row_number,
                    "field": "general",
                    "value": str(fund_data),
                    "error": f"Processing error: {str(e)}",
                    "severity": "error"
                })
                failed_imports += 1
        
        completed_at = datetime.now()
        
        result = ImportResult(
            total_records=total_records,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            duplicates_found=duplicates_found,
            duplicates_merged=duplicates_merged,
            validation_errors=validation_errors,
            import_id=import_id,
            started_at=started_at,
            completed_at=completed_at,
            file_path=file_path,
            backup_path=backup_path
        )
        
        logger.info(f"Import completed: {successful_imports}/{total_records} successful, {failed_imports} failed, {duplicates_found} duplicates found")
        
        return result
    
    def _read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Чтение данных из файла"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            return self._read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self._read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _read_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Чтение CSV файла"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Очищаем и нормализуем данные
                cleaned_row = {}
                for key, value in row.items():
                    if value is not None:
                        cleaned_row[key.strip()] = value.strip()
                    else:
                        cleaned_row[key.strip()] = ""
                data.append(cleaned_row)
        return data
    
    def _read_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """Чтение Excel файла"""
        df = pd.read_excel(file_path)
        
        # Преобразуем NaN в None
        df = df.where(pd.notnull(df), None)
        
        # Преобразуем в список словарей
        data = df.to_dict('records')
        
        # Очищаем данные
        for row in data:
            for key, value in row.items():
                if value is not None:
                    row[key] = str(value).strip()
                else:
                    row[key] = ""
        
        return data
    
    def _create_backup(self) -> Optional[str]:
        """Создание backup базы данных"""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"vc_funds_backup_{timestamp}.json"
            
            # Экспортируем текущие данные
            db = next(get_db())
            funds = db.query(VCFund).all()
            
            backup_data = []
            for fund in funds:
                backup_data.append({
                    "id": fund.id,
                    "name": fund.name,
                    "focus_industries": fund.focus_industries,
                    "investment_stages": fund.investment_stages,
                    "geography": fund.geography,
                    "ticket_size_min": fund.ticket_size_min,
                    "ticket_size_max": fund.ticket_size_max,
                    "email": fund.email,
                    "contact_info": fund.contact_info,
                    "matching_criteria": fund.matching_criteria,
                    "created_at": fund.created_at.isoformat() if fund.created_at else None,
                    "updated_at": fund.updated_at.isoformat() if fund.updated_at else None
                })
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _create_fund_from_data(self, fund_data: Dict[str, Any]) -> VCFund:
        """Создание объекта VCFund из данных"""
        # Обработка отраслей
        focus_industries = fund_data.get("focus_industries", [])
        if isinstance(focus_industries, str):
            focus_industries = [i.strip() for i in focus_industries.split(",") if i.strip()]
        
        # Обработка стадий инвестирования
        investment_stages = fund_data.get("investment_stages", [])
        if isinstance(investment_stages, str):
            investment_stages = [s.strip() for s in investment_stages.split(",") if s.strip()]
        
        # Обработка размеров инвестиций
        ticket_size_min = fund_data.get("ticket_size_min")
        if ticket_size_min is not None:
            try:
                ticket_size_min = float(ticket_size_min)
            except (ValueError, TypeError):
                ticket_size_min = None
        
        ticket_size_max = fund_data.get("ticket_size_max")
        if ticket_size_max is not None:
            try:
                ticket_size_max = float(ticket_size_max)
            except (ValueError, TypeError):
                ticket_size_max = None
        
        # Обработка контактной информации
        contact_info = {}
        if fund_data.get("contact_person"):
            contact_info["contact_person"] = fund_data["contact_person"]
        if fund_data.get("phone"):
            contact_info["phone"] = fund_data["phone"]
        if fund_data.get("website"):
            contact_info["website"] = fund_data["website"]
        
        return VCFund(
            name=fund_data.get("name", "").strip(),
            focus_industries=focus_industries,
            investment_stages=investment_stages,
            geography=fund_data.get("geography", "").strip(),
            ticket_size_min=ticket_size_min,
            ticket_size_max=ticket_size_max,
            email=fund_data.get("email", "").strip(),
            contact_info=contact_info if contact_info else None,
            matching_criteria=None
        )
    
    def _merge_fund_data(self, new_data: Dict[str, Any], existing_fund: VCFund, db: Session):
        """Слияние данных нового фонда с существующим"""
        # Обновляем поля, если новые данные более полные
        if new_data.get("description") and not existing_fund.contact_info.get("description"):
            if not existing_fund.contact_info:
                existing_fund.contact_info = {}
            existing_fund.contact_info["description"] = new_data["description"]
        
        # Обновляем контактную информацию
        if new_data.get("phone") and not existing_fund.contact_info.get("phone"):
            if not existing_fund.contact_info:
                existing_fund.contact_info = {}
            existing_fund.contact_info["phone"] = new_data["phone"]
        
        if new_data.get("website") and not existing_fund.contact_info.get("website"):
            if not existing_fund.contact_info:
                existing_fund.contact_info = {}
            existing_fund.contact_info["website"] = new_data["website"]
        
        # Обновляем размеры инвестиций, если они не заданы
        if existing_fund.ticket_size_min is None and new_data.get("ticket_size_min"):
            try:
                existing_fund.ticket_size_min = float(new_data["ticket_size_min"])
            except (ValueError, TypeError):
                pass
        
        if existing_fund.ticket_size_max is None and new_data.get("ticket_size_max"):
            try:
                existing_fund.ticket_size_max = float(new_data["ticket_size_max"])
            except (ValueError, TypeError):
                pass
        
        existing_fund.updated_at = datetime.now()
        db.commit()
    
    def validate_fund_data(self, fund_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Валидация данных фонда"""
        errors = self.validator.validate_fund_data(fund_dict)
        return [{
            "field": e.field,
            "value": e.value,
            "error": e.error_message,
            "severity": e.severity
        } for e in errors]
    
    def merge_duplicate_funds(self, fund1_id: int, fund2_id: int, keep_fund_id: int) -> Dict[str, Any]:
        """Слияние дубликатов фондов"""
        try:
            db = next(get_db())
            
            fund1 = db.query(VCFund).filter(VCFund.id == fund1_id).first()
            fund2 = db.query(VCFund).filter(VCFund.id == fund2_id).first()
            
            if not fund1 or not fund2:
                return {"success": False, "error": "One or both funds not found"}
            
            # Определяем какой фонд оставляем
            if keep_fund_id == fund1_id:
                keep_fund = fund1
                merge_fund = fund2
            else:
                keep_fund = fund2
                merge_fund = fund1
            
            # Перемещаем коммуникации
            communications = db.query(Communication).filter(Communication.vc_fund_id == merge_fund.id).all()
            for comm in communications:
                comm.vc_fund_id = keep_fund.id
            
            # Удаляем дублирующий фонд
            db.delete(merge_fund)
            db.commit()
            
            return {
                "success": True,
                "message": f"Funds merged successfully. Kept fund {keep_fund.id}, merged fund {merge_fund.id}",
                "communications_moved": len(communications)
            }
            
        except Exception as e:
            logger.error(f"Error merging funds: {e}")
            return {"success": False, "error": str(e)}
    
    def export_data(self, entity_type: str, format: str = "csv") -> str:
        """Экспорт данных"""
        try:
            db = next(get_db())
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if entity_type == "vc_funds":
                entities = db.query(VCFund).all()
                filename = f"vc_funds_export_{timestamp}.{format}"
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
            
            file_path = export_dir / filename
            
            if format == "csv":
                self._export_to_csv(entities, file_path)
            elif format == "json":
                self._export_to_json(entities, file_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise
    
    def _export_to_csv(self, entities: List[VCFund], file_path: Path):
        """Экспорт в CSV"""
        if not entities:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'name', 'focus_industries', 'investment_stages', 'geography',
                'ticket_size_min', 'ticket_size_max', 'email', 'created_at', 'updated_at'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for fund in entities:
                writer.writerow({
                    'id': fund.id,
                    'name': fund.name,
                    'focus_industries': ','.join(fund.focus_industries) if fund.focus_industries else '',
                    'investment_stages': ','.join(fund.investment_stages) if fund.investment_stages else '',
                    'geography': fund.geography,
                    'ticket_size_min': fund.ticket_size_min,
                    'ticket_size_max': fund.ticket_size_max,
                    'email': fund.email,
                    'created_at': fund.created_at.isoformat() if fund.created_at else '',
                    'updated_at': fund.updated_at.isoformat() if fund.updated_at else ''
                })
    
    def _export_to_json(self, entities: List[VCFund], file_path: Path):
        """Экспорт в JSON"""
        data = []
        for fund in entities:
            data.append({
                'id': fund.id,
                'name': fund.name,
                'focus_industries': fund.focus_industries,
                'investment_stages': fund.investment_stages,
                'geography': fund.geography,
                'ticket_size_min': fund.ticket_size_min,
                'ticket_size_max': fund.ticket_size_max,
                'email': fund.email,
                'contact_info': fund.contact_info,
                'matching_criteria': fund.matching_criteria,
                'created_at': fund.created_at.isoformat() if fund.created_at else None,
                'updated_at': fund.updated_at.isoformat() if fund.updated_at else None
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Глобальный экземпляр импортера
vc_fund_importer = VCFundImporter()
