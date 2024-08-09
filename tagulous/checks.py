from django.core.checks import Warning, register

SERIALIZATION_MODULES_EXPECTED = {
    "xml": "tagulous.serializers.xml_serializer",
    "json": "tagulous.serializers.json",
    "python": "tagulous.serializers.python",
    "yaml": "tagulous.serializers.pyyaml",
}

WARNING_W001 = Warning(
    "``settings.SERIALIZATION_MODULES`` has not been configured as expected",
    hint=(
        "See Tagulous installation instructions for"
        " recommended SERIALIZATION_MODULES setting"
    ),
    id="tagulous.W001",
)


def tagulous_check(app_configs, **kwargs):
    from django.conf import settings

    errors = []

    serialization_modules = getattr(settings, "SERIALIZATION_MODULES", None)
    if serialization_modules != SERIALIZATION_MODULES_EXPECTED:
        errors.append(WARNING_W001)

    return errors


def register_checks():
    register(tagulous_check)
