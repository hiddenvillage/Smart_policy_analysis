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
from rest_framework import status

from insurance_project.core.form_service import FormDataService

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def start_interpretation(request):
    """
    Start group order interpretation
    Required fields: task_name, company, scene, pdf_file, [png_files]
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
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique task ID
        task_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
        
        # Validate file uploads
        pdf_file = request.FILES.get('pdf_file')
        png_files = request.FILES.getlist('png_files')
        
        if not pdf_file:
            return Response({
                'success': False,
                'error': 'PDF file is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file types
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({
                'success': False,
                'error': 'PDF file must have .pdf extension'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate PNG files (max 30)
        if len(png_files) > 30:
            return Response({
                'success': False,
                'error': 'Maximum 30 PNG files allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        for png_file in png_files:
            if not png_file.name.lower().endswith('.png'):
                return Response({
                    'success': False,
                    'error': f'File {png_file.name} must have .png extension'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save files
        task_dir = os.path.join('uploads', task_id)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, task_dir), exist_ok=True)
        
        # Save PDF file
        pdf_path = os.path.join(task_dir, f'contract_{pdf_file.name}')
        pdf_path_saved = default_storage.save(pdf_path, pdf_file)
        
        # Save PNG files
        png_paths = []
        for i, png_file in enumerate(png_files):
            png_path = os.path.join(task_dir, f'quote_{i+1}.png')
            png_path_saved = default_storage.save(png_path, png_file)
            png_paths.append(png_path_saved)
        
        # Create initial task record
        FormDataService.handle_task_start(
            task_id=task_id,
            task_name=task_name,
            company=company,
            scene=scene
        )
        
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
        
        return Response({
            'success': True,
            'task_id': task_id,
            'message': 'Group order interpretation task started successfully'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error starting interpretation: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
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
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error querying task status: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update form content
        affected_rows = FormDataService.update_content(task_id, content)
        
        if affected_rows == 0:
            return Response({
                'success': False,
                'error': 'Task not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Form content updated successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating form content: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Form deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting form: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            }, status=status.HTTP_400_BAD_REQUEST)
        
        affected_rows = FormDataService.delete_forms_batch(task_ids)
        
        return Response({
            'success': True,
            'message': f'Deleted {affected_rows} forms successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting forms in batch: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Format datetime
        if form.get('create_time'):
            form['create_time'] = form['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return Response({
            'success': True,
            'data': form
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting form details: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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