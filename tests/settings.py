"""
Django settings for test project.
"""
import os
import re

import django


testenv = re.sub(
    r"[^a-zA-Z0-9]",
    "_",
    os.environ.get("TOXENV", "_".join(str(v) for v in django.VERSION)),
)
tests_migration_module_name = "migrations_{}".format(testenv)


INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "tagulous",
    "tests",
    "tests.tagulous_tests_app",
    "tests.tagulous_tests_app2",
    "tests.tagulousTestsApp3",
    "tests.tagulous_tests_migration",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
SECRET_KEY = "secret"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
ROOT_URLCONF = "tests.tagulous_tests_app.urls"
SERIALIZATION_MODULES = {
    "xml": "tagulous.serializers.xml_serializer",
    "json": "tagulous.serializers.json",
    "python": "tagulous.serializers.python",
}

# If pyyaml is installed, add to serialisers
try:
    import yaml  # noqa
except ImportError:
    pass
else:
    SERIALIZATION_MODULES["yaml"] = "tagulous.serializers.pyyaml"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
        },
    }
]
MIGRATION_MODULES = {
    "tagulous_tests_migration": "tests.tagulous_tests_migration.{}".format(
        tests_migration_module_name
    ),
}
TAGULOUS_NAME_MAX_LENGTH = 191


# Build database settings
DATABASE = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}
engine = os.environ.get("DATABASE_ENGINE")
if engine:
    if engine == "postgresql":
        DATABASE["ENGINE"] = "django.db.backends.postgresql_psycopg2"
        DATABASE["HOST"] = "localhost"
    elif engine == "mysql":
        DATABASE["ENGINE"] = "django.db.backends.mysql"

        # Make sure test DB is going to be UTF8
        DATABASE_TEST = {"TEST": {"CHARSET": "utf8", "COLLATION": "utf8_general_ci"}}
        DATABASE.update(DATABASE_TEST)

    else:
        raise ValueError("Unknown database engine")

    DATABASE["NAME"] = os.environ.get("DATABASE_NAME", "test_tagulous_%s" % testenv)
    for key in ["USER", "PASSWORD", "HOST", "PORT"]:
        if "DATABASE_" + key in os.environ:
            DATABASE[key] = os.environ["DATABASE_" + key]
DATABASES = {"default": DATABASE, "test": DATABASE}


# Make sure the django migration loader will find MIGRATION_MODULES
# This will be cleaned away after each test
tests_migration_path = os.path.join(
    os.path.dirname(__file__),
    "tagulous_tests_migration",
)
if not os.path.isdir(tests_migration_path):
    raise ValueError("tests.tagulous_tests_migration not found")

tests_migration_module_path = os.path.join(
    tests_migration_path,
    tests_migration_module_name,
)
if not os.path.exists(tests_migration_module_path):
    os.mkdir(tests_migration_module_path)

tests_migration_module_init = os.path.join(
    tests_migration_module_path,
    "__init__.py",
)
if not os.path.exists(tests_migration_module_init):
    open(tests_migration_module_init, "a").close()
