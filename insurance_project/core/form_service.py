"""
Form data service for handling form CRUD operations
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .database import (
    db, SELECT_FORM_DATA, COUNT_FORM_DATA, SELECT_FORM_BY_TASK_ID,
    INSERT_FORM_DATA, UPDATE_FORM_STATUS, UPDATE_FORM_CONTENT,
    DELETE_FORM_BY_TASK_ID, DELETE_FORM_BATCH
)

logger = logging.getLogger(__name__)

class FormDataService:
    """Service for managing form data"""
    
    @staticmethod
    def create_form(
        task_id: str,
        task_name: str,
        company: str,
        scene: str,
        progress: str = "0%",
        status: str = "解读中",
        llm_content: Optional[str] = None
    ) -> int:
        """Create a new form record"""
        try:
            params = {
                'task_id': task_id,
                'task_name': task_name,
                'company': company,
                'scene': scene,
                'progress': progress,
                'status': status,
                'llm_content': llm_content or ''
            }
            return db.execute_insert(INSERT_FORM_DATA, params)
        except Exception as e:
            logger.error(f"Failed to create form: {e}")
            raise
    
    @staticmethod
    def update_task_status(
        task_id: str,
        task_name: str,
        company: str,
        scene: str,
        progress: str,
        status: str,
        llm_content: Optional[str] = None
    ) -> int:
        """Update task status and related fields"""
        try:
            params = {
                'task_id': task_id,
                'task_name': task_name,
                'company': company,
                'scene': scene,
                'progress': progress,
                'status': status,
                'llm_content': llm_content or ''
            }
            return db.execute_update(UPDATE_FORM_STATUS, params)
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            raise
    
    @staticmethod
    def update_content(task_id: str, update_content: str) -> int:
        """Update form content"""
        try:
            params = {
                'task_id': task_id,
                'update_content': update_content
            }
            return db.execute_update(UPDATE_FORM_CONTENT, params)
        except Exception as e:
            logger.error(f"Failed to update form content: {e}")
            raise
    
    @staticmethod
    def get_form_by_task_id(task_id: str) -> Optional[Dict[str, Any]]:
        """Get form data by task ID"""
        try:
            params = {'task_id': task_id}
            result = db.execute_query(SELECT_FORM_BY_TASK_ID, params)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get form by task_id: {e}")
            raise
    
    @staticmethod
    def query_forms(
        task_name: Optional[str] = None,
        company: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Query forms with pagination"""
        try:
            offset = (page - 1) * page_size
            
            # Prepare query parameters
            params = {
                'task_name': task_name,
                'company': company,
                'task_name_pattern': f'%{task_name}%' if task_name else None,
                'limit': page_size,
                'offset': offset
            }
            
            # Get total count
            count_result = db.execute_query(COUNT_FORM_DATA, params)
            total = count_result[0]['total'] if count_result else 0
            
            # Get paginated results
            forms = db.execute_query(SELECT_FORM_DATA, params)
            
            # Format datetime fields
            for form in forms:
                if form.get('create_time'):
                    form['create_time'] = form['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'data': forms
            }
        except Exception as e:
            logger.error(f"Failed to query forms: {e}")
            raise
    
    @staticmethod
    def delete_form(task_id: str) -> int:
        """Delete a single form"""
        try:
            params = {'task_id': task_id}
            return db.execute_update(DELETE_FORM_BY_TASK_ID, params)
        except Exception as e:
            logger.error(f"Failed to delete form: {e}")
            raise
    
    @staticmethod
    def delete_forms_batch(task_ids: List[str]) -> int:
        """Delete multiple forms"""
        try:
            if not task_ids:
                return 0
            
            # Convert list to tuple for SQL IN clause
            task_ids_tuple = tuple(task_ids)
            params = {'task_ids': task_ids_tuple}
            return db.execute_update(DELETE_FORM_BATCH, params)
        except Exception as e:
            logger.error(f"Failed to delete forms in batch: {e}")
            raise
    
    @staticmethod
    def handle_task_start(task_id: str, task_name: str, company: str, scene: str) -> None:
        """Handle task start - create or update task record"""
        try:
            # Check if task already exists
            existing_form = FormDataService.get_form_by_task_id(task_id)
            
            if existing_form:
                # Update existing task
                FormDataService.update_task_status(
                    task_id=task_id,
                    task_name=task_name,
                    company=company,
                    scene=scene,
                    progress="0%",
                    status="解读中"
                )
            else:
                # Create new task
                FormDataService.create_form(
                    task_id=task_id,
                    task_name=task_name,
                    company=company,
                    scene=scene,
                    progress="0%",
                    status="解读中"
                )
            
            logger.info(f"Task {task_id} started successfully")
        except Exception as e:
            logger.error(f"Failed to handle task start: {e}")
            raise
    
    @staticmethod
    def handle_task_progress(
        task_id: str,
        task_name: str,
        company: str,
        scene: str,
        progress: str
    ) -> None:
        """Handle task progress update"""
        try:
            FormDataService.update_task_status(
                task_id=task_id,
                task_name=task_name,
                company=company,
                scene=scene,
                progress=progress,
                status="解读中"
            )
            logger.info(f"Task {task_id} progress updated to {progress}")
        except Exception as e:
            logger.error(f"Failed to handle task progress: {e}")
            raise
    
    @staticmethod
    def handle_task_success(
        task_id: str,
        task_name: str,
        company: str,
        scene: str,
        llm_content: str
    ) -> None:
        """Handle task success completion"""
        try:
            FormDataService.update_task_status(
                task_id=task_id,
                task_name=task_name,
                company=company,
                scene=scene,
                progress="100%",
                status="完成",
                llm_content=llm_content
            )
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            logger.error(f"Failed to handle task success: {e}")
            raise
    
    @staticmethod
    def handle_task_error(
        task_id: str,
        task_name: str,
        company: str,
        scene: str,
        progress: str
    ) -> None:
        """Handle task error/failure"""
        try:
            # Check if task exists
            existing_form = FormDataService.get_form_by_task_id(task_id)
            
            if existing_form:
                # Update existing task to failed
                FormDataService.update_task_status(
                    task_id=task_id,
                    task_name=task_name,
                    company=company,
                    scene=scene,
                    progress=progress,
                    status="失败"
                )
            else:
                # Create new failed task record
                FormDataService.create_form(
                    task_id=task_id,
                    task_name=task_name,
                    company=company,
                    scene=scene,
                    progress=progress,
                    status="失败"
                )
            
            logger.info(f"Task {task_id} marked as failed at progress {progress}")
        except Exception as e:
            logger.error(f"Failed to handle task error: {e}")
            raise