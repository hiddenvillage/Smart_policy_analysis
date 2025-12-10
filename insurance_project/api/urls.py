"""
URL configuration for API app
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Group order interpretation endpoints
    path('interpretation/start/', views.start_interpretation, name='start_interpretation'),
    path('interpretation/status/', views.query_task_status, name='query_task_status'),
    
    # Form management endpoints
    path('forms/<str:task_id>/', views.get_form_details, name='get_form_details'),
    path('forms/<str:task_id>/update/', views.update_form_content, name='update_form_content'),
    path('forms/<str:task_id>/delete/', views.delete_form, name='delete_form'),
    path('forms/delete-batch/', views.delete_forms_batch, name='delete_forms_batch'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]