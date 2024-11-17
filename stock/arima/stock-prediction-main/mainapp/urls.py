from django.urls import path
from . import views
from .views import CustomLoginView,logout_view

urlpatterns = [
    path('', views.index, name='index'),
    path('news', views.news, name='news'),  # Add name='news' here
    path('visualization/', views.visualize_csv_form, name='visualization'),
    path('data_download/', views.data_download, name='data_download'),
    path('auto_download', views.auto_download, name='auto_download'),
    path('predict', views.predict, name='predict'),
    path('select-symbol/', views.select_symbol, name='select_symbol'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
