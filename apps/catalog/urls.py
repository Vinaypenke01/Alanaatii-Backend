from django.urls import path
from .views import (
    CatalogListView, AdminCatalogListCreateView, AdminCatalogDetailView,
    AdminCatalogSummaryView
)

urlpatterns = [
    path('catalog/', CatalogListView.as_view(), name='catalog-list'),
    path('admin/catalog/', AdminCatalogListCreateView.as_view(), name='admin-catalog-list'),
    path('admin/catalog/summary/', AdminCatalogSummaryView.as_view(), name='admin-catalog-summary'),
    path('admin/catalog/<uuid:pk>/', AdminCatalogDetailView.as_view(), name='admin-catalog-detail'),
]
