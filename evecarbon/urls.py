from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="auth_sso/login.html")),  # or your real homepage
    path("", include("evecarbon.auth_sso.urls")),
]
