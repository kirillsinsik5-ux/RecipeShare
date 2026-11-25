from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/<int:user_id>/', views.profile_edit_view, name='profile_edit'),
    path('moderation/', views.moderation_dashboard_view, name='moderation'),
    path('moderation/toggle/<int:user_id>/', views.toggle_active_view, name='toggle_active'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
]
