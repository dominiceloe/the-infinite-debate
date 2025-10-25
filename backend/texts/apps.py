from django.apps import AppConfig


class TextsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "texts"

    def ready(self):
        """Import signal handlers when the app is ready."""
        import texts.signals  # noqa
