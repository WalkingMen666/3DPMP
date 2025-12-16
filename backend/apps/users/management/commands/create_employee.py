"""
Management command to create an employee/admin account.

Usage:
    python manage.py create_employee --email admin@example.com --password Admin123! --name "Admin User" --admin
"""

from django.core.management.base import BaseCommand, CommandError
from allauth.account.models import EmailAddress
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
        user_exists = User.objects.filter(email=email).exists()
        
        if user_exists:
            # Get existing user and update password
            user = User.objects.get(email=email)
            user.set_password(password)
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.save()
            
            self.stdout.write(
                self.style.NOTICE(f'User with email {email} already exists - updated password and permissions')
            )
            
            # Check if employee profile exists
            if not Employee.objects.filter(user=user).exists():
                # Create the employee profile
                Employee.objects.create(
                    user=user,
                    employee_name=name,
                    is_admin=is_admin
                )
                self.stdout.write(
                    self.style.NOTICE(f'Created employee profile for existing user')
                )
            else:
                # Update existing employee profile
                employee = Employee.objects.get(user=user)
                employee.employee_name = name
                employee.is_admin = is_admin
                employee.save()
                self.stdout.write(
                    self.style.NOTICE(f'Updated existing employee profile')
                )
        else:
            # Create new user
            user = User.objects.create_user(
                email=email,
                password=password,
                is_staff=is_admin,  # Allow access to Django admin
                is_superuser=is_admin,  # Full permissions if admin
            )

            # Create the employee profile
            Employee.objects.create(
                user=user,
                employee_name=name,
                is_admin=is_admin
            )

        # Handle email verification
        if EmailAddress.objects.filter(email=email).exists():
            # Update existing email address to verified
            EmailAddress.objects.filter(email=email).update(
                verified=True,
                primary=True
            )
            self.stdout.write(
                self.style.NOTICE(f'Marked existing email as verified')
            )
        else:
            # Create verified email address
            EmailAddress.objects.create(
                user=user,
                email=email,
                verified=True,
                primary=True
            )

        role = 'admin' if is_admin else 'employee'
        action = 'Updated' if user_exists else 'Created'
        self.stdout.write(
            self.style.SUCCESS(f'{action} {role}: {email} ({name}) [email verified]')
        )
