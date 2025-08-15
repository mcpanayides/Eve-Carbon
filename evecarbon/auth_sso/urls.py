from django.urls import path
from .views import eve_login, eve_callback, logout_view, landing

app_name = "auth_sso"

urlpatterns = [
    path("", landing, name="landing"),
    path("login/", eve_login, name="login"),
    path("sso/callback/", eve_callback, name="callback"),
    path("logout/", logout_view, name="logout"),
]