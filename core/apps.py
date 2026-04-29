from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Hook the audit signals - importing the module wires the
        # @receiver decorators.
        from . import signals  # noqa: F401
