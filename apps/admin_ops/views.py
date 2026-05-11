"""Admin ops views."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.permissions import IsAdminUser
from utils.pagination import StandardPagination
from .models import PricingDayRule, PincodeRule, MandatoryQuestion, Coupon, SiteSettings, SupportMessage
from .serializers import (
    PricingDayRuleSerializer, PincodeRuleSerializer, MandatoryQuestionSerializer,
    CouponSerializer, SiteSettingsSerializer, PublicSiteSettingsSerializer,
    SupportMessageSerializer, SupportMessageUpdateSerializer,
)
from . import services


class PricingOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        day_rules = PricingDayRule.objects.all().order_by('days_limit')
        pincode_rules = PincodeRule.objects.all().order_by('zip_prefix')
        
        return Response({
            'day_rules': PricingDayRuleSerializer(day_rules, many=True).data,
            'pincode_rules': PincodeRuleSerializer(pincode_rules, many=True).data
        })

    def put(self, request):
        # This is a bulk update view as expected by the frontend
        day_rules_data = request.data.get('day_rules', [])
        pincode_rules_data = request.data.get('pincode_rules', [])
        
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        
        # 1. Update Day Rules
        for item in day_rules_data:
            # Map frontend 'days'/'charge' to backend fields
            days_limit = item.get('days_limit') or item.get('days')
            extra_charge = item.get('extra_charge') or item.get('charge')
            
            if days_limit is not None and extra_charge is not None:
                PricingDayRule.objects.update_or_create(
                    days_limit=days_limit,
                    defaults={'extra_charge': extra_charge, 'created_by': admin}
                )
            
        # 2. Update Pincode Rules
        for item in pincode_rules_data:
            # Map frontend 'prefix'/'charge' to backend fields
            zip_prefix = item.get('zip_prefix') or item.get('prefix')
            delivery_fee = item.get('delivery_fee') or item.get('charge')
            
            if zip_prefix is not None and delivery_fee is not None:
                PincodeRule.objects.update_or_create(
                    zip_prefix=zip_prefix,
                    defaults={'delivery_fee': delivery_fee, 'created_by': admin}
                )
            
        return self.get(request)


class PublicSiteSettingsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(PublicSiteSettingsSerializer(SiteSettings.get()).data)


class AdminSiteSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(SiteSettingsSerializer(SiteSettings.get()).data)

    def put(self, request):
        settings = SiteSettings.get()
        ser = SiteSettingsSerializer(settings, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class PricingDayRuleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(PricingDayRuleSerializer(PricingDayRule.objects.all().order_by('days_limit'), many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        ser = PricingDayRuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rule = PricingDayRule.objects.create(created_by=admin, **ser.validated_data)
        return Response(PricingDayRuleSerializer(rule).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        try:
            rule = PricingDayRule.objects.get(pk=pk)
        except PricingDayRule.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        ser = PricingDayRuleSerializer(rule, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        PricingDayRule.objects.filter(pk=pk).delete()
        return Response({'message': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)


class PincodeRuleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(PincodeRuleSerializer(PincodeRule.objects.all().order_by('zip_prefix'), many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        ser = PincodeRuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rule = PincodeRule.objects.create(created_by=admin, **ser.validated_data)
        return Response(PincodeRuleSerializer(rule).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        try:
            rule = PincodeRule.objects.get(pk=pk)
        except PincodeRule.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        ser = PincodeRuleSerializer(rule, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        PincodeRule.objects.filter(pk=pk).delete()
        return Response({'message': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)


class MandatoryQuestionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = MandatoryQuestion.objects.all().order_by('display_order')
        return Response(MandatoryQuestionSerializer(qs, many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        ser = MandatoryQuestionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        q = MandatoryQuestion.objects.create(created_by=admin, **ser.validated_data)
        return Response(MandatoryQuestionSerializer(q).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        try:
            q = MandatoryQuestion.objects.get(pk=pk)
        except MandatoryQuestion.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        ser = MandatoryQuestionSerializer(q, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        MandatoryQuestion.objects.filter(pk=pk).delete()
        return Response({'message': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)


class PublicQuestionsView(APIView):
    """Public: fetch questions for a relation type."""
    permission_classes = [AllowAny]

    def get(self, request):
        relation = request.query_params.get('relation_type', '')
        questions = services.get_questions_for_relation(relation)
        return Response(questions)


class CouponView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(CouponSerializer(Coupon.objects.all().order_by('-created_at'), many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        ser = CouponSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        coupon = Coupon.objects.create(created_by=admin, **ser.validated_data)
        return Response(CouponSerializer(coupon).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        ser = CouponSerializer(coupon, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        Coupon.objects.filter(pk=pk).delete()
        return Response({'message': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)


class SupportMessageCreateView(APIView):
    """Public contact form submission."""
    permission_classes = [AllowAny]

    def post(self, request):
        ser = SupportMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        msg = SupportMessage.objects.create(**ser.validated_data)
        return Response({'message': 'Message received. We will get back to you soon.'}, status=status.HTTP_201_CREATED)


class AdminSupportMessageView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status')
        qs = SupportMessage.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(SupportMessageSerializer(page, many=True).data)

    def patch(self, request, pk):
        try:
            msg = SupportMessage.objects.get(pk=pk)
        except SupportMessage.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        ser = SupportMessageUpdateSerializer(msg, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(SupportMessageSerializer(msg).data)
