"""
Django management command for environment validation.

Validates environment variables and configuration to ensure proper setup.
"""

from django.core.management.base import BaseCommand, CommandError

from core.validation import EnvironmentValidator


class Command(BaseCommand):
    """Management command to validate environment configuration."""
    
    help = "Validate environment variables and configuration"
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--exit-on-fail",
            action="store_true",
            help="Exit with error code if validation fails",
        )
        parser.add_argument(
            "--quiet",
            action="store_true", 
            help="Only show errors and warnings, not success messages",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format",
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        validator = EnvironmentValidator()
        results = validator.validate_all()
        
        if options["json"]:
            import json
            self.stdout.write(json.dumps(results, indent=2))
        else:
            validator.print_validation_results(results)
        
        if not results["success"]:
            if options["exit_on_fail"]:
                raise CommandError("Environment validation failed")
            else:
                self.stdout.write(
                    self.style.ERROR("Environment validation failed (use --exit-on-fail to exit with error)")
                )
        elif not options["quiet"]:
            self.stdout.write(
                self.style.SUCCESS("Environment validation completed successfully")
            )