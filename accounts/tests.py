# Create your tests here.
# from django.test import TestCase
import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission, Group
from accounts.models import Department, CustomUser


@pytest.fixture
def admin_user(db):
    """A user with permissions to manage other users."""
    user = CustomUser.objects.create(username="admin_staff", is_staff=True)
    # Grant permissions found in accounts.views
    perms = Permission.objects.filter(
        codename__in=[
            "add_customuser",
            "view_customuser",
            "change_customuser",
            "add_department",
            "view_department",
            "change_department",
        ]
    )
    user.user_permissions.add(*perms)
    return user


@pytest.fixture
def normal_user(db):
    """Fixture to create a normal user in the accounts app."""
    return CustomUser.objects.create(username="normal_user")


@pytest.fixture
def it_department(db):
    """Fixture to create a department in the accounts app."""
    return Department.objects.create(department_name="IT")


@pytest.mark.django_db
class TestLoginFlow:
    def test_login_redirects_to_reset_if_flag_true(self, client):
        # Create user with reset_password=True
        user = CustomUser.objects.create(username="newbie", reset_password=True)
        user.set_password("password123")
        user.save()

        # Submit login form
        login_url = reverse("login")
        response = client.post(
            login_url, {"username": "newbie", "password": "password123"}
        )

        # Should redirect to password_reset
        assert response.status_code == 302
        assert response.url == reverse("password_reset")

    def test_force_password_reset_clears_flag(self, client):
        user = CustomUser.objects.create(username="reset_user", reset_password=True)
        user.set_password("old_password")
        user.save()
        client.force_login(user)

        # Submit the PasswordChangeForm
        url = reverse("password_reset")
        response = client.post(
            url,
            {
                "old_password": "old_password",
                "new_password1": "new_secret_123",
                "new_password2": "new_secret_123",
            },
        )

        user.refresh_from_db()
        assert response.status_code == 302
        assert user.reset_password is False  # Flag cleared!
        assert user.check_password("new_secret_123")  # Password updated!


@pytest.mark.django_db
class TestUserManagement:
    def test_normal_user_cannot_view_users(self, client, normal_user):
        client.force_login(normal_user)
        url = reverse("user_list")
        response = client.get(url)
        assert response.status_code == 403

        url = reverse("user_detail", kwargs={"pk": 1})
        response = client.get(url)
        assert response.status_code == 403

    def test_normal_user_cannot_view_departments(self, client, normal_user):
        client.force_login(normal_user)
        url = reverse("department_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_normal_user_cannot_create_user(self, client, normal_user):
        client.force_login(normal_user)
        url = reverse("user_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_normal_user_cannot_update_user(self, client, normal_user):
        client.force_login(normal_user)
        url = reverse("user_update", kwargs={"pk": 1})
        response = client.get(url)
        assert response.status_code == 403

    def test_normal_user_cannot_create_department(self, client, normal_user):
        client.force_login(normal_user)
        url = reverse("department_add")
        response = client.get(url)
        assert response.status_code == 403

    def test_normal_user_cannot_update_department(
        self, client, normal_user, it_department
    ):
        client.force_login(normal_user)
        assert it_department.department_name == "IT"
        url = reverse("department_update", kwargs={"pk": 1})
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_user_can_view_users(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("user_list")
        response = client.get(url)
        assert response.status_code == 200
        user_pk = admin_user.pk
        url = reverse("user_detail", kwargs={"pk": user_pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_user_can_view_departments(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("department_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_user_create_department(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("department_add")

        data = {"department_name": "HR"}
        response = client.post(url, data)

        assert response.status_code == 302

    def test_admin_user_update_department(self, client, admin_user, it_department):
        client.force_login(admin_user)
        assert it_department.department_name == "IT"
        url = reverse("department_update", kwargs={"pk": it_department.pk})

        data = {"department_name": "CFAC"}
        response = client.post(url, data)
        it_department.refresh_from_db()
        assert it_department.department_name == "CFAC"
        assert response.status_code == 302

    def test_admin_user_create_user_view_sets_defaults(
        self, client, admin_user, it_department
    ):
        client.force_login(admin_user)

        # 1. Create a group because the form REQUIRES at least one
        staff_group = Group.objects.create(name="Staff")

        url = reverse("user_create")

        # 2. Add 'groups' to your data dictionary
        data = {
            "username": "new_employee",
            "department": it_department.id,
            "email_address": "test@example.com",
            "groups": [staff_group.id],  # Pass as a list for MultipleChoiceField
        }

        response = client.post(url, data)

        # Debugging helper if it fails again
        if response.status_code == 200:
            print(f"Form Errors: {response.context['form'].errors}")

        assert response.status_code == 302

        # 3. Verify the user was created with the right attributes
        new_user = CustomUser.objects.get(username="new_employee")
        assert new_user.groups.filter(id=staff_group.id).exists()
        assert new_user.reset_password is True
        assert new_user.check_password("united")

    def test_admin_user_update_user_view(self, client, admin_user, it_department):
        # Create an existing user to update
        target_user = CustomUser.objects.create(
            username="update_me",
            department=it_department,
            email_address="old_email@example.com",
        )
        assert target_user.email_address == "old_email@example.com"
        staff_group = Group.objects.create(name="Staff")
        target_user.groups.add(staff_group)

        client.force_login(admin_user)
        url = reverse("user_update", kwargs={"pk": target_user.pk})

        data = {
            "department": it_department.id,
            "groups": [staff_group.id],  # Must be included or form fails
            "email_address": "new_email@example.com",
            "reset_password": True,
        }

        response = client.post(url, data)
        assert response.status_code == 302

        target_user.refresh_from_db()
        assert target_user.email_address == "new_email@example.com"

    def test_admin_user_create_user_duplicate_username(
        self, client, admin_user, it_department
    ):
        # 1. Setup: Create a user that already exists
        CustomUser.objects.create(username="existing_user", department=it_department)
        staff_group = Group.objects.create(name="Staff")

        client.force_login(admin_user)
        url = reverse("user_create")

        # 2. Action: Try to create a second user with the same username
        data = {
            "username": "existing_user",  # Same name as above
            "department": it_department.id,
            "email_address": "different@example.com",
            "groups": [staff_group.id],
        }

        response = client.post(url, data)

        # 3. Assert: It should stay on the page (200 OK) and show an error
        assert response.status_code == 200

        # Check that the form has the specific error for the username field
        form = response.context["form"]
        assert "username" in form.errors
        assert (
            "user with this username already exists"
            in str(form.errors["username"]).lower()
        )

        # Verify a new user was NOT created
        assert CustomUser.objects.filter(username="existing_user").count() == 1


def test_logout_requires_login(client):
    response = client.get(reverse("logout"))
    assert response.status_code == 302  # Redirects to login
