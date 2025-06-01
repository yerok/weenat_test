import os
import django

# 1. Définir la variable d'environnement Django (ajuster selon ton projet)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weenat_test_api.settings')

# 2. Initialiser Django
django.setup()

# 3. Importer MonkeyType et appliquer les types
from monkeytype import apply

modules_to_apply = [
    'api.views',
    # ajoute d'autres modules si besoin
]

for module in modules_to_apply:
    print(f"Applying MonkeyType to {module} ...")
    apply.apply(module)
print("Done applying MonkeyType.")