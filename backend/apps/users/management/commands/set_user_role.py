"""
Management command to set user roles (employee/admin status).
Usage:
    python manage.py set_user_role <email> --employee --admin
    python manage.py set_user_role <email> --remove-employee
    python manage.py set_user_role <email> --list
"""
from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User, Employee, Customer


class Command(BaseCommand):
    help = 'Set user role (employee/admin status) for a given user.'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the user to modify.'
        )
        parser.add_argument(
            '--employee',
            action='store_true',
            help='Make user an employee (creates Employee profile if not exists).'
        )
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Make user an admin (sets is_admin=True on Employee profile).'
        )
        parser.add_argument(
            '--remove-employee',
            action='store_true',
            help='Remove employee status (deletes Employee profile).'
        )
        parser.add_argument(
            '--remove-admin',
            action='store_true',
            help='Remove admin status (sets is_admin=False but keeps Employee profile).'
        )
        parser.add_argument(
            '--name',
            type=str,
            default=None,
            help='Employee name (optional, defaults to email username).'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List current user role information.'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist.')

        # List mode
        if options['list']:
            self._show_user_info(user)
            return

        # Validation
        if options['employee'] and options['remove_employee']:
            raise CommandError('Cannot use --employee and --remove-employee together.')
        
        if options['admin'] and options['remove_admin']:
            raise CommandError('Cannot use --admin and --remove-admin together.')

        # Remove employee profile
        if options['remove_employee']:
            try:
                employee = Employee.objects.get(user=user)
                employee.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'Removed Employee profile for {email}.'
                ))
            except Employee.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'User {email} does not have an Employee profile.'
                ))
            return

        # Create/update employee profile
        if options['employee'] or options['admin']:
            employee_name = options['name'] or email.split('@')[0].title()
            is_admin = options['admin']
            
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'employee_name': employee_name,
                    'is_admin': is_admin
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Created Employee profile for {email}: '
                    f'name="{employee_name}", is_admin={is_admin}'
                ))
            else:
                # Update existing
                if options['name']:
                    employee.employee_name = employee_name
                if options['admin']:
                    employee.is_admin = True
                employee.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Updated Employee profile for {email}: '
                    f'name="{employee.employee_name}", is_admin={employee.is_admin}'
                ))
            return

        # Remove admin status only
        if options['remove_admin']:
            try:
                employee = Employee.objects.get(user=user)
                employee.is_admin = False
                employee.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Removed admin status for {email}. Still an employee.'
                ))
            except Employee.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'User {email} does not have an Employee profile.'
                ))
            return

        # If no action specified, show help
        self._show_user_info(user)
        self.stdout.write('')
        self.stdout.write('Use --employee, --admin, --remove-employee, or --remove-admin to modify.')

    def _show_user_info(self, user):
        """Display current user role information."""
        self.stdout.write(self.style.MIGRATE_HEADING(f'\nUser: {user.email}'))
        self.stdout.write(f'  ID: {user.id}')
        self.stdout.write(f'  is_superuser: {user.is_superuser}')
        self.stdout.write(f'  is_staff: {user.is_staff}')
        self.stdout.write(f'  is_active: {user.is_active}')
        
        # Customer profile
        try:
            customer = Customer.objects.get(user=user)
            self.stdout.write(self.style.SUCCESS(f'  Has Customer profile: Yes'))
        except Customer.DoesNotExist:
            self.stdout.write(f'  Has Customer profile: No')
        
        # Employee profile
        try:
            employee = Employee.objects.get(user=user)
            self.stdout.write(self.style.SUCCESS(f'  Has Employee profile: Yes'))
            self.stdout.write(f'    Employee name: {employee.employee_name}')
            if employee.is_admin:
                self.stdout.write(self.style.SUCCESS(f'    is_admin: True'))
            else:
                self.stdout.write(f'    is_admin: False')
        except Employee.DoesNotExist:
            self.stdout.write(f'  Has Employee profile: No')
