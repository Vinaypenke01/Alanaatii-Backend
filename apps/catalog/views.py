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
        compatible_with = request.query_params.get('compatible_with')
        
        qs = CatalogItem.objects.filter(is_active=True)
        
        if category:
            qs = qs.filter(category=category)
            
        if compatible_with:
            try:
                parent_item = CatalogItem.objects.get(id=compatible_with)
                if not parent_item.fits_all_boxes:
                    qs = qs.filter(id__in=parent_item.compatible_boxes.all())
            except CatalogItem.DoesNotExist:
                pass
                
        qs = qs.order_by('category', 'title')
        return Response(CatalogItemSerializer(qs, many=True, context={'request': request}).data)


class AdminCatalogSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from .models import CatalogCategory
        summary = {}
        for code, label in CatalogCategory.choices:
            summary[code] = {
                'label': label,
                'count': CatalogItem.objects.filter(category=code).count()
            }
        return Response(summary)


class AdminCatalogListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        category = request.query_params.get('category')
        qs = CatalogItem.objects.all().order_by('category', 'title')
        if category:
            qs = qs.filter(category=category)
        return Response(CatalogItemSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        
        # Make a mutable copy of request.data if it's a QueryDict
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        
        # Map 'image' from frontend to 'image_url' field in DB
        if 'image' in request.FILES:
            data['image_url'] = request.FILES['image']
            
        ser = CatalogItemCreateSerializer(data=data)
        ser.is_valid(raise_exception=True)
        item = services.create_catalog_item(ser.validated_data, admin)
        return Response(CatalogItemSerializer(item, context={'request': request}).data, status=status.HTTP_201_CREATED)


class AdminCatalogDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        
        # Map 'image' from frontend to 'image_url' field in DB
        if 'image' in request.FILES:
            data['image_url'] = request.FILES['image']

        item_obj = CatalogItem.objects.get(id=pk)
        ser = CatalogItemCreateSerializer(item_obj, data=data, partial=True)
        ser.is_valid(raise_exception=True)

        item = services.update_catalog_item(str(pk), ser.validated_data, admin)
        return Response(CatalogItemSerializer(item, context={'request': request}).data)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        services.delete_catalog_item(str(pk), admin)
        return Response({'message': 'Item deleted.'}, status=status.HTTP_204_NO_CONTENT)
