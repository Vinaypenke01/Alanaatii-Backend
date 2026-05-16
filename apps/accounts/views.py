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
            'user': WriterProfileSerializer(result['writer']).data,
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
            'user': AdminSerializer(result['admin']).data,
        })


class OTPRequestView(APIView):
    permission_classes = [AllowAny]
    role = 'admin'

    def post(self, request):
        email = request.data.get('email')
        purpose = request.data.get('purpose', 'reset_password')
        if not email:
            return Response({'error': True, 'message': 'Email is required.'}, status=400)
        services.request_otp(email, self.role, purpose)
        return Response({'message': 'OTP sent to your email.'})


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    role = 'admin'

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        if not all([email, code, new_password]):
            return Response({'error': True, 'message': 'Email, code and new_password are required.'}, status=400)
        services.reset_password_with_otp(email, self.role, code, new_password)
        return Response({'message': 'Password reset successful.'})


class PasswordUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    role = 'admin'

    def post(self, request):
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        if not all([code, new_password]):
            return Response({'error': True, 'message': 'Code and new_password are required.'}, status=400)
        services.update_password_with_otp(request.user.id, self.role, code, new_password)
        return Response({'message': 'Password updated successfully.'})


# ─── Role Specific Implementations ───────────────────────────────────────────

class AdminRequestOTPView(OTPRequestView):
    role = 'admin'

class AdminResetPasswordView(PasswordResetView):
    role = 'admin'

class AdminUpdatePasswordView(PasswordUpdateView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    role = 'admin'

class WriterRequestOTPView(OTPRequestView):
    role = 'writer'

class WriterResetPasswordView(PasswordResetView):
    role = 'writer'

class WriterUpdatePasswordView(PasswordUpdateView):
    permission_classes = [IsAuthenticated, IsWriterUser]
    role = 'writer'

class CustomerRequestOTPView(OTPRequestView):
    role = 'user'

class CustomerResetPasswordView(PasswordResetView):
    role = 'user'

class CustomerUpdatePasswordView(PasswordUpdateView):
    permission_classes = [IsAuthenticated]
    role = 'user'


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
        
        from utils.pagination import StandardPagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = WriterSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        admin = Admin.objects.get(id=request.user.id)
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        if not otp_code:
            return Response({'error': True, 'message': 'Verification code (OTP) is required to onboard a writer.'}, status=400)

        # Verify OTP
        services.verify_otp(email, otp_code, 'create_writer')

        serializer = WriterCreateSerializer(data=request.data, context={'admin': admin})
        serializer.is_valid(raise_exception=True)
        writer = serializer.save()

        # Mark OTP as used
        from .models import OTPVerification
        OTPVerification.objects.filter(email=email, code=otp_code, purpose='create_writer').update(is_verified=True)

        logger.info(f'Admin {admin.email} created writer {writer.email} after OTP verification')
        return Response({
            'message': 'Writer account created and verified.',
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


# ─── Sidebar Stats ────────────────────────────────────────────────────────────
class SidebarStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = {}
            
            # Robust Role Detection
            role = 'user'
            if hasattr(user, 'role'):
                role = 'admin'
            elif hasattr(user, 'status'):
                role = 'writer'
            else:
                role = 'user'

            if role == 'user':
                from apps.orders.models import Order, OrderStatus
                orders = Order.objects.filter(user=user)
                data = {
                    'required_details': orders.filter(status=OrderStatus.AWAITING_DETAILS).count(),
                    'script_review': orders.filter(status=OrderStatus.CUSTOMER_REVIEW).count(),
                }
            elif role == 'writer':
                from apps.writers.models import WriterAssignment
                from apps.orders.models import OrderStatus
                
                assignments = WriterAssignment.objects.filter(writer=user)
                data = {
                    'pending_requests': assignments.filter(status='pending').count(),
                    'active_writing': assignments.filter(
                        status='accepted', 
                        order__status=OrderStatus.ACCEPTED_BY_WRITER
                    ).count(),
                    'pending_revisions': assignments.filter(
                        status='accepted',
                        order__status=OrderStatus.REVISION_REQUESTED
                    ).count(),
                }
            elif role == 'admin':
                from apps.orders.models import Order, OrderStatus, Refund, Transaction
                from apps.admin_ops.models import SupportMessage
                
                data = {
                    'pending_payments': Transaction.objects.filter(status='pending').count(),
                    'pending_scripts': Order.objects.filter(status__in=[
                        OrderStatus.ACCEPTED_BY_WRITER, OrderStatus.REVISION_REQUESTED
                    ]).count(),
                    'pending_support': SupportMessage.objects.filter(status='new').count(),
                    'pending_refunds': Refund.objects.filter(status='pending').count(),
                    'pending_orders': Order.objects.exclude(status__in=[
                        OrderStatus.DELIVERED, 
                        OrderStatus.OUT_FOR_DELIVERY,
                        OrderStatus.CANCELLED,
                        OrderStatus.PAYMENT_PENDING,  # Assuming pending payments are handled separately
                        OrderStatus.PAYMENT_REJECTED
                    ]).count(),
                    'orders_by_type': {
                        'letter': Order.objects.filter(product_type='letter').count(),
                        'letter_paper': Order.objects.filter(product_type='letterPaper').count(),
                        'script': Order.objects.filter(product_type='script').count(),
                    }
                }
            
            return Response(data)
        except Exception as e:
            import traceback
            print(f"DEBUG SidebarStatsError: {str(e)}")
            print(traceback.format_exc())
            return Response({
                "error": True, 
                "message": str(e),
                "traceback": traceback.format_exc() if 'localhost' in request.get_host() else None
            }, status=500)

