"""
Accounts views — thin controllers that delegate to services.
"""
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from utils.permissions import IsAdminUser, IsCustomerUser, IsWriterUser
from .models import UserAddress, Writer, Admin
from .serializers import (
    UserRegisterSerializer, UserProfileSerializer, UserAddressSerializer,
    WriterSerializer, WriterCreateSerializer, WriterUpdateSerializer, WriterProfileSerializer,
    AdminSerializer, AdminCreateSerializer,
    GoogleLoginSerializer,
    get_tokens_for_user,
)
from . import services

logger = logging.getLogger('apps')


# ─── Customer Auth ────────────────────────────────────────────────────────────

class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        if not settings.AUTH_MODE_PASSWORD:
            return Response({
                'error': True,
                'code': 'AUTH_MODE_DISABLED',
                'message': 'Password registration is disabled. Please use Google Sign-In.',
                'google_endpoint': '/api/v1/auth/user/google/',
            }, status=status.HTTP_403_FORBIDDEN)

        result = services.register_user(request.data)
        user = result['user']
        return Response({
            'message': 'Account created successfully.',
            'tokens': result['tokens'],
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        if not settings.AUTH_MODE_PASSWORD:
            return Response({
                'error': True,
                'code': 'AUTH_MODE_DISABLED',
                'message': 'Password login is disabled. Please use Google Sign-In.',
                'google_endpoint': '/api/v1/auth/user/google/',
            }, status=status.HTTP_403_FORBIDDEN)

        result = services.login_user(
            request.data.get('email', ''),
            request.data.get('password', ''),
        )
        return Response({
            'message': 'Login successful.',
            'tokens': result['tokens'],
            'user': UserProfileSerializer(result['user']).data,
        })


class GoogleLoginView(APIView):
    """
    POST /api/v1/auth/user/google/
    Body: { "id_token": "<google_id_token_from_frontend>" }

    The frontend uses the Google Sign-In SDK to get an id_token after the user
    clicks 'Continue with Google'. That token is sent here, verified server-side
    against Google's public keys, and your platform JWT is returned.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        if settings.AUTH_MODE_PASSWORD:
            return Response({
                'error': True,
                'code': 'AUTH_MODE_DISABLED',
                'message': 'Google OAuth is disabled. Please use email and password to log in.',
                'login_endpoint': '/api/v1/auth/user/login/',
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        is_new = serializer.validated_data.get('is_new', False)
        tokens = get_tokens_for_user(user, role='user')

        logger.info(f'Google OAuth {"register" if is_new else "login"}: {user.email}')
        return Response({
            'message': 'Google login successful.',
            'is_new_account': is_new,
            'tokens': tokens,
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED if is_new else status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UserAddressViewSet(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request):
        addresses = UserAddress.objects.filter(user=request.user)
        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserAddressDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def _get_address(self, pk, user):
        from rest_framework.exceptions import NotFound, PermissionDenied
        try:
            addr = UserAddress.objects.get(pk=pk)
        except UserAddress.DoesNotExist:
            raise NotFound('Address not found.')
        if addr.user != user:
            raise PermissionDenied('You cannot access this address.')
        return addr

    def get(self, request, pk):
        addr = self._get_address(pk, request.user)
        return Response(UserAddressSerializer(addr).data)

    def put(self, request, pk):
        addr = self._get_address(pk, request.user)
        serializer = UserAddressSerializer(addr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        addr = self._get_address(pk, request.user)
        addr.delete()
        return Response({'message': 'Address deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ─── Writer Auth ──────────────────────────────────────────────────────────────

class WriterLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        result = services.login_writer(
            request.data.get('email', ''),
            request.data.get('password', ''),
        )
        return Response({
            'message': 'Login successful.',
            'tokens': result['tokens'],
            'writer': WriterProfileSerializer(result['writer']).data,
        })


class WriterProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsWriterUser]
    serializer_class = WriterProfileSerializer

    def get_object(self):
        return self.request.user


# ─── Admin Auth ───────────────────────────────────────────────────────────────

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        result = services.login_admin(
            request.data.get('email', ''),
            request.data.get('password', ''),
        )
        return Response({
            'message': 'Login successful.',
            'tokens': result['tokens'],
            'admin': AdminSerializer(result['admin']).data,
        })


# ─── Admin: Writer Management ─────────────────────────────────────────────────

class AdminWriterListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = Writer.objects.all().order_by('-created_at')
        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(full_name__icontains=search) | qs.filter(email__icontains=search)
        serializer = WriterSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        admin = Admin.objects.get(id=request.user.id)
        serializer = WriterCreateSerializer(data=request.data, context={'admin': admin})
        serializer.is_valid(raise_exception=True)
        writer = serializer.save()
        logger.info(f'Admin {admin.email} created writer {writer.email}')
        return Response({
            'message': 'Writer account created.',
            'writer': WriterSerializer(writer).data,
        }, status=status.HTTP_201_CREATED)


class AdminWriterDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        writer = services.get_writer_by_id(pk)
        return Response(WriterSerializer(writer).data)

    def put(self, request, pk):
        writer = services.get_writer_by_id(pk)
        serializer = WriterUpdateSerializer(writer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Writer updated.',
            'writer': WriterSerializer(writer).data,
        })

    def delete(self, request, pk):
        admin = Admin.objects.get(id=request.user.id)
        services.delete_writer(pk, admin)
        return Response({'message': 'Writer deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ─── Admin: Admin Management ──────────────────────────────────────────────────

class AdminManagementView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """Create a new admin account (super_admin only)."""
        requesting_admin = Admin.objects.get(id=request.user.id)
        if requesting_admin.role != 'super_admin':
            return Response({'error': True, 'message': 'Only super admins can create admin accounts.'}, status=403)
        serializer = AdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response(AdminSerializer(admin).data, status=status.HTTP_201_CREATED)


# ─── Token Logout ─────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                # Only User tokens are in OutstandingToken; Writer/Admin are not —
                # blacklist() may raise for untracked tokens, which is fine.
                token.blacklist()
        except Exception:
            pass  # Token not tracked or already blacklisted — treat as logged out
        return Response({'message': 'Logged out successfully.'})

