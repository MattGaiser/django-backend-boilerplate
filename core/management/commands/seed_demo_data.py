from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import User, Organization, OrganizationMembership, OrgRole


class Command(BaseCommand):
    help = 'Seed the database with demo data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing demo data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Starting demo data seeding...'))
        
        if options['clean']:
            self.clean_demo_data()
        
        with transaction.atomic():
            # Create demo organization
            org = self.create_demo_organization()
            
            # Create demo users
            admin_user = self.create_admin_user(org)
            regular_user = self.create_regular_user(org)
            viewer_user = self.create_viewer_user(org)
            
            self.stdout.write(self.style.SUCCESS('\n✅ Demo data seeded successfully!'))
            self.output_credentials(admin_user, regular_user, viewer_user, org)

    def clean_demo_data(self):
        """Clean existing demo data"""
        self.stdout.write('🧹 Cleaning existing demo data...')
        
        # Delete demo users (this will cascade to memberships)
        demo_emails = [
            'admin@demo.com',
            'user@demo.com', 
            'viewer@demo.com'
        ]
        User.objects.filter(email__in=demo_emails).delete()
        
        # Delete demo organization
        Organization.objects.filter(name='Demo Organization').delete()
        
        self.stdout.write(self.style.WARNING('Existing demo data cleaned.'))

    def create_demo_organization(self):
        """Create a demo organization"""
        org, created = Organization.objects.get_or_create(
            name='Demo Organization',
            defaults={
                'description': 'A sample organization for development and testing purposes.',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'📊 Created organization: {org.name}')
        else:
            self.stdout.write(f'📊 Using existing organization: {org.name}')
        
        return org

    def create_admin_user(self, organization):
        """Create an admin user"""
        user, created = User.objects.get_or_create(
            email='admin@demo.com',
            defaults={
                'full_name': 'Demo Admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'👤 Created admin user: {user.email}')
        else:
            self.stdout.write(f'👤 Using existing admin user: {user.email}')
        
        # Create or update membership
        membership, created = OrganizationMembership.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={
                'role': OrgRole.SUPER_ADMIN,
                'is_default': True
            }
        )
        
        if created:
            self.stdout.write(f'🔗 Created admin membership with role: {membership.get_role_display()}')
        
        return user

    def create_regular_user(self, organization):
        """Create a regular user"""
        user, created = User.objects.get_or_create(
            email='user@demo.com',
            defaults={
                'full_name': 'Demo User',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False
            }
        )
        
        if created:
            user.set_password('user123')
            user.save()
            self.stdout.write(f'👤 Created regular user: {user.email}')
        else:
            self.stdout.write(f'👤 Using existing regular user: {user.email}')
        
        # Create or update membership
        membership, created = OrganizationMembership.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={
                'role': OrgRole.EDITOR,
                'is_default': True
            }
        )
        
        if created:
            self.stdout.write(f'🔗 Created user membership with role: {membership.get_role_display()}')
        
        return user

    def create_viewer_user(self, organization):
        """Create a viewer user"""
        user, created = User.objects.get_or_create(
            email='viewer@demo.com',
            defaults={
                'full_name': 'Demo Viewer',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False
            }
        )
        
        if created:
            user.set_password('viewer123')
            user.save()
            self.stdout.write(f'👤 Created viewer user: {user.email}')
        else:
            self.stdout.write(f'👤 Using existing viewer user: {user.email}')
        
        # Create or update membership
        membership, created = OrganizationMembership.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={
                'role': OrgRole.VIEWER,
                'is_default': True
            }
        )
        
        if created:
            self.stdout.write(f'🔗 Created viewer membership with role: {membership.get_role_display()}')
        
        return user

    def output_credentials(self, admin_user, regular_user, viewer_user, organization):
        """Output the demo credentials"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🔑 DEMO CREDENTIALS'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Organization: {organization.name}')
        self.stdout.write(f'Organization ID: {organization.id}')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('👑 SUPER ADMIN USER:'))
        self.stdout.write(f'   Email: {admin_user.email}')
        self.stdout.write(f'   Password: admin123')
        self.stdout.write(f'   Role: Super Admin')
        self.stdout.write(f'   Django Admin: ✅ Yes')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('✏️  EDITOR USER:'))
        self.stdout.write(f'   Email: {regular_user.email}')
        self.stdout.write(f'   Password: user123')
        self.stdout.write(f'   Role: Editor')
        self.stdout.write(f'   Django Admin: ❌ No')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('👁️  VIEWER USER:'))
        self.stdout.write(f'   Email: {viewer_user.email}')
        self.stdout.write(f'   Password: viewer123')
        self.stdout.write(f'   Role: Viewer')
        self.stdout.write(f'   Django Admin: ❌ No')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('🌐 ACCESS URLS:'))
        self.stdout.write('   Django Admin: http://localhost:8001/admin/')
        self.stdout.write('   API Root: http://localhost:8001/')
        self.stdout.write('   Prefect UI: http://localhost:4200/')
        self.stdout.write('   pgAdmin: http://localhost:5050/')
        self.stdout.write(self.style.SUCCESS('='*60))