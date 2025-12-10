"""
Django management command to initialize database
"""
from django.core.management.base import BaseCommand
from insurance_project.core.database import init_database

class Command(BaseCommand):
    help = 'Initialize database and create form_data table'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database...')
        try:
            init_database()
            self.stdout.write(self.style.SUCCESS('Database initialized successfully!'))
            self.stdout.write(self.style.SUCCESS('Table "form_data" has been created.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database initialization failed: {e}'))