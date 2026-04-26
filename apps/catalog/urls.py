from django.urls import path
from .views import (
    CatalogListView, AdminCatalogListCreateView, AdminCatalogDetailView,
    RelationCategoryListView, AdminRelationCategoryView,
)

urlpatterns = [
    path('catalog/', CatalogListView.as_view(), name='catalog-list'),
    path('admin/catalog/', AdminCatalogListCreateView.as_view(), name='admin-catalog-list'),
    path('admin/catalog/<uuid:pk>/', AdminCatalogDetailView.as_view(), name='admin-catalog-detail'),
    path('relations/', RelationCategoryListView.as_view(), name='relation-list'),
    path('admin/relations/', AdminRelationCategoryView.as_view(), name='admin-relation-list'),
    path('admin/relations/<int:pk>/', AdminRelationCategoryView.as_view(), name='admin-relation-delete'),
]
