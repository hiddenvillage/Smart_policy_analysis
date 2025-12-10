#!/usr/bin/env python
"""
Server startup script with database initialization
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Initialize database and start server"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insurance_project.settings')
    
    # Setup Django
    django.setup()
    
    # Initialize database
    try:
        from insurance_project.core.database import init_database
        print("Initializing database...")
        init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("Continuing with server startup...")
    
    # Start development server
    os.system('python manage.py runserver 0.0.0.0:8000')

if __name__ == '__main__':
    main()