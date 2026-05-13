from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegisterView, UserLoginView, GoogleLoginView, UserProfileView,
    UserAddressViewSet, UserAddressDetailView,
    CustomerRequestOTPView, CustomerResetPasswordView, CustomerUpdatePasswordView,
    AdminLoginView, AdminRequestOTPView, AdminResetPasswordView, AdminUpdatePasswordView,
    WriterLoginView, WriterRequestOTPView, WriterResetPasswordView, WriterUpdatePasswordView,
    WriterProfileView,
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
    path('auth/admin/request-otp/', AdminRequestOTPView.as_view(), name='admin-request-otp'),
    path('auth/admin/reset-password/', AdminResetPasswordView.as_view(), name='admin-reset-password'),
    path('auth/admin/update-password/', AdminUpdatePasswordView.as_view(), name='admin-update-password'),

    # Writer auth
    path('auth/writer/login/', WriterLoginView.as_view(), name='writer-login'),
    path('auth/writer/request-otp/', WriterRequestOTPView.as_view(), name='writer-request-otp'),
    path('auth/writer/reset-password/', WriterResetPasswordView.as_view(), name='writer-reset-password'),
    path('auth/writer/update-password/', WriterUpdatePasswordView.as_view(), name='writer-update-password'),

    # Customer (User) auth
    path('auth/user/request-otp/', CustomerRequestOTPView.as_view(), name='customer-request-otp'),
    path('auth/user/reset-password/', CustomerResetPasswordView.as_view(), name='customer-reset-password'),
    path('auth/user/update-password/', CustomerUpdatePasswordView.as_view(), name='customer-update-password'),

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
