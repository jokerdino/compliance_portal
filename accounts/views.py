import pandas as pd

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic import FormView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.hashers import make_password

from django_tables2.views import SingleTableView

from .tables import UserTable, DepartmentTable
from .forms import CustomLoginForm, UserCreateForm, UserUpdateForm, UploadExcelForm
from .models import Department

User = get_user_model()


class DepartmentCreateView(CreateView):
    model = Department
    fields = ["department_name"]
    success_url = reverse_lazy("department_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add new department"
        return context


class DepartmentUpdateView(UpdateView):
    model = Department
    fields = ["department_name"]
    success_url = reverse_lazy("department_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update department"
        return context


class DepartmentListView(SingleTableView):
    model = Department
    table_class = DepartmentTable


class CustomLoginView(LoginView):
    authentication_form = CustomLoginForm
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.reset_password:
            return reverse_lazy("password_reset")
        return reverse_lazy(
            "task_list", kwargs={"filter": "due-today"}
        )  # Or your normal dashboard


class ForcePasswordResetView(LoginRequiredMixin, FormView):
    template_name = "accounts/force_password_reset.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy("task_list", args=["upcoming"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()  # this sets the new password
        user.reset_password = False  # ✅ Clear the flag
        user.save()
        update_session_auth_hash(self.request, user)  # ✅ Keep user logged in
        return super().form_valid(form)


class CustomLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy("login")


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = get_user_model()
    form_class = UserCreateForm
    template_name = "accounts/form.html"
    success_url = reverse_lazy("user_list")

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add new user"
        return context

    def form_valid(self, form):
        # Create the user instance but don't save yet
        user = form.save(commit=False)
        user.reset_password = True
        #  user.username = user.oo_code
        # ✅ Always set password to 'united', hashed
        user.set_password("united")
        # if user.user_type == "RO":
        #    user.is_staff = True
        user.save()
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "accounts/form.html"
    success_url = reverse_lazy("user_list")

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update user"
        return context

    def form_valid(self, form):
        # Create the user instance but don't save yet
        user = form.save(commit=False)
        if user.reset_password:
            # ✅ Always set password to 'united', hashed
            user.set_password("united")

        user.save()
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = get_user_model()
    template_name = "proposal/detail.html"

    def test_func(self):
        return self.request.user.is_staff


class UserListView(
    LoginRequiredMixin, UserPassesTestMixin, SingleTableView
):  ##Mixin, FilterView):
    model = get_user_model()
    table_class = UserTable
    template_name = "accounts/list.html"
    paginate = False

    def test_func(self):
        return self.request.user.is_staff


class UploadExcelView(UserPassesTestMixin, FormView):
    template_name = "accounts/form.html"
    form_class = UploadExcelForm
    success_url = reverse_lazy("user_list")

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        file = form.cleaned_data["file"]

        # ✅ Use pandas to read Excel in memory
        df = pd.read_excel(
            file,
            dtype={"oo_code": str, "ro_code": str, "username": str, "user_type": str},
        )

        # Example: columns must match!
        # username, oo_code, ro_code, user_type
        User = get_user_model()
        existing_usernames = set(User.objects.values_list("username", flat=True))
        users_to_create = []
        password = make_password("united")
        for _, row in df.iterrows():
            username = row["username"]
            if username in existing_usernames:
                continue

            user = User(
                username=row["username"],
                oo_code=row["oo_code"],
                ro_code=row["ro_code"],
                user_type=row["user_type"],
                reset_password=True,
                password=password,
            )
            users_to_create.append(user)

        User.objects.bulk_create(users_to_create)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Bulk upload users"
        return context
