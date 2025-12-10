"""
Celery tasks for async processing
"""
import json
import time
import random
import logging
from celery import shared_task
from insurance_project.core.form_service import FormDataService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_interpretation_task(self, task_id, task_name, company, scene, pdf_path, png_paths):
    """
    Process group order interpretation asynchronously
    """
    try:
        logger.info(f"Starting interpretation task {task_id}")
        
        # Simulate processing steps
        total_steps = 10
        for step in range(1, total_steps + 1):
            # Simulate processing time
            time.sleep(random.uniform(1, 3))
            
            # Calculate progress
            progress = f"{int((step / total_steps) * 100)}%"
            
            # Update task progress
            FormDataService.handle_task_progress(
                task_id=task_id,
                task_name=task_name,
                company=company,
                scene=scene,
                progress=progress
            )
            
            logger.info(f"Task {task_id} progress: {progress}")
            
            # Simulate occasional errors (5% chance)
            if random.random() < 0.05:
                raise Exception(f"Simulated processing error at step {step}")
        
        # Generate mock interpretation result
        result = {
            'task_id': task_id,
            'task_name': task_name,
            'company': company,
            'scene': scene,
            'interpretation_result': {
                'policy_info': {
                    'policy_number': f'POL-{task_id}',
                    'policy_type': scene,
                    'effective_date': '2025-01-01',
                    'expiry_date': '2026-01-01',
                    'insured_count': random.randint(50, 500),
                    'premium_amount': f'¥{random.randint(100000, 500000):,}',
                },
                'coverage_details': {
                    'main_coverage': random.choice(['门诊医疗', '住院医疗', '重疾保障', '意外伤害']),
                    'additional_coverage': ['就医绿通', '第二诊疗意见', '健康管理服务'],
                    'deductible': f'¥{random.choice([0, 100, 500, 1000]):,}',
                    'reimbursement_ratio': f'{random.choice([80, 90, 100])}%'
                },
                'special_terms': [
                    '等待期：30天',
                    '医院范围：二级及以上公立医院',
                    '理赔方式：先垫付后报销'
                ],
                'exclusions': [
                    '既往症不保',
                    '美容整形相关费用',
                    '非治疗性体检费用'
                ]
            },
            'processing_time': f"{random.uniform(2.5, 5.1):.1f}秒",
            'confidence_score': f"{random.uniform(85, 98):.1f}%",
            'recommendations': [
                '建议补充补充医疗保险',
                '可考虑增加重疾保额',
                '建议定期更新员工名单'
            ]
        }
        
        # Save result to database
        FormDataService.handle_task_success(
            task_id=task_id,
            task_name=task_name,
            company=company,
            scene=scene,
            llm_content=json.dumps(result, ensure_ascii=False, indent=2)
        )
        
        logger.info(f"Task {task_id} completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Task {task_id} failed: {exc}")
        
        # Calculate current progress
        current_step = locals().get('step', 0)
        progress = f"{int((current_step / total_steps) * 100)}%" if 'total_steps' in locals() else "0%"
        
        # Mark task as failed
        FormDataService.handle_task_error(
            task_id=task_id,
            task_name=task_name,
            company=company,
            scene=scene,
            progress=progress
        )
        
        # Retry if retry attempts available
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        # Log final failure
        logger.error(f"Task {task_id} failed after {self.max_retries} retries")
        raise exc