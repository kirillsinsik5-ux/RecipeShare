from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
]
