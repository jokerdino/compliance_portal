from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


from accounts.models import Department, CustomUser
from compliance.models import (
    Task,
    Template,
    RegulatoryPublication,
    TaskRemark,
)
from compliance.tables import TaskTable

from auditlog.context import set_actor


@pytest.fixture
def normal_user(db):
    """Fixture to create a normal user in the accounts app."""
    return CustomUser.objects.create(username="normal_user")


@pytest.fixture
def admin_user(db, admin_user_group):
    user = CustomUser.objects.create(username="admin_staff", is_staff=True)
    user.groups.add(admin_user_group)
    return user


@pytest.fixture
def viewer_user(db, viewer_user_group):
    user = CustomUser.objects.create(username="viewer")
    user.groups.add(viewer_user_group)
    return user


@pytest.fixture
def department_user(db, department_user_group, it_department):
    user = CustomUser.objects.create(username="dept_officer", department=it_department)
    user.groups.add(department_user_group)
    return user


@pytest.fixture
def department_cm_user(db, department_cm_group, it_department):
    user = CustomUser.objects.create(username="dept_cm", department=it_department)
    user.groups.add(department_cm_group)
    return user


@pytest.fixture
def department_dgm_user(db, department_dgm_group, it_department):
    user = CustomUser.objects.create(username="dept_dgm", department=it_department)
    user.groups.add(department_dgm_group)
    return user


@pytest.fixture
def it_department(db):
    """Fixture to create a department in the accounts app."""
    return Department.objects.create(department_name="IT")


@pytest.fixture
def finance_department(db):
    """Fixture to create a department in the accounts app."""
    return Department.objects.create(department_name="Finance")


@pytest.fixture
def admin_user_group(db):
    """Creates a group and attaches compliance permissions."""
    group = Group.objects.create(name="Admin")
    permission_list = [
        "add_publicholiday",
        "add_regulatorypublication",
        "add_task",
        "add_taskremark",
        "add_template",
        "change_regulatorypublication",
        "change_template",
        "view_publicholiday",
        "view_regulatorypublication",
        "view_task",
        "view_template",
        "can_edit_as_compliance",
    ]
    perm = Permission.objects.filter(codename__in=permission_list)
    group.permissions.add(*perm)
    return group


@pytest.fixture
def department_user_group(db):
    """Creates a group and attaches department permissions."""
    group = Group.objects.create(name="Department User")
    permission_list = [
        "add_taskremark",
        "view_regulatorypublication",
        "view_task",
        "can_edit_as_department",
    ]
    perm = Permission.objects.filter(codename__in=permission_list)
    group.permissions.add(*perm)
    return group


@pytest.fixture
def viewer_user_group(db):
    group = Group.objects.create(name="Viewer")
    permission_list = [
        "add_taskremark",
        "can_view_as_compliance",
        "view_publicholiday",
        "view_regulatorypublication",
        "view_task",
        "view_template",
    ]
    perm = Permission.objects.filter(codename__in=permission_list)
    group.permissions.add(*perm)
    return group


@pytest.fixture
def department_cm_group(db):
    group = Group.objects.create(name="Department Chief Manager")
    permission_list = [
        "add_taskremark",
        "can_edit_as_department",
        "can_mark_as_pending",
        "view_regulatorypublication",
        "view_task",
    ]
    perm = Permission.objects.filter(codename__in=permission_list)
    group.permissions.add(*perm)
    return group


@pytest.fixture
def department_dgm_group(db):
    group = Group.objects.create(name="Department DGM")
    permission_list = [
        "add_taskremark",
        "can_edit_as_department",
        "can_mark_as_pending",
        "view_regulatorypublication",
        "view_task",
    ]
    perm = Permission.objects.filter(codename__in=permission_list)
    group.permissions.add(*perm)
    return group


# Define our users for the matrix
USERS = [
    "admin_user",
    "viewer_user",
    "normal_user",
    "department_user",
    "department_cm_user",
    "department_dgm_user",
]


@pytest.mark.django_db
class TestGlobalPermissionMatrix:
    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            # (URL_NAME, { USER: EXPECTED_STATUS })
            (
                "public_holiday_list",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "template_add",
                {
                    "admin_user": 200,
                    "viewer_user": 403,
                    "normal_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_add",
                {
                    "admin_user": 200,
                    "viewer_user": 403,
                    "normal_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "template_list",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "upload_public_holidays",
                {
                    "admin_user": 200,
                    "viewer_user": 403,
                    "normal_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "publication_list",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
            (
                "publication_create",
                {
                    "admin_user": 200,
                    "viewer_user": 403,
                    "normal_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user", USERS)
    def test_url_access_by_role(self, request, client, user, url_name, expectations):
        # 1. Get the actual user object from the fixture name
        login_user = request.getfixturevalue(user)
        client.force_login(login_user)

        # 2. Get the expected status for this specific role
        # Default to 403 if the role isn't explicitly defined in the map
        expected_status = expectations.get(user, 403)

        url = reverse(url_name)
        response = client.get(url)

        assert response.status_code == expected_status, (
            f"User {user} expected {expected_status} on {url_name} but got {response.status_code}"
        )

    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            (
                "task_edit",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
            (
                "task_detail",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 200,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user", USERS)
    def test_task_permission_logic_same_dept(
        self, request, client, user, url_name, expectations, it_department
    ):
        login_user = request.getfixturevalue(user)

        with set_actor(login_user):
            task = Task.objects.create(task_name="IT Task", department=it_department)

        client.force_login(login_user)
        url = reverse(url_name, kwargs={"pk": task.pk})
        response = client.get(url)

        assert response.status_code == expectations.get(user)

    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            (
                "task_edit",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_detail",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 200,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user", USERS)
    def test_task_permission_logic_diff_dept(
        self, request, client, user, url_name, expectations, finance_department
    ):
        login_user = request.getfixturevalue(user)

        with set_actor(login_user):
            task = Task.objects.create(
                task_name="IT Task", department=finance_department
            )

        client.force_login(login_user)
        url = reverse(url_name, kwargs={"pk": task.pk})
        response = client.get(url)

        assert response.status_code == expectations.get(user)

    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            (
                "template_duplicate",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "template_edit",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_create_from_template",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "template_detail",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 200,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user", USERS)
    def test_template_permission_logic(
        self, request, client, user, url_name, expectations, it_department
    ):
        # client.force_login(viewer_user)
        login_user = request.getfixturevalue(user)
        client.force_login(login_user)

        template = Template.objects.create(
            task_name="Test Template", department=it_department
        )

        url = reverse(url_name, kwargs={"pk": template.pk})
        response = client.get(url)
        assert response.status_code == expectations.get(user)

    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            (
                "publication_update",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "publication_detail",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 200,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user", USERS)
    def test_publication_permission_logic(
        self, request, client, user, url_name, expectations
    ):
        login_user = request.getfixturevalue(user)
        client.force_login(login_user)

        publication = RegulatoryPublication.objects.create(
            title="Generic Publication",
            category="REGULATIONS",
            effective_from=timezone.now(),
            date_of_publication=timezone.now(),
        )

        url = reverse(url_name, kwargs={"pk": publication.pk})
        response = client.get(url)
        assert response.status_code == expectations.get(user)

    @pytest.mark.parametrize("is_same_dept", [True, False])
    @pytest.mark.parametrize(
        "url_name, start_status, end_status, same_dept_expects, diff_dept_expects",
        [
            (
                "task_remarks",
                "review",
                "review",  # Remarks don't change status
                {
                    "admin_user": 302,
                    "normal_user": 403,
                    "viewer_user": 302,
                    "department_user": 302,
                    "department_cm_user": 302,
                    "department_dgm_user": 302,
                },
                {
                    "admin_user": 302,
                    "normal_user": 403,
                    "viewer_user": 302,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_remarks",
                "submitted",
                "submitted",  # cannot add remarks when status is submitted
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_revise",
                "review",
                "revision",  # Moves from review -> revision
                {
                    "admin_user": 302,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
                {
                    "admin_user": 302,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_revise",
                "submitted",
                "revision",  # Moves from submitted -> revision
                {
                    "admin_user": 302,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
                {
                    "admin_user": 302,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_revise",
                "pending",
                "pending",  # revise only moves from submitted / review to revision
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_approve",
                "to_be_approved",
                "review",  # Moves to review status
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 302,
                    "department_dgm_user": 302,
                },
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_approve",
                "submitted",
                "submitted",  # task approve only works if status is in to_be_approved
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_pending",
                "to_be_approved",
                "pending",  # Moves to pending status
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 302,
                    "department_dgm_user": 302,
                },
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
            (
                "task_pending",
                "pending",
                "pending",  # task_pending only works if status in to_be_approved
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
                {
                    "admin_user": 403,
                    "normal_user": 403,
                    "viewer_user": 403,
                    "department_user": 403,
                    "department_cm_user": 403,
                    "department_dgm_user": 403,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user_fixture", USERS)
    def test_task_post_permission_logic(
        self,
        request,
        client,
        user_fixture,
        url_name,
        start_status,
        end_status,
        same_dept_expects,
        diff_dept_expects,
        is_same_dept,
        it_department,
        finance_department,
    ):
        login_user = request.getfixturevalue(user_fixture)
        # login_user.department = it_department
        # login_user.save()

        task_dept = it_department if is_same_dept else finance_department

        # 1. Initialize Task with the required start_status for this specific test case
        task = Task.objects.create(
            task_name="Test Task", department=task_dept, current_status=start_status
        )
        initial_remark_count = TaskRemark.objects.filter(task=task).count()

        client.force_login(login_user)
        url = reverse(url_name, kwargs={"pk": task.pk})
        remark_text = "Verification Remark"
        response = client.post(url, {"remark": remark_text})

        # 2. Resolve Expectations
        expectations = same_dept_expects if is_same_dept else diff_dept_expects
        expected_http_status = expectations.get(user_fixture)

        assert response.status_code == expected_http_status

        # 3. Comprehensive Database Check
        task.refresh_from_db()
        if expected_http_status == 302:
            # Check Status Transition
            assert task.current_status == end_status, (
                f"Status should have moved to {end_status}"
            )

            assert (
                TaskRemark.objects.filter(task=task).count() == initial_remark_count + 1
            )
            latest_remark = TaskRemark.objects.filter(task=task).latest("created_at")
            assert latest_remark.text == remark_text
            assert latest_remark.created_by == login_user
        else:
            # If 403, nothing should have changed
            assert task.current_status == start_status
            assert TaskRemark.objects.filter(task=task).count() == initial_remark_count

    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            (
                "task_list_approval_pending",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
            (
                "task_list_review",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
            (
                "task_list_revision",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
            (
                "task_list_submitted",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
            (
                "task_list_board_meeting_pending",
                {
                    "admin_user": 200,
                    "viewer_user": 200,
                    "normal_user": 403,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            ),
        ],
    )
    @pytest.mark.parametrize("user_fixture", USERS)
    def test_task_list_permission_logic(
        self, request, client, user_fixture, url_name, expectations
    ):
        login_user = request.getfixturevalue(user_fixture)
        client.force_login(login_user)

        # 2. Get the expected status for this specific role
        # Default to 403 if the role isn't explicitly defined in the map
        expected_status = expectations.get(user_fixture, 403)

        url = reverse(url_name)
        response = client.get(url)

        assert response.status_code == expected_status, (
            f"User {user_fixture} expected {expected_status} on {url_name} but got {response.status_code}"
        )

    @pytest.mark.parametrize("filter", ["overdue", "due-today", "upcoming"])
    @pytest.mark.parametrize(
        "url_name, expectations",
        [
            (
                "task_list",
                {
                    "admin_user": 200,
                    "normal_user": 403,
                    "viewer_user": 200,
                    "department_user": 200,
                    "department_cm_user": 200,
                    "department_dgm_user": 200,
                },
            )
        ],
    )
    @pytest.mark.parametrize("user_fixture", USERS)
    def test_task_list_filtered_permission_logic(
        self, request, client, user_fixture, url_name, filter, expectations
    ):
        login_user = request.getfixturevalue(user_fixture)
        client.force_login(login_user)

        # 2. Get the expected status for this specific role
        # Default to 403 if the role isn't explicitly defined in the map
        expected_status = expectations.get(user_fixture, 403)

        url = reverse(url_name, kwargs={"filter": filter})
        response = client.get(url)

        assert response.status_code == expected_status, (
            f"User {user_fixture} expected {expected_status} on {url_name} but got {response.status_code}"
        )


@pytest.mark.django_db
class TestTaskUI:
    @pytest.mark.parametrize(
        "status, status_label",
        [
            ("pending", "Pending"),
            ("to_be_approved", "To be approved"),
            ("review", "In review"),
            ("revision", "Revised document to be uploaded"),
            ("submitted", "Submitted"),
        ],
    )
    @pytest.mark.parametrize("user_fixture", USERS)
    def test_task_status_user_interface(
        self, request, client, user_fixture, it_department, status, status_label
    ):
        login_user = request.getfixturevalue(user_fixture)
        client.force_login(login_user)
        with set_actor(login_user):
            task = Task.objects.create(
                task_name="Test Task",
                due_date=timezone.now(),
                current_status=status,
                department=it_department,
            )
        url = reverse("task_detail", kwargs={"pk": task.pk})
        response = client.get(url)
        edit_button = ' <i class="bi bi-pencil-square"></i> Edit Task'
        remarks_button = ' <i class="bi bi-chat-left-text"></i> Add remarks'
        if user_fixture == "normal_user":
            assert response.status_code == 403
        else:
            assert response.status_code == 200
            assert status_label in response.content.decode()
            if status != "submitted":
                assert remarks_button in response.content.decode()
            else:
                assert remarks_button not in response.content.decode()

        if user_fixture == "admin_user" and status in ["submitted", "review"]:
            assert "Revision required" in response.content.decode()
        elif (
            user_fixture in ["department_cm_user", "department_dgm_user"]
            and status == "to_be_approved"
        ):
            assert "Revision required" in response.content.decode()
        else:
            assert "Revision required" not in response.content.decode()
        if user_fixture == "admin_user":
            if status not in ["submitted"]:
                assert edit_button in response.content.decode()
            else:
                assert edit_button not in response.content.decode()
        if user_fixture in [
            "department_user",
            "department_cm_user",
            "department_dgm_user",
        ]:
            if status in ["pending", "revision"]:
                assert edit_button in response.content.decode()
            else:
                assert edit_button not in response.content.decode()

        if user_fixture in ["department_cm_user", "department_dgm-user"]:
            if status in ["to_be_approved"]:
                assert "Approve" in response.content.decode()
                assert "Revision required" in response.content.decode()
            else:
                assert "Approve" not in response.content.decode()
                assert "Revision required" not in response.content.decode()

    @pytest.mark.parametrize(
        "user_fixture", ["department_user", "department_cm_user", "department_dgm_user"]
    )
    def test_task_overdue_form_submission_without_delay_remark(
        self, request, client, user_fixture, it_department
    ):
        login_user = request.getfixturevalue(user_fixture)
        client.force_login(login_user)
        with set_actor(login_user):
            task = Task.objects.create(
                task_name="Test Task",
                due_date=timezone.now() - timedelta(days=1),
                current_status="pending",
                department=it_department,
            )
            # 2. Mock a file upload but provide NO reason_for_delay
        fake_file = SimpleUploadedFile(
            "test_doc.pdf", b"file_content", content_type="application/pdf"
        )
        data = {
            "data_document": fake_file,
            "reason_for_delay": "",  # Explicitly empty
        }
        url = reverse("task_edit", kwargs={"pk": task.pk})
        response = client.post(url, data=data)

        # response = client.post(url)
        delay_remark = "Reason for delay is required because the task is overdue."
        assert response.status_code == 200
        assert delay_remark in response.content.decode()

    @pytest.mark.parametrize(
        "user_fixture", ["department_user", "department_cm_user", "department_dgm_user"]
    )
    def test_task_overdue_form_submission_with_delay_remark(
        self, request, client, user_fixture, it_department
    ):
        login_user = request.getfixturevalue(user_fixture)
        client.force_login(login_user)

        # 1. Setup Task
        with set_actor(login_user):
            task = Task.objects.create(
                task_name="Test Task",
                due_date=timezone.now().date() - timedelta(days=2),
                current_status="pending",
                department=it_department,
            )

        url = reverse("task_edit", kwargs={"pk": task.pk})

        # 2. GET the page first to see what Django wants
        get_response = client.get(url)
        formset = get_response.context["remarks_formset"]
        prefix = formset.prefix  # This will likely be 'taskremark_set'

        # 3. Build the data using that prefix
        fake_file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )

        data = {
            "data_document": fake_file,
            "reason_for_delay": "Valid Reason",
            # Management data using the dynamic prefix
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-text": "Some remark",
        }

        # 4. POST the data
        response = client.post(url, data=data)

        assert response.status_code == 302

    @pytest.mark.parametrize(
        "user_fixture", ["department_user", "department_cm_user", "department_dgm_user"]
    )
    def test_task_overdue_form_submission_upcoming_without_delay_remark(
        self, request, client, user_fixture, it_department
    ):
        login_user = request.getfixturevalue(user_fixture)
        client.force_login(login_user)

        # 1. Setup Task
        with set_actor(login_user):
            task = Task.objects.create(
                task_name="Test Task",
                due_date=timezone.now().date() + timedelta(days=2),
                current_status="pending",
                department=it_department,
            )

        url = reverse("task_edit", kwargs={"pk": task.pk})

        # 2. GET the page first to see what Django wants
        get_response = client.get(url)
        formset = get_response.context["remarks_formset"]
        prefix = formset.prefix  # This will likely be 'taskremark_set'

        # 3. Build the data using that prefix
        fake_file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )

        data = {
            "data_document": fake_file,
            # Management data using the dynamic prefix
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-text": "Some remark",
        }

        # 4. POST the data
        response = client.post(url, data=data)

        assert response.status_code == 302


@pytest.mark.django_db
class TestAdminBasedPermissions:
    def test_admin_user_can_create_template(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("template_add")
        response = client.get(url)
        assert response.status_code == 200
        assert admin_user.has_perm("compliance.add_template")


@pytest.mark.django_db
class TestViewerBasedPermissions:
    def test_viewer_user_can_view_public_holidays(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("public_holiday_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_cannot_create_template(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("template_add")
        response = client.get(url)
        assert response.status_code == 403
        assert not viewer_user.has_perm("compliance.add_template")

    def test_viewer_user_cannot_edit_template(self, client, viewer_user, it_department):
        client.force_login(viewer_user)

        template = Template.objects.create(
            task_name="Test Template", department=it_department
        )

        url = reverse("template_edit", kwargs={"pk": template.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_cannot_duplicate_template(
        self, client, viewer_user, it_department
    ):
        client.force_login(viewer_user)

        template = Template.objects.create(
            task_name="Test Template", department=it_department
        )

        url = reverse("template_duplicate", kwargs={"pk": template.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_can_view_templates(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("template_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_cannot_create_task(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_add")
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_cannot_create_task_from_template(
        self, client, viewer_user, it_department
    ):
        client.force_login(viewer_user)

        template = Template.objects.create(
            task_name="Test Template", department=it_department
        )

        url = reverse("task_create_from_template", kwargs={"pk": template.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_cannot_edit_task(self, client, viewer_user, it_department):
        client.force_login(viewer_user)

        with set_actor(viewer_user):
            task = Task.objects.create(
                task_name="Generic Task",
                department=it_department,
                current_status="pending",
            )

        url = reverse("task_edit", kwargs={"pk": task.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_can_view_task(self, client, it_department, viewer_user):
        client.force_login(viewer_user)
        assert viewer_user.has_perm("compliance.view_task")
        assert viewer_user.has_perm("compliance.can_view_as_compliance")

        with set_actor(viewer_user):
            task = Task.objects.create(
                task_name="Generic Task",
                department=it_department,
                current_status="pending",
            )

        url = reverse("task_detail", kwargs={"pk": task.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_can_view_template_list(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("template_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_can_view_submitted_task_list(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_list", kwargs={"filter": "submitted"})
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_can_view_revision_task_list(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_list", kwargs={"filter": "revision"})
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_can_view_review_task_list(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_list", kwargs={"filter": "review"})
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_can_view_approval_pending_task_list(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_list", kwargs={"filter": "to_be_approved"})
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_user_can_view_pending_task_list(
        self, client, viewer_user, it_department
    ):
        client.force_login(viewer_user)
        overdue_task = Task.objects.create(
            task_name="Overdue Task",
            department=it_department,
            current_status="pending",
            due_date=timezone.now() - timedelta(days=2),
        )
        due_today_task = Task.objects.create(
            task_name="Due Today Task",
            department=it_department,
            current_status="pending",
            due_date=timezone.now(),
        )
        upcoming_task = Task.objects.create(
            task_name="Upcoming Task",
            department=it_department,
            current_status="pending",
            due_date=timezone.now() + timedelta(days=2),
        )
        overdue_url = reverse("task_list", kwargs={"filter": "overdue"})
        due_today_url = reverse("task_list", kwargs={"filter": "due-today"})
        upcoming_url = reverse("task_list", kwargs={"filter": "upcoming"})

        overdue_response = client.get(overdue_url)
        assert overdue_response.status_code == 200

        due_today_response = client.get(due_today_url)
        assert due_today_response.status_code == 200

        upcoming_response = client.get(upcoming_url)
        assert upcoming_response.status_code == 200
        # Check Overdue Task
        assert overdue_task in overdue_response.context["object_list"]
        assert upcoming_task not in overdue_response.context["object_list"]
        assert due_today_task not in overdue_response.context["object_list"]
        # Verify the task name appears in the HTML bytes
        assert "Overdue Task" in overdue_response.content.decode()

        # Check Due Today Task
        assert due_today_task in due_today_response.context["object_list"]
        assert upcoming_task not in due_today_response.context["object_list"]
        assert overdue_task not in due_today_response.context["object_list"]
        assert "Due Today Task" in due_today_response.content.decode()
        # Check Upcoming Task
        assert upcoming_task in upcoming_response.context["object_list"]
        assert due_today_task not in upcoming_response.context["object_list"]
        assert overdue_task not in upcoming_response.context["object_list"]
        assert "Upcoming Task" in upcoming_response.content.decode()

    @pytest.mark.parametrize(
        "task_filter", ["submitted", "revision", "review", "to_be_approved", "overdue"]
    )
    def test_task_list_filters_accessible(self, client, viewer_user, task_filter):
        client.force_login(viewer_user)
        url = reverse("task_list", kwargs={"filter": task_filter})
        assert client.get(url).status_code == 200

    def test_viewer_user_can_view_board_meeting_list(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_list_board_meeting_pending")
        response = client.get(url)
        assert response.status_code == 200

    def test_viewer_cannot_upload_public_holidays(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("upload_public_holidays")
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_cannot_mark_task_revision(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_revise", kwargs={"pk": 1})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_cannot_mark_task_pending(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_pending", kwargs={"pk": 1})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_cannot_mark_task_approved(self, client, viewer_user):
        client.force_login(viewer_user)
        url = reverse("task_approve", kwargs={"pk": 1})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_add_taskremark_success(
        self, client, viewer_user, it_department
    ):
        client.force_login(viewer_user)

        task = Task.objects.create(
            task_name="Generic Task", department=it_department, current_status="pending"
        )

        url = reverse("task_remarks", kwargs={"pk": task.pk})
        remark_text = "This is a test remark"
        response = client.post(url, {"remark": remark_text})

        # 1. Check redirect to task_detail
        assert response.status_code == 302
        assert response.url == reverse("task_detail", kwargs={"pk": task.pk})

        # 2. Check DB state
        remark = TaskRemark.objects.get(task=task)
        assert remark.text == remark_text
        assert remark.created_by == viewer_user

    def test_viewer_user_cannot_create_regulatory_publication(
        self, client, viewer_user
    ):
        client.force_login(viewer_user)
        url = reverse("publication_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_cannot_edit_regulatory_publication(self, client, viewer_user):
        client.force_login(viewer_user)
        publication = RegulatoryPublication.objects.create(
            title="Generic Publication",
            category="REGULATIONS",
            effective_from=timezone.now(),
            date_of_publication=timezone.now(),
        )
        url = reverse("publication_update", kwargs={"pk": publication.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_viewer_user_can_view_regulatory_publications(self, client, viewer_user):
        client.force_login(viewer_user)
        publication = RegulatoryPublication.objects.create(
            title="Generic Publication",
            category="REGULATIONS",
            effective_from=timezone.now(),
            date_of_publication=timezone.now(),
        )

        url = reverse("publication_list")
        response = client.get(url)
        assert response.status_code == 200
        assert publication in response.context["object_list"]
        url = reverse("publication_detail", kwargs={"pk": publication.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Generic Publication" in response.content.decode()


@pytest.mark.django_db
class TestBulkBoardMeetingView:
    def test_authorized_user_bulk_set_date_success(
        self, client, admin_user, it_department
    ):
        """Verify compliance user can bulk update tasks needing board dates."""
        client.force_login(admin_user)
        template = Template.objects.create(
            task_name="Generic Template",
            type_of_due_date="board_meeting",
            department=it_department,
        )
        # 1. Setup tasks that require board dates
        task1 = Task.objects.create(
            task_name="Meeting Task 1",
            department=it_department,
            board_meeting_date_flag=False,
            template=template,
            # Ensure template matches the type_of_due_date logic in your view
        )
        # Manually setting template properties if not using fixtures for them:
        # task1.template.type_of_due_date = "board_meeting"
        # task1.template.save()

        url = reverse("task_board_meeting_bulk")
        meeting_date = timezone.now().date() + timedelta(days=10)

        data = {
            "task_ids": f"{task1.id}",
            "board_meeting_date": meeting_date,
        }

        response = client.post(url, data)

        # Assertions
        assert response.status_code == 302
        assert response.url == reverse("task_list_board_meeting_pending")

        task1.refresh_from_db()
        assert task1.board_meeting_date == meeting_date
        assert task1.board_meeting_date_flag is True

    def test_unauthorized_user_is_forbidden(self, client, viewer_user, it_department):
        """Verify user without correct perm gets a 403."""
        client.force_login(viewer_user)

        task = Task.objects.create(task_name="Secured Task", department=it_department)
        url = reverse("task_board_meeting_bulk")

        # Even with valid data, the permission check happens first
        response = client.post(
            url, {"task_ids": f"{task.id}", "board_meeting_date": "2026-12-31"}
        )

        assert response.status_code == 403

    def test_bulk_set_date_invalid_data(self, client, admin_user):
        """Verify redirect and error message on empty task list."""
        client.force_login(admin_user)
        url = reverse("task_board_meeting_bulk")

        # Sending POST with empty task_ids
        response = client.post(
            url, {"task_ids": "", "board_meeting_date": "2026-12-31"}
        )

        assert response.status_code == 302
        # Verify it redirects back to the pending list
        assert response.url == reverse("task_list_board_meeting_pending")

        # Optional: Check if the error message is in the session
        messages = list(response.wsgi_request._messages)
        assert any("Invalid submission" in m.message for m in messages)

    @pytest.mark.parametrize(
        "due_date_type, expected_name",
        [
            ("board_meeting", "Standard Task"),
            ("board_meeting_conditional", "Conditional Task"),
        ],
    )
    def test_bulk_set_date_logic_types(
        self, client, admin_user, it_department, due_date_type, expected_name
    ):
        client.force_login(admin_user)
        template = Template.objects.create(
            task_name="Generic Template",
            type_of_due_date="board_meeting",
            department=it_department,
        )

        # Setup: Create a task based on the current parameter
        task = Task.objects.create(
            task_name=expected_name,
            department=it_department,
            board_meeting_date_flag=False,
            template=template,
        )
        # Configure the template type according to the parameter
        # task.template.type_of_due_date = due_date_type
        # task.template.save()

        url = reverse("task_board_meeting_bulk")
        data = {
            "task_ids": str(task.id),
            "board_meeting_date": "2026-12-31",
        }

        client.post(url, data)
        task.refresh_from_db()

        # Verification
        assert task.board_meeting_date_flag is True
        assert str(task.board_meeting_date) == "2026-12-31"


@pytest.mark.django_db
class TestTaskRemarksFunction:
    def test_add_remark_anonymous_redirects(self, client, it_department):
        """Verify unlogged users are redirected to login."""
        task = Task.objects.create(task_name="Test Task", department=it_department)
        url = reverse("task_remarks", kwargs={"pk": task.pk})

        response = client.post(url, {"remark": "Should fail"})

        assert response.status_code == 302
        assert "login" in response.url

    def test_add_remark_get_request_forbidden(self, client, admin_user, it_department):
        """Verify GET requests return 403 as per your view logic."""
        client.force_login(admin_user)
        task = Task.objects.create(task_name="Test Task", department=it_department)
        url = reverse("task_remarks", kwargs={"pk": task.pk})

        response = client.get(url)

        # Your view explicitly returns HttpResponseForbidden for non-POST
        assert response.status_code == 403

    def test_add_remark_no_permission(self, client, normal_user, it_department):
        """Verify logged in user without specific permission is redirected."""
        client.force_login(normal_user)
        task = Task.objects.create(task_name="Test Task", department=it_department)
        url = reverse("task_remarks", kwargs={"pk": task.pk})

        response = client.post(url, {"remark": "No perms"})

        assert response.status_code == 403


@pytest.mark.django_db
class TestGroupBasedPermissions:
    def test_compliance_group_can_edit_any_task(self, admin_user_group, it_department):
        """Verify Group members can edit tasks they don't own."""
        user = CustomUser.objects.create(username="compliance_admin")
        user.groups.add(admin_user_group)

        task = Task.objects.create(
            task_name="Generic Task", department=it_department, current_status="pending"
        )

        # Test: Compliance user has no user_type, but is in the Group
        assert user.has_perm("compliance.can_edit_as_compliance")
        assert task.can_edit(user) is True

    def test_department_group_restricted_by_dept(
        self, department_user_group, it_department
    ):
        """Verify Group members are still restricted by their department ID."""
        user = CustomUser.objects.create(username="dept_user", department=it_department)
        user.groups.add(department_user_group)

        # Task in SAME department
        own_task = Task.objects.create(
            task_name="Our Task", department=it_department, current_status="pending"
        )

        # Task in DIFFERENT department
        other_dept = Department.objects.create(department_name="HR")
        other_task = Task.objects.create(
            task_name="Other Task", department=other_dept, current_status="pending"
        )

        assert own_task.can_edit(user) is True
        assert other_task.can_edit(user) is False


@pytest.mark.django_db
class TestTaskCrossAppLogic:
    def test_task_belongs_to_accounts_department(self, it_department, department_user):
        """
        Verify that a Task in the 'compliance' app correctly links
        to a Department in the 'accounts' app.
        """
        task = Task.objects.create(
            task_name="Cross-App Test Task",
            department=it_department,  # Link to accounts.Department
            current_status="pending",
        )

        # Test the custom logic in your compliance.Task model
        assert task.department.department_name == "IT"
        assert task.can_edit(department_user) is True

    def test_priority_rendering_logic(self, it_department):
        """Checks the render_priority method in TaskTable."""
        task = Task.objects.create(
            task_name="Priority Test",
            priority=2,  # Medium
            department=it_department,
        )

        table = TaskTable([task])
        # value 'Medium' comes from the choices mapping (2, "Medium")
        html = table.render_priority(value="Medium", record=task)

        # Based on your HTML: elif record.priority == 2: bg-warning text-dark
        assert "bg-warning" in html
        assert "text-dark" in html
        assert "Medium" in html


@pytest.mark.django_db
class TestTaskPermissions:
    def test_can_edit_as_department_success(self, department_user):
        task = Task.objects.create(
            task_name="Monthly Report",
            department=department_user.department,
            current_status="pending",  # Editable status
        )
        assert task.can_edit(department_user) is True

    def test_can_edit_as_department_wrong_status(self, department_user):
        task = Task.objects.create(
            task_name="Monthly Report",
            department=department_user.department,
            current_status="submitted",  # Non-editable for dept
        )
        assert task.can_edit(department_user) is False

    def test_can_request_revision_compliance_only(self, admin_user, department_user):
        task = Task.objects.create(
            task_name="Review Task",
            department=department_user.department,
            current_status="review",
        )
        # Compliance should be able to request revision
        assert task.can_request_revision(admin_user) is True
        # Department user should NOT
        assert task.can_request_revision(department_user) is False

    def test_is_overdue(self):
        past_task = Task(due_date=timezone.now().date() - timedelta(days=1))
        future_task = Task(due_date=timezone.now().date() + timedelta(days=1))

        assert past_task.is_overdue() is True
        assert future_task.is_overdue() is False


@pytest.mark.django_db
def test_task_table_priority_rendering():
    dept = Department.objects.create(department_name="Finance")
    task = Task.objects.create(
        task_name="High Priority Task",
        priority=3,  # Should be bg-danger
        department=dept,
    )

    table = TaskTable([task])
    # Get the HTML for the priority column of the first row
    html = table.render_priority(value="High", record=task)

    assert "bg-danger" in html
    assert "High" in html
    assert "fs-6" in html


@pytest.mark.django_db
def test_user_without_legacy_type_can_still_edit(admin_user_group, it_department):
    # Notice we don't set user_type at all here
    clean_user = CustomUser.objects.create(username="modern_user")
    clean_user.groups.add(admin_user_group)

    task = Task.objects.create(
        task_name="Modernization Test",
        department=it_department,
        current_status="review",
    )

    # If this passes, you know your can_edit logic is purely permission-based!
    assert task.can_edit(clean_user) is True
