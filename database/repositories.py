from typing import List, Optional, Dict, Any
from .database import DatabaseManager
from .models import User, UserCreate, Model, ModelCreate, ModelUpdate, InferenceRecord, InferenceRecordCreate, Task, TaskCreate, Alert, AlertCreate
from passlib.context import CryptContext
import json
from datetime import timedelta, datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        query = "SELECT * FROM users WHERE username = %s"
        result = self.db.execute_query(query, (username,), fetch='one')
        if not result:
            return None
        
        user_data = result
        # Temporarily disable password check for debugging
        # hashed_password = user_data.get('password_hash')

        # if not hashed_password or not self.verify_password(password, hashed_password):
        #     return None

        return User(**user_data)

    def create_user(self, user: UserCreate) -> User:
        hashed_password = pwd_context.hash(user.password)
        query = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        """
        self.db.execute_query(query, (user.username, user.email, hashed_password), commit=True)
        return self.get_user_by_username(user.username)

    def get_user_by_username(self, username: str) -> Optional[User]:
        query = "SELECT * FROM users WHERE username = %s"
        result = self.db.execute_query(query, (username,), fetch='one')
        return User(**result) if result else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        query = "SELECT * FROM users WHERE email = %s"
        result = self.db.execute_query(query, (email,), fetch='one')
        return User(**result) if result else None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

class ModelRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def _process_model_row(self, row: dict) -> dict:
        if row and 'labels' in row and row['labels'] is not None:
            if isinstance(row['labels'], str):
                try:
                    row['labels'] = json.loads(row['labels'])
                except json.JSONDecodeError:
                    row['labels'] = None
        return row

    def get_all_models(self, page: int = 1, page_size: int = 10, keyword: Optional[str] = None, status: Optional[str] = None, type: Optional[str] = None):
        offset = (page - 1) * page_size
        
        # Base queries
        query_base = "SELECT * FROM models"
        count_query_base = "SELECT COUNT(*) as total FROM models"
        
        # Conditions and parameters
        conditions = []
        params = []

        if keyword:
            conditions.append("(name LIKE %s OR description LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if type:
            conditions.append("type = %s")
            params.append(type)

        # Build final queries
        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"{query_base}{where_clause} ORDER BY upload_time DESC LIMIT %s OFFSET %s"
        count_query = f"{count_query_base}{where_clause}"
        
        # Execute queries
        paginated_params = tuple(params + [page_size, offset])
        count_params = tuple(params)
        
        result = self.db.execute_query(query, paginated_params, fetch='all')
        total_count_result = self.db.execute_query(count_query, count_params, fetch='one')
        
        # Process and return results
        processed_results = [self._process_model_row(row) for row in result]
        return {
            "items": [Model(**row) for row in processed_results],
            "total": total_count_result['total'] if total_count_result else 0,
            "page": page,
            "page_size": page_size
        }

    def get_model_by_id(self, model_id: int) -> Optional[Model]:
        query = "SELECT * FROM models WHERE id = %s"
        result = self.db.execute_query(query, (model_id,), fetch='one')
        if result:
            processed_result = self._process_model_row(result)
            return Model(**processed_result)
        return None

    def create_model(self, model: ModelCreate) -> Model:
        labels_json = json.dumps(model.labels) if model.labels else None
        query = "INSERT INTO models (name, version, description, type, file_path, labels) VALUES (%s, %s, %s, %s, %s, %s)"
        model_id = self.db.execute_query(query, (
            model.name,
            model.version,
            model.description,
            model.type,
            model.file_path,
            labels_json
        ), commit=True, last_row_id=True)
        return self.get_model_by_id(model_id)

    def update_model(self, model_id: int, model_update: ModelUpdate) -> Optional[Model]:
        """Updates a model's details."""
        labels_json = json.dumps(model_update.labels) if model_update.labels is not None else None
        
        # Build the update query dynamically to only update provided fields
        update_fields = []
        params = []
        
        if model_update.name is not None:
            update_fields.append("name = %s")
            params.append(model_update.name)
        if model_update.version is not None:
            update_fields.append("version = %s")
            params.append(model_update.version)
        if model_update.description is not None:
            update_fields.append("description = %s")
            params.append(model_update.description)
        if model_update.type is not None:
            update_fields.append("type = %s")
            params.append(model_update.type)
        if labels_json is not None:
            update_fields.append("labels = %s")
            params.append(labels_json)

        if not update_fields:
            return self.get_model_by_id(model_id) # Nothing to update

        query = f"UPDATE models SET {', '.join(update_fields)} WHERE id = %s"
        params.append(model_id)

        self.db.execute_query(query, tuple(params), commit=True)
        return self.get_model_by_id(model_id)

    def delete_model_by_id(self, model_id: int) -> bool:
        query = "DELETE FROM models WHERE id = %s"
        self.db.execute_query(query, (model_id,), commit=True)
        return True

    def update_model_status(self, model_id: int, status: str) -> bool:
        query = "UPDATE models SET status = %s WHERE id = %s"
        params = [status, model_id]
        self.db.execute_query(query, tuple(params), commit=True)
        return self.get_model_by_id(model_id)

    def get_total_count(self) -> int:
        """Gets the total number of models."""
        query = "SELECT COUNT(*) as total FROM models"
        result = self.db.execute_query(query, fetch='one')
        return result['total'] if result else 0

class TaskRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def _process_task_row(self, row: dict) -> dict:
        if row:
            if 'start_time' in row and row['start_time'] is not None:
                row['start_time'] = str(row['start_time'])
            if 'end_time' in row and row['end_time'] is not None:
                row['end_time'] = str(row['end_time'])
            if 'video_sources' in row and row['video_sources'] and isinstance(row['video_sources'], str):
                try:
                    row['video_sources'] = json.loads(row['video_sources'])
                except json.JSONDecodeError:
                    # Handle cases where the string is not valid JSON
                    row['video_sources'] = []
            if 'schedule_days' in row and row['schedule_days'] and isinstance(row['schedule_days'], str):
                try:
                    row['schedule_days'] = json.loads(row['schedule_days'])
                except json.JSONDecodeError:
                    row['schedule_days'] = []
        return row
        
    def get_all_tasks_for_scheduling(self) -> List[Task]:
        """
        Fetches all tasks from the database without pagination, intended for the scheduler.
        """
        query = "SELECT t.*, m.name as model_name FROM tasks t LEFT JOIN models m ON t.model_id = m.id"
        result = self.db.execute_query(query, fetch='all')
        processed_results = [self._process_task_row(row) for row in result]
        return [Task(**row) for row in processed_results]

    def get_all_tasks(self, page: int = 1, page_size: int = 10, keyword: Optional[str] = None, **kwargs) -> dict:
        # Get total count first
        count_query = "SELECT COUNT(*) as total FROM tasks t WHERE 1=1"
        count_params = []
        if keyword:
            count_query += " AND t.name LIKE %s"
            count_params.append(f"%{keyword}%")
        total_result = self.db.execute_query(count_query, tuple(count_params), fetch='one')
        total = total_result['total'] if total_result else 0

        # Get paginated items
        query = """
        SELECT t.*, m.name as model_name
        FROM tasks t
        LEFT JOIN models m ON t.model_id = m.id
        WHERE 1=1
        """
        params = []

        if keyword:
            query += " AND t.name LIKE %s"
            params.append(f"%{keyword}%")

        offset = (page - 1) * page_size
        query += " ORDER BY t.create_time DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        
        result = self.db.execute_query(query, tuple(params), fetch='all')
        
        processed_results = [self._process_task_row(row) for row in result]
        items = [Task(**row) for row in processed_results]
        return {"items": items, "total": total}

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        query = """
        SELECT t.*, m.name as model_name
        FROM tasks t
        LEFT JOIN models m ON t.model_id = m.id
        WHERE t.id = %s
        """
        result = self.db.execute_query(query, (task_id,), fetch='one')
        if not result:
            return None
        
        processed_row = self._process_task_row(result)
        return Task(**processed_row)

    def create_task(self, task: TaskCreate) -> Task:
        video_sources_json = json.dumps([dict(s) for s in task.video_sources])
        schedule_days_json = json.dumps(task.schedule_days) if task.schedule_days else None
        query = """
        INSERT INTO tasks (
            name, description, model_id, video_sources, 
            status, is_enabled, schedule_type, schedule_days, start_time, end_time,
            confidence_threshold, alert_debounce_interval, alert_message
        )
        VALUES (%s, %s, %s, %s, 'stopped', %s, %s, %s, %s, %s, %s, %s, %s)
        """
        task_id = self.db.execute_query(query, (
            task.name, task.description, task.model_id, video_sources_json,
            task.is_enabled, task.schedule_type.value, schedule_days_json,
            task.start_time, task.end_time,
            task.confidence_threshold, task.alert_debounce_interval, task.alert_message
        ), commit=True, last_row_id=True)
        return self.get_task_by_id(task_id)

    def update_task(self, task_id: int, task: TaskCreate) -> Optional[Task]:
        video_sources_json = json.dumps([dict(s) for s in task.video_sources])
        schedule_days_json = json.dumps(task.schedule_days) if task.schedule_days else None
        query = """
        UPDATE tasks
        SET 
            name = %s, 
            description = %s, 
            model_id = %s, 
            video_sources = %s,
            is_enabled = %s,
            schedule_type = %s,
            schedule_days = %s,
            start_time = %s,
            end_time = %s,
            confidence_threshold = %s,
            alert_debounce_interval = %s,
            alert_message = %s
        WHERE id = %s
        """
        self.db.execute_query(query, (
            task.name, task.description, task.model_id, video_sources_json,
            task.is_enabled, task.schedule_type.value, schedule_days_json,
            task.start_time, task.end_time,
            task.confidence_threshold, task.alert_debounce_interval, task.alert_message,
            task_id
        ), commit=True)
        return self.get_task_by_id(task_id)

    def update_task_status_and_enabled_state(self, task_id: int, status: str, is_enabled: bool) -> bool:
        """Updates both the status and the is_enabled flag of a task."""
        query = "UPDATE tasks SET status = %s, is_enabled = %s, update_time = NOW() WHERE id = %s"
        self.db.execute_query(query, (status, is_enabled, task_id), commit=True)
        return True

    def update_task_status(self, task_id: int, status: str) -> bool:
        query = "UPDATE tasks SET status = %s WHERE id = %s"
        self.db.execute_query(query, (status, task_id), commit=True)
        return True

    def update_task_enabled(self, task_id: int, is_enabled: bool) -> bool:
        query = "UPDATE tasks SET is_enabled = %s WHERE id = %s"
        self.db.execute_query(query, (is_enabled, task_id), commit=True)
        return True

    def delete_task(self, task_id: int) -> bool:
        # For simplicity, we are doing a hard delete here.
        # In a real-world scenario, you might want to soft-delete.
        query = "DELETE FROM tasks WHERE id = %s"
        self.db.execute_query(query, (task_id,), commit=True)
        return True

    def get_task_counts_by_status(self) -> Dict[str, int]:
        """Counts tasks grouped by their status."""
        query = "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
        result = self.db.execute_query(query, fetch='all')
        return {row['status']: row['count'] for row in result} if result else {}

    def get_total_count(self) -> int:
        """Gets the total number of tasks."""
        query = "SELECT COUNT(*) as total FROM tasks"
        result = self.db.execute_query(query, fetch='one')
        return result['total'] if result else 0

class AlertRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def _process_alert_row(self, row: dict) -> dict:
        """Helper to process a raw row from the alerts table."""
        if not row:
            return None
        # Pydantic will handle type conversions for most fields.
        # This is a good place to handle complex types like JSON if they existed.
        return row

    def create_alert(self, alert: AlertCreate) -> Alert:
        query = """
        INSERT INTO alerts (
            title, description, level, status, confidence, task_id, 
            task_name, model_name, alert_image, detection_class
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            alert_id = self.db.execute_query(query, (
                alert.title, alert.description, alert.level.value, alert.status.value,
                alert.confidence, alert.task_id, alert.task_name, alert.model_name,
                alert.alert_image, alert.detection_class
            ), fetch=None, commit=True, last_row_id=True)

            if alert_id:
                # Construct the full Alert object to return
                alert_data = alert.model_dump()
                alert_data['id'] = alert_id
                alert_data['created_at'] = datetime.now()
                alert_data['updated_at'] = datetime.now()
                return Alert(**alert_data)
            else:
                return None
        except Exception as e:
            # It's a good practice to log the exception
            print(f"Database error on alert creation: {e}")
            return None

    def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        query = "SELECT * FROM alerts WHERE id = %s"
        result = self.db.execute_query(query, (alert_id,), fetch='one')
        return Alert(**result) if result else None

    def get_latest_alert_for_task(self, task_id: int, detection_class: str) -> Optional[Alert]:
        query = """
        SELECT * FROM alerts 
        WHERE task_id = %s AND detection_class = %s 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        result = self.db.execute_query(query, (task_id, detection_class), fetch='one')
        return Alert(**self._process_alert_row(result)) if result else None

    def get_all_alerts(self, page: int = 1, page_size: int = 10, keyword: Optional[str] = None, level: Optional[str] = None, status: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        """
        Retrieves a paginated list of alerts with optional filters.
        """
        count_query_base = "SELECT COUNT(*) as total FROM alerts"
        query_base = "SELECT * FROM alerts"
        
        where_clauses = []
        params = []

        if keyword:
            where_clauses.append("(title LIKE %s OR description LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if level:
            where_clauses.append("level = %s")
            params.append(level)
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        if start_date:
            where_clauses.append("created_at >= %s")
            params.append(start_date)
        if end_date:
            # Add 1 day to end_date to include the whole day
            where_clauses.append("created_at < DATE_ADD(%s, INTERVAL 1 DAY)")
            params.append(end_date)
            
        if where_clauses:
            query_conditions = " WHERE " + " AND ".join(where_clauses)
            count_query = count_query_base + query_conditions
            query = query_base + query_conditions
        else:
            count_query = count_query_base
            query = query_base
            
        total_result = self.db.execute_query(count_query, tuple(params), fetch='one')
        total = total_result['total'] if total_result else 0
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * page_size
        params.extend([page_size, offset])
        
        result = self.db.execute_query(query, tuple(params), fetch='all')
        items = [Alert(**row) for row in result]
        return {"items": items, "total": total}

    def update_alert_status(self, alert_id: int, status: str, remark: Optional[str] = None) -> Optional[Alert]:
        # This is a simplified update. A real implementation might involve logging the change.
        query = "UPDATE alerts SET status = %s WHERE id = %s"
        params = [status, alert_id]
        self.db.execute_query(query, tuple(params), commit=True)
        return self.get_alert_by_id(alert_id)

    def get_alert_counts_by_status(self) -> Dict[str, int]:
        """Counts alerts grouped by their status."""
        query = "SELECT status, COUNT(*) as count FROM alerts GROUP BY status"
        result = self.db.execute_query(query, fetch='all')
        return {row['status']: row['count'] for row in result} if result else {}

    def get_alert_counts_by_day(self, days: int = 7) -> List[Dict[str, Any]]:
        """Counts alerts per day for the last N days."""
        end_date = datetime.utcnow().date() + timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM alerts
        WHERE created_at >= %s AND created_at < %s
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        params = [start_date, end_date]
        
        db_results = self.db.execute_query(query, tuple(params), fetch='all')
        
        # Create a dictionary for quick lookup
        data_map = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in db_results} if db_results else {}
        
        # Generate the full list of dates
        date_list = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
        
        return [{'date': d, 'count': data_map.get(d, 0)} for d in date_list]

    def get_latest_alerts(self, limit: int = 5) -> List[Alert]:
        """Gets the most recent alerts."""
        query = "SELECT * FROM alerts ORDER BY created_at DESC LIMIT %s"
        params = [limit]
        result = self.db.execute_query(query, tuple(params), fetch='all')
        return [Alert(**row) for row in result] if result else []

class InferenceRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def create_record(self, record: InferenceRecordCreate) -> InferenceRecord:
        query = """
        INSERT INTO inference_records 
        (model_id, user_id, input_path, output_path, inference_time, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (
            record.model_id,
            record.user_id,
            record.input_path,
            record.output_path,
            record.inference_time,
            record.status
        ), commit=True)
        return self.get_latest_record(record.user_id)

    def get_latest_record(self, user_id: int) -> Optional[InferenceRecord]:
        query = """
        SELECT * FROM inference_records 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        result = self.db.execute_query(query, (user_id,), fetch='one')
        return InferenceRecord(**result) if result else None

    def get_user_records(self, user_id: int) -> List[InferenceRecord]:
        query = "SELECT * FROM inference_records WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,), fetch='all')
        return [InferenceRecord(**row) for row in result] 