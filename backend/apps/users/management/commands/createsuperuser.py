"""
Custom createsuperuser command that also creates an Employee profile with is_admin=True.
This overrides Django's default createsuperuser to ensure superusers can access the admin dashboard.
"""
from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from apps.users.models import Employee


class Command(BaseCommand):
    help = 'Create a superuser with an associated admin Employee profile.'

    def handle(self, *args, **options):
        # Call the original createsuperuser
        super().handle(*args, **options)
        
        # After successful creation, add Employee profile
        # We need to get the user that was just created
        email = options.get('email') or options.get(self.UserModel.USERNAME_FIELD)
        
        if email:
            try:
                user = self.UserModel._default_manager.get_by_natural_key(email)
                employee, created = Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        'employee_name': email.split('@')[0].title(),
                        'is_admin': True
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Employee profile created for {email} with admin privileges.'
                    ))
                elif not employee.is_admin:
                    employee.is_admin = True
                    employee.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Employee profile updated with admin privileges for {email}.'
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'Employee profile already exists with admin privileges for {email}.'
                    ))
            except self.UserModel.DoesNotExist:
                pass  # User creation may have failed, don't create employee
            except Exception as e:
                self.stderr.write(self.style.WARNING(
                    f'Could not create Employee profile: {e}'
                ))
