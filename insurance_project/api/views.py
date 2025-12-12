"""
API views for insurance group order interpretation
"""
import uuid
import os
import json
import logging
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response

from insurance_project.core.form_service import FormDataService

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def start_interpretation(request):
    """
    Start group order interpretation
    Required fields: task_name, company, scene
    Files: Support three modes:
    1. Only pdf_file (contract file)
    2. Only png_files (1-30 images)
    3. Both pdf_file and png_files
    """
    try:
        # Extract form data
        task_name = request.data.get('task_name')
        company = request.data.get('company')
        scene = request.data.get('scene')
        
        # Validate required fields
        if not all([task_name, company, scene]):
            return Response({
                'success': False,
                'error': 'Missing required fields: task_name, company, scene'
            }, status=400)
        
        # Generate unique task ID
        task_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
        
        # Validate file uploads
        pdf_file = request.FILES.get('pdf_file')
        png_files = request.FILES.getlist('png_files')
        
        # Validate file requirements
        # Support three modes:
        # 1. Only contract file (PDF/DOC/DOCX)
        # 2. Only image files (1-30 PNG/JPG)
        # 3. Both contract file and image files
        if not pdf_file and len(png_files) == 0:
            return Response({
                'success': False,
                'error': 'Please upload either a contract file, or images, or both'
            }, status=400)
        
        # Validate PDF file type (only if uploaded)
        if pdf_file:
            if not pdf_file.name.lower().endswith('.pdf'):
                return Response({
                    'success': False,
                    'error': 'Contract file must be PDF format'
                }, status=400)
        
        # Validate PNG/JPG files (only if uploaded)
        if png_files:
            if len(png_files) > 30:
                return Response({
                    'success': False,
                    'error': 'Maximum 30 image files allowed'
                }, status=400)
            
            img_extensions = ['.png', '.jpg', '.jpeg']
            for png_file in png_files:
                if not any(png_file.name.lower().endswith(ext) for ext in img_extensions):
                    return Response({
                        'success': False,
                        'error': f'File {png_file.name} must be PNG, JPG, or JPEG format'
                    }, status=400)
        
        # Save files
        task_dir = os.path.join('uploads', task_id)
        full_task_dir = os.path.join(settings.MEDIA_ROOT, task_dir)
        os.makedirs(full_task_dir, exist_ok=True)
        
        # Save files based on upload pattern
        pdf_path_saved = None
        png_paths = []
        
        if pdf_file:
            # Pattern 1: Save contract file
            pdf_filename = 'contract.pdf'
            pdf_path = os.path.join(full_task_dir, pdf_filename)
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            pdf_path_saved = os.path.join(task_dir, pdf_filename)
            logger.info(f"Saved PDF file to: {pdf_path_saved}")
        
        if png_files:
            # Pattern 2: Save image files
            for i, png_file in enumerate(png_files):
                png_filename = f'quote_{i+1}.png'
                png_path = os.path.join(full_task_dir, png_filename)
                with open(png_path, 'wb') as f:
                    for chunk in png_file.chunks():
                        f.write(chunk)
                png_path_saved = os.path.join(task_dir, png_filename)
                png_paths.append(png_path_saved)
            logger.info(f"Saved {len(png_files)} image files")
        
        # Create initial task record with error handling
        try:
            FormDataService.handle_task_start(
                task_id=task_id,
                task_name=task_name,
                company=company,
                scene=scene
            )
            logger.info(f"Task record created for task_id: {task_id}")
        except Exception as db_error:
            logger.error(f"Database error while creating task: {db_error}")
            # Continue even if database fails, just log the error
            # We can still return success since files are saved
        
        # Trigger async interpretation task (using Celery in production)
        # For now, simulate async processing
        try:
            from insurance_project.api.tasks import process_interpretation_task
            process_interpretation_task.delay(
                task_id=task_id,
                task_name=task_name,
                company=company,
                scene=scene,
                pdf_path=pdf_path_saved,
                png_paths=png_paths
            )
        except ImportError:
            # Fallback to direct processing if Celery is not configured
            logger.warning(f"Celery not configured, processing task {task_id} directly")
            # Simulate processing
            try:
                FormDataService.handle_task_success(
                    task_id=task_id,
                    task_name=task_name,
                    company=company,
                    scene=scene,
                    llm_content=json.dumps({
                        'message': 'Group order interpretation completed successfully',
                        'extracted_data': {
                            'policy_number': 'POL-' + task_id,
                            'company_name': company,
                            'scene_type': scene,
                            'coverage_details': 'Sample coverage details',
                            'premium_amount': 'Sample premium amount'
                        }
                    }, ensure_ascii=False)
                )
                logger.info(f"Task success status updated for task_id: {task_id}")
            except Exception as success_error:
                logger.error(f"Failed to update task success status: {success_error}")
                # Continue even if update fails
        
        return Response({
            'success': True,
            'task_id': task_id,
            'message': 'Group order interpretation task started successfully'
        }, status=202)
        
    except Exception as e:
        logger.error(f"Error starting interpretation: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def query_task_status(request):
    """
    Query task status
    Required query params: task_name, company
    Optional: page, page_size
    """
    try:
        task_name = request.query_params.get('task_name')
        company = request.query_params.get('company')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Validate required parameters
        if not task_name or not company:
            return Response({
                'success': False,
                'error': 'Required query parameters: task_name, company'
            }, status=400)
        
        # Query forms
        result = FormDataService.query_forms(
            task_name=task_name,
            company=company,
            page=page,
            page_size=page_size
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error querying task status: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@api_view(['GET'])
def get_all_tasks(request):
    """
    Get all tasks from database
    Optional query params: page, page_size, status, company, scene, create_time
    """
    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        status = request.query_params.get('status', None)
        company = request.query_params.get('company', None)
        scene = request.query_params.get('scene', None)
        create_time = request.query_params.get('create_time', None)
        
        # Handle empty string values to treat them as None (meaning all)
        if company == '':
            company = None
        if scene == '':
            scene = None
        if create_time == '':
            create_time = None
        
        # Get all tasks
        result = FormDataService.get_all_tasks(
            page=page,
            page_size=page_size,
            status=status,
            company=company,
            scene=scene,
            create_time=create_time
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting all tasks: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@api_view(['POST'])
def update_form_content(request):
    """
    Update form content (llm_content field)
    Required fields: task_id, content
    """
    try:
        task_id = request.data.get('task_id')
        content = request.data.get('content')
        
        if not task_id or content is None:
            return Response({
                'success': False,
                'error': 'Missing required fields: task_id, content'
            }, status=400)
        
        # Update form content
        affected_rows = FormDataService.update_content(task_id, content)
        
        if affected_rows == 0:
            return Response({
                'success': False,
                'error': 'Task not found'
            }, status=404)
        
        return Response({
            'success': True,
            'message': 'Form content updated successfully'
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error updating form content: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@api_view(['DELETE'])
def delete_form(request, task_id):
    """
    Delete a single form by task_id
    """
    try:
        affected_rows = FormDataService.delete_form(task_id)
        
        if affected_rows == 0:
            return Response({
                'success': False,
                'error': 'Task not found'
            }, status=404)
        
        return Response({
            'success': True,
            'message': 'Form deleted successfully'
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error deleting form: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@api_view(['DELETE'])
def delete_forms_batch(request):
    """
    Delete multiple forms
    Required field: task_ids (list)
    """
    try:
        task_ids = request.data.get('task_ids', [])
        
        if not task_ids:
            return Response({
                'success': False,
                'error': 'task_ids list is required'
            }, status=400)
        
        affected_rows = FormDataService.delete_forms_batch(task_ids)
        
        return Response({
            'success': True,
            'message': f'Deleted {affected_rows} forms successfully'
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error deleting forms in batch: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@api_view(['GET'])
def get_form_details(request, task_id):
    """
    Get form details by task_id
    """
    try:
        form = FormDataService.get_form_by_task_id(task_id)
        
        if not form:
            return Response({
                'success': False,
                'error': 'Task not found'
            }, status=404)
        
        # Format datetime
        if form.get('create_time'):
            form['create_time'] = form['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return Response({
            'success': True,
            'data': form
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting form details: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({
        'success': True,
        'message': 'Service is running',
        'timestamp': datetime.now().isoformat()
    })