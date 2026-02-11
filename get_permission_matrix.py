from django.contrib.auth.models import Group, Permission

groups = list(Group.objects.prefetch_related("permissions").all())
permissions = list(
    Permission.objects.select_related("content_type").order_by(
        "content_type__app_label", "codename"
    )
)

# Header: Permission + group names
header = ["Permission"] + [g.name for g in groups]
print("\t".join(header))

# Rows: each permission
for perm in permissions:
    perm_name = f"{perm.content_type.app_label}.{perm.codename}"
    row = [perm_name]

    for group in groups:
        if perm in group.permissions.all():
            row.append("✔")
        else:
            row.append("")

    print("\t".join(row))
