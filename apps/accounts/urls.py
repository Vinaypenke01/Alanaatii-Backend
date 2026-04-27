from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegisterView, UserLoginView, GoogleLoginView, UserProfileView,
    UserAddressViewSet, UserAddressDetailView,
    WriterLoginView, WriterProfileView,
    AdminLoginView,
    AdminWriterListCreateView, AdminWriterDetailView,
    AdminManagementView,
    LogoutView,
)

urlpatterns = [
    # Customer auth
    path('auth/user/register/', UserRegisterView.as_view(), name='user-register'),
    path('auth/user/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/user/google/', GoogleLoginView.as_view(), name='user-google-login'),

    # Writer auth
    path('auth/writer/login/', WriterLoginView.as_view(), name='writer-login'),

    # Admin auth
    path('auth/admin/login/', AdminLoginView.as_view(), name='admin-login'),

    # Token management
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Customer profile & addresses
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('user/addresses/', UserAddressViewSet.as_view(), name='user-addresses'),
    path('user/addresses/<uuid:pk>/', UserAddressDetailView.as_view(), name='user-address-detail'),

    # Writer profile
    path('writer/profile/', WriterProfileView.as_view(), name='writer-profile'),

    # Admin: writer management
    path('admin/writers/', AdminWriterListCreateView.as_view(), name='admin-writer-list'),
    path('admin/writers/<uuid:pk>/', AdminWriterDetailView.as_view(), name='admin-writer-detail'),

    # Admin: admin management
    path('admin/admins/', AdminManagementView.as_view(), name='admin-admin-create'),
]
