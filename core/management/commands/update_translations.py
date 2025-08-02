"""
Management command to update translation files.

This command runs makemessages for all configured languages and then compiles them.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Command(BaseCommand):
    """Management command to update and compile translation files."""
    
    help = 'Update and compile translation files for all configured languages'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--no-compile',
            action='store_true',
            help='Only update message files, do not compile them'
        )
        parser.add_argument(
            '--language',
            '-l',
            action='append',
            dest='languages',
            help='Update only specific language(s). Can be used multiple times.'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        languages = options.get('languages', [])
        no_compile = options.get('no_compile', False)
        
        # If no specific languages provided, use all configured languages except English
        if not languages:
            languages = [lang_code for lang_code, lang_name in settings.LANGUAGES if lang_code != 'en']
        
        self.stdout.write(
            self.style.SUCCESS(
                _('Updating translation files for languages: {}').format(', '.join(languages))
            )
        )
        
        # Run makemessages for each language
        for language in languages:
            self.stdout.write(_('Processing language: {}').format(language))
            try:
                call_command('makemessages', locale=[language], verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS(_('✓ Updated messages for {}').format(language))
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(_('✗ Error updating messages for {}: {}').format(language, e))
                )
        
        # Compile messages unless --no-compile is specified
        if not no_compile:
            self.stdout.write(_('Compiling translation files...'))
            try:
                call_command('compilemessages', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS(_('✓ Translation files compiled successfully'))
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(_('✗ Error compiling messages: {}').format(e))
                )
        
        self.stdout.write(
            self.style.SUCCESS(_('Translation update completed!'))
        )