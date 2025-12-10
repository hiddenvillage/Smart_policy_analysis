#!/usr/bin/env python
"""
Database initialization script
"""
import os
import sys
import django

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insurance_project.settings')
django.setup()

from insurance_project.core.database import init_database

def main():
    """Initialize database and create tables"""
    print("Initializing database...")
    try:
        init_database()
        print("Database initialized successfully!")
        print("\nTable 'form_data' has been created.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()