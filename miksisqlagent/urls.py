from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path("signup/", views.UserSignup, name = "signup"),
    path("login/", views.login_view, name = "login"),
    path("checkdb/", views.check_database_connection_status, name = "check_db_status"),
    path("chat/", views.process_request, name = "chat_database"),
    
]