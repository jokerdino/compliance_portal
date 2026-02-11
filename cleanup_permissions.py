from django.apps import apps
from django.contrib.auth.models import Permission


# 1️⃣ Collect all valid permissions from current models
valid_permissions = set()

for model in apps.get_models():
    opts = model._meta
    app_label = opts.app_label
    model_name = opts.model_name

    # Default Django permissions
    for action in ["add", "change", "delete", "view"]:
        valid_permissions.add((app_label, f"{action}_{model_name}"))

    # Custom Meta permissions
    for codename, _ in opts.permissions:
        valid_permissions.add((app_label, codename))


# 2️⃣ Compare with database permissions
stale_permissions = []

for perm in Permission.objects.select_related("content_type"):
    key = (perm.content_type.app_label, perm.codename)
    if key not in valid_permissions:
        stale_permissions.append(perm)


# 3️⃣ Print results
print(f"\nFound {len(stale_permissions)} stale permissions:\n")

for p in stale_permissions:
    print(f"{p.content_type.app_label}.{p.codename}")
    p.delete()
