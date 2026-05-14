from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'apps.catalog'
    label = 'catalog'
    verbose_name = 'Catalog'

    def ready(self):
        import apps.catalog.signals  # noqa: F401 — connects signal handlers
