from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = 'apps.content'
    label = 'content'
    verbose_name = 'Content'

    def ready(self):
        import apps.content.signals  # noqa: F401 — connects signal handlers
