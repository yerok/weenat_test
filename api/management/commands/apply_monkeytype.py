from django.core.management.base import BaseCommand
import subprocess
import django

class Command(BaseCommand):
    help = "Apply monkeytype type annotations to specified modules"
    
    django.setup()

    def handle(self, *args, **options):
        modules = [
            "api.views",        ]
        for module in modules:
            self.stdout.write(f"Applying monkeytype to {module}...")
            subprocess.run(["monkeytype", "apply", module], check=True)
        self.stdout.write(self.style.SUCCESS("MonkeyType apply done for all modules."))