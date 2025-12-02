"""
Management command to create an employee/admin account.

Usage:
    python manage.py create_employee --email admin@example.com --password Admin123! --name "Admin User" --admin
"""

from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User, Employee


class Command(BaseCommand):
    help = 'Create an employee or admin account'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email address for the employee')
        parser.add_argument('--password', type=str, required=True, help='Password for the employee')
        parser.add_argument('--name', type=str, required=True, help='Employee name')
        parser.add_argument('--admin', action='store_true', help='Make this employee an admin')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        name = options['name']
        is_admin = options['admin']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        # Create the user
        user = User.objects.create_user(
            email=email,
            password=password,
            is_staff=is_admin,  # Allow access to Django admin
            is_superuser=is_admin,  # Full permissions if admin
        )

        # Create the employee profile
        employee = Employee.objects.create(
            user=user,
            employee_name=name,
            is_admin=is_admin
        )

        role = 'admin' if is_admin else 'employee'
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {role}: {email} ({name})')
        )
