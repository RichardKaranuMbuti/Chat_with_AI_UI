from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    
    path("checkdb/", views.check_database_connection_status, name = "check_db_status"),
    path("chat/", views.process_request, name = "chat_database"),
    path('users/signup/', views.render_signup, name="signup_page"),# render sign up template
    path('users/login/', views.show_login_template, name="show_login"), #login template
    path('chatpage/', views.chat_page, name = 'show_chat_page')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)