"""Content views."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from utils.permissions import IsAdminUser
from utils.cache_keys import PUBLIC_REVIEWS, PUBLIC_FAQS, SITE_STEPS, REVIEWS_TTL, FAQS_TTL, STEPS_TTL
from .models import Review, FAQ, SiteContentStep
from .serializers import ReviewSerializer, FAQSerializer, SiteContentStepSerializer


class PublicReviewListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.core.cache import cache
        data = cache.get(PUBLIC_REVIEWS)
        if data is None:
            reviews = Review.objects.filter(is_published=True).order_by('-created_at')
            data = ReviewSerializer(reviews, many=True).data
            cache.set(PUBLIC_REVIEWS, data, REVIEWS_TTL)
        return Response(data)


class ReviewSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order_id = request.data.get('order_id')
        review = Review.objects.create(order_id=order_id if order_id else None, **ser.validated_data)
        return Response({'message': 'Thank you! Your review has been submitted for moderation.'}, status=status.HTTP_201_CREATED)


class AdminReviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = Review.objects.all().order_by('-created_at')
        return Response(ReviewSerializer(qs, many=True).data)

    def patch(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        review.is_published = request.data.get('is_published', review.is_published)
        review.save(update_fields=['is_published'])
        return Response(ReviewSerializer(review).data)

    def delete(self, request, pk):
        Review.objects.filter(pk=pk).delete()
        return Response({'message': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)


class PublicFAQView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.core.cache import cache
        data = cache.get(PUBLIC_FAQS)
        if data is None:
            faqs = FAQ.objects.filter(is_active=True).order_by('category', 'display_order')
            data = FAQSerializer(faqs, many=True).data
            cache.set(PUBLIC_FAQS, data, FAQS_TTL)
        return Response(data)


class AdminFAQView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(FAQSerializer(FAQ.objects.all().order_by('category', 'display_order'), many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        ser = FAQSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        faq = FAQ.objects.create(created_by=admin, **ser.validated_data)
        return Response(FAQSerializer(faq).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        try:
            faq = FAQ.objects.get(pk=pk)
        except FAQ.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        ser = FAQSerializer(faq, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        FAQ.objects.filter(pk=pk).delete()
        return Response({'message': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)


class SiteContentStepView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.core.cache import cache
        data = cache.get(SITE_STEPS)
        if data is None:
            data = SiteContentStepSerializer(SiteContentStep.objects.all(), many=True).data
            cache.set(SITE_STEPS, data, STEPS_TTL)
        return Response(data)


class AdminSiteContentStepView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, step_num):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        ser = SiteContentStepSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        step, _ = SiteContentStep.objects.update_or_create(step_num=step_num, defaults={**ser.validated_data, 'created_by': admin})
        return Response(SiteContentStepSerializer(step).data)
