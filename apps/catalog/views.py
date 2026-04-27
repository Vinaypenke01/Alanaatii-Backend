"""Catalog views."""
import os
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from utils.permissions import IsAdminUser
from .models import CatalogItem
from .serializers import CatalogItemSerializer, CatalogItemCreateSerializer
from . import services


class CatalogListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get('category')
        if category:
            qs = CatalogItem.objects.filter(category=category, is_active=True).order_by('title')
        else:
            qs = CatalogItem.objects.filter(is_active=True).order_by('category', 'title')
        return Response(CatalogItemSerializer(qs, many=True).data)


class AdminCatalogListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        category = request.query_params.get('category')
        qs = CatalogItem.objects.all().order_by('category', 'title')
        if category:
            qs = qs.filter(category=category)
        return Response(CatalogItemSerializer(qs, many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        # Handle image upload
        data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
        image_file = request.FILES.get('image_url')
        if image_file:
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'catalog')
            os.makedirs(upload_dir, exist_ok=True)
            filename = f'{timezone.now().strftime("%Y%m%d%H%M%S")}_{image_file.name}'
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb+') as dest:
                for chunk in image_file.chunks():
                    dest.write(chunk)
            data['image_url'] = f'catalog/{filename}'
        ser = CatalogItemCreateSerializer(data=data)
        ser.is_valid(raise_exception=True)
        item = services.create_catalog_item(ser.validated_data, admin)
        return Response(CatalogItemSerializer(item).data, status=status.HTTP_201_CREATED)


class AdminCatalogDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, pk):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
        item = services.update_catalog_item(str(pk), data, admin)
        return Response(CatalogItemSerializer(item).data)

    def delete(self, request, pk):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        services.delete_catalog_item(str(pk), admin)
        return Response({'message': 'Item deleted.'}, status=status.HTTP_204_NO_CONTENT)
