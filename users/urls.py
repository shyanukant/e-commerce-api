app_name = 'users'
from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, LogoutView, get_user_profile, update_user_profile

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/details/', get_user_profile, name='profile-details'),
    path('profile/update/', update_user_profile, name='profile-update'),
] 