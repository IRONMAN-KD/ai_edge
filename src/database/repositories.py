from typing import List, Optional, Dict, Any
from .database import DatabaseManager
from .models import User, UserCreate, Model, ModelCreate, ModelUpdate, InferenceRecord, InferenceRecordCreate, Task, TaskCreate, Alert, AlertCreate
from database.schema import Task as TaskDB, Model as ModelDB
from passlib.context import CryptContext
import json
from datetime import timedelta, datetime
import os
from sqlalchemy.orm import joinedload
from sqlalchemy import func, exc

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

    def get_user_by_token(self, token: str) -> Optional[User]:
        """通过令牌获取用户
        
        Args:
            token: 用户令牌
            
        Returns:
            User: 用户对象，如果未找到则返回None
        """
        # 简单实现：假设token就是用户名，实际应用中应该解析JWT或其他令牌格式
        try:
            # 解析token，提取用户名或ID
            # 这里简化处理，假设token格式为"username:timestamp"
            if ':' in token:
                username = token.split(':')[0]
                return self.get_user_by_username(username)
            else:
                # 尝试直接用token作为用户名查询
                return self.get_user_by_username(token)
        except Exception as e:
            print(f"解析token失败: {e}")
            return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

class ModelRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def _process_model_row(self, row: dict) -> dict:
        if not row:
            return row
            
        # 处理labels字段
        if 'labels' in row and row['labels'] is not None:
            if isinstance(row['labels'], str):
                try:
                    row['labels'] = json.loads(row['labels'])
                except json.JSONDecodeError:
                    row['labels'] = None
        
        # 映射数据库字段到Model类字段
        if 'upload_time' not in row and 'created_at' in row:
            row['upload_time'] = row['created_at']
            
        if 'update_time' not in row and 'updated_at' in row:
            row['update_time'] = row['updated_at']
            
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
            # 直接使用status字段
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
        import os
        
        # 计算文件大小
        file_size = 0
        if model.file_path and os.path.exists(model.file_path):
            file_size = os.path.getsize(model.file_path)
        
        # 处理标签
        labels_json = json.dumps(model.labels) if model.labels else None
        
        query = """
        INSERT INTO models (name, version, type, file_path, file_size, input_size, 
                           confidence_threshold, nms_threshold, classes, description, 
                           status, labels) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        model_id = self.db.execute_query(query, (
            model.name,
            model.version,
            model.type,
            model.file_path,
            file_size,
            '640x640',  # 默认输入尺寸
            0.5,        # 默认置信度阈值
            0.4,        # 默认NMS阈值
            labels_json,  # classes字段
            model.description,
            'active',   # 默认状态
            labels_json  # labels字段
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
        # 直接使用status字段
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

    def get_task_by_id(self, task_id: int) -> Optional[TaskDB]:
        with self.db.get_session() as session:
            task = session.query(TaskDB).options(joinedload(TaskDB.model)).filter(TaskDB.id == task_id).first()
            
            if not task:
                return None
            
            # Create a new detached Task object with all data loaded
            new_task = TaskDB()
            
            # Copy all basic attributes
            for column in TaskDB.__table__.columns:
                setattr(new_task, column.name, getattr(task, column.name))
            
            # Handle the model relationship
            if task.model:
                new_model = type(task.model)()  # Create new Model instance
                for column in task.model.__table__.columns:
                    setattr(new_model, column.name, getattr(task.model, column.name))
                new_task.model = new_model
            
            return new_task

    def get_all_tasks_for_scheduling(self) -> List[TaskDB]:
        with self.db.get_session() as session:
            return session.query(TaskDB).options(joinedload(TaskDB.model)).all()

    def get_all_tasks(self, page: int = 1, page_size: int = 10, keyword: Optional[str] = None, 
                     status: Optional[str] = None, model_id: Optional[int] = None, 
                     is_enabled: Optional[bool] = None) -> dict:
        with self.db.get_session() as session:
            # Base query
            query = session.query(TaskDB)

            # Apply filters
            if keyword:
                query = query.filter(TaskDB.name.like(f"%{keyword}%"))
            
            if status:
                query = query.filter(TaskDB.status == status)
            
            if model_id:
                query = query.filter(TaskDB.model_id == model_id)
            
            if is_enabled is not None:
                query = query.filter(TaskDB.is_enabled == is_enabled)

            # Efficiently count the total number of items
            try:
                count_query = query.with_entities(func.count(TaskDB.id))
                total = count_query.scalar()
            except exc.SQLAlchemyError:
                total = query.count()

            # Eagerly load the related model for the paginated query
            offset = (page - 1) * page_size
            tasks = query.options(joinedload(TaskDB.model)).order_by(TaskDB.create_time.desc()).offset(offset).limit(page_size).all()
            
            # Create new detached Task objects with all data loaded
            task_list = []
            for task in tasks:
                # Create a new Task object with all attributes manually copied
                new_task = TaskDB()
                
                # Copy all basic attributes
                for column in TaskDB.__table__.columns:
                    setattr(new_task, column.name, getattr(task, column.name))
                
                # Handle the model relationship
                if task.model:
                    new_model = type(task.model)()  # Create new Model instance
                    for column in task.model.__table__.columns:
                        setattr(new_model, column.name, getattr(task.model, column.name))
                    new_task.model = new_model
                
                task_list.append(new_task)
            
            return {"items": task_list, "total": total, "page": page, "page_size": page_size}

    def create_task(self, task: TaskCreate) -> TaskDB:
        with self.db.get_session() as session:
            db_task = TaskDB(
                **task.model_dump(exclude={"video_sources", "schedule_days"}),
                video_sources=json.dumps(task.video_sources),
                schedule_days=json.dumps(task.schedule_days)
            )
            session.add(db_task)
            session.commit()
            session.refresh(db_task)
            
            # Get the task with model relationship loaded before session closes
            task_with_model = session.query(TaskDB).options(
                joinedload(TaskDB.model)
            ).filter(TaskDB.id == db_task.id).first()
            
            # Create a new detached Task object with all data loaded
            new_task = TaskDB()
            
            # Copy all basic attributes
            for column in TaskDB.__table__.columns:
                setattr(new_task, column.name, getattr(task_with_model, column.name))
            
            # Handle the model relationship
            if task_with_model.model:
                new_model = type(task_with_model.model)()  # Create new Model instance
                for column in task_with_model.model.__table__.columns:
                    setattr(new_model, column.name, getattr(task_with_model.model, column.name))
                new_task.model = new_model
            
            return new_task

    def update_task(self, task_id: int, task: TaskCreate) -> Optional[TaskDB]:
        with self.db.get_session() as session:
            db_task = session.get(TaskDB, task_id)
            if not db_task:
                return None

            update_data = task.model_dump(exclude_unset=True)

            db_task.end_time = update_data.pop('end_time', db_task.end_time)

            for key, value in update_data.items():
                setattr(db_task, key, value)
            
            session.commit()

            # Query the fresh instance with the relationship loaded
            updated_task = session.query(TaskDB).options(
                joinedload(TaskDB.model)
            ).filter(TaskDB.id == task_id).first()
            
            # Create a new detached Task object with all data loaded
            new_task = TaskDB()
            
            # Copy all basic attributes
            for column in TaskDB.__table__.columns:
                setattr(new_task, column.name, getattr(updated_task, column.name))
            
            # Handle the model relationship
            if updated_task.model:
                new_model = type(updated_task.model)()  # Create new Model instance
                for column in updated_task.model.__table__.columns:
                    setattr(new_model, column.name, getattr(updated_task.model, column.name))
                new_task.model = new_model
            
            return new_task

    def delete_task(self, task_id: int) -> bool:
        with self.db.get_session() as session:
            db_task = session.query(TaskDB).filter(TaskDB.id == task_id).first()
            if db_task:
                session.delete(db_task)
                session.commit()
                return True
            return False

    def update_task_status(self, task_id: int, status: str) -> bool:
        with self.db.get_session() as session:
            result = session.query(TaskDB).filter(TaskDB.id == task_id).update({"status": status})
            session.commit()
            return result > 0

    def update_task_enabled(self, task_id: int, is_enabled: bool) -> bool:
        with self.db.get_session() as session:
            result = session.query(TaskDB).filter(TaskDB.id == task_id).update({"is_enabled": is_enabled})
            session.commit()
            return result > 0
    
    def update_task_status_and_enabled_state(self, task_id: int, status: str, is_enabled: bool) -> bool:
        with self.db.get_session() as session:
            result = session.query(TaskDB).filter(TaskDB.id == task_id).update({
                "status": status,
                "is_enabled": is_enabled,
                "update_time": datetime.utcnow()
            })
            session.commit()
            return result > 0

    def get_task_counts_by_status(self) -> Dict[str, int]:
        with self.db.get_session() as session:
            result = session.query(
                TaskDB.status, 
                func.count(TaskDB.id)
            ).group_by(TaskDB.status).all()
            return {status: count for status, count in result}

    def get_total_count(self) -> int:
        with self.db.get_session() as session:
            return session.query(TaskDB).count()

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
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def update_alert_status(self, alert_id: int, status: str, remark: Optional[str] = None) -> Optional[Alert]:
        # This is a simplified update. A real implementation might involve logging the change.
        query = "UPDATE alerts SET status = %s, remark = %s WHERE id = %s"
        params = [status, remark, alert_id]
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

    def delete_alerts_older_than(self, days: int, alert_image_dir: str) -> int:
        """
        Safely deletes alerts older than a specified number of days and their associated image files.
        This operation is transactional for the database part.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        alerts_to_delete = []
        
        try:
            # Start a transaction to ensure atomicity for database operations
            self.db.start_transaction()

            # Step 1: Select the alerts to be deleted to get their image filenames
            query_select = "SELECT id, alert_image FROM alerts WHERE created_at < %s"
            alerts_to_delete = self.db.execute_query(query_select, (cutoff_date,), fetch='all')

            if not alerts_to_delete:
                self.db.commit() # Nothing to do, but commit to close transaction
                return 0

            # Step 2: Delete alert records from the database
            alert_ids_to_delete = [alert['id'] for alert in alerts_to_delete]
            placeholders = ', '.join(['%s'] * len(alert_ids_to_delete))
            query_delete = f"DELETE FROM alerts WHERE id IN ({placeholders})"
            
            self.db.execute_query(query_delete, tuple(alert_ids_to_delete))

            # Step 3: Commit the transaction
            self.db.commit()
            
        except Exception as e:
            print(f"Error during database transaction for alert deletion, rolling back. Error: {e}")
            self.db.rollback()
            return 0 # Return 0 as no alerts were successfully deleted
        finally:
            self.db.close_transaction()

        # Step 4: After successful DB deletion, delete the image files
        deleted_count = len(alerts_to_delete)
        print(f"Successfully deleted {deleted_count} alert records from the database. Now deleting image files.")

        for alert in alerts_to_delete:
            if alert.get('alert_image'):
                # Construct a safe path, preventing traversal attacks
                image_filename = os.path.basename(alert['alert_image'])
                image_path = os.path.join(alert_image_dir, image_filename)
                
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        print(f"Deleted image file: {image_path}")
                    except OSError as e:
                        print(f"Error deleting image file {image_path}: {e}")
                else:
                    print(f"Image file not found, skipping: {image_path}")
                    
        return deleted_count

    def delete_alert(self, alert_id: int) -> bool:
        """
        删除单条告警
        """
        query = "DELETE FROM alerts WHERE id = %s"
        try:
            result = self.db.execute_query(query, (alert_id,), commit=True)
            # execute_query返回受影响行数或None
            return result is None or result > 0
        except Exception as e:
            print(f"Error deleting alert {alert_id}: {e}")
            return False

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

class SystemConfigRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all_configs(self) -> Dict[str, Any]:
        query = "SELECT `key`, `value` FROM system_configs"
        results = self.db.execute_query(query, fetch='all')
        
        configs = {}
        for row in results:
            try:
                # Attempt to parse value as JSON, otherwise keep as string
                configs[row['key']] = json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                configs[row['key']] = row['value']
        return configs

    def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        query = "SELECT `value` FROM system_configs WHERE `key` = %s"
        result = self.db.execute_query(query, (key,), fetch='one')
        if result and result['value']:
            try:
                return json.loads(result['value'])
            except (json.JSONDecodeError, TypeError):
                return result['value']
        return None

    def update_configs(self, configs: Dict[str, Any]) -> None:
        """Updates multiple system configurations within a single transaction."""
        try:
            self.db.start_transaction()
            
            for key, value in configs.items():
                # Serialize complex types (dict, list) to a JSON string
                value_to_store = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                
                # Use INSERT ... ON DUPLICATE KEY UPDATE to handle both new and existing keys
                query = """
                INSERT INTO system_configs (`key`, `value`)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE `value` = %s
                """
                params = (key, value_to_store, value_to_store)
                self.db.execute_query(query, params)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating system configurations, rolling back transaction. Error: {e}")
            self.db.rollback()
            raise e # Re-raise the exception to be handled by the caller
        finally:
            self.db.close_transaction() 