from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from mainapp.admin import custom_admin_site
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'), 
    path('', include('mainapp.urls')),
    
]

urlpatterns += staticfiles_urlpatterns()
