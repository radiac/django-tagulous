import os
import re
import sys

from setuptools import find_packages, setup


VERSION = "1.3.0"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def runtests(args):
    "Run tests"
    import django
    from django.conf import settings
    from django.core.management import execute_from_command_line

    if not settings.configured:
        testenv = re.sub(
            r"[^a-zA-Z0-9]",
            "_",
            os.environ.get("TOXENV", "_".join(str(v) for v in django.VERSION)),
        )
        tests_migration_module_name = "migrations_{}".format(testenv)

        SETTINGS = dict(
            INSTALLED_APPS=[
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
            ],
            MIDDLEWARE=[
                "django.middleware.common.CommonMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
            ],
            SECRET_KEY="secret",
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            ROOT_URLCONF="tests.tagulous_tests_app.urls",
            SERIALIZATION_MODULES={
                "xml": "tagulous.serializers.xml_serializer",
                "json": "tagulous.serializers.json",
                "python": "tagulous.serializers.python",
            },
            TEMPLATES=[
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
            ],
            MIGRATION_MODULES={
                "tagulous_tests_migration": "tests.tagulous_tests_migration.{}".format(
                    tests_migration_module_name
                ),
            },
            TAGULOUS_NAME_MAX_LENGTH=191,
        )

        # If yaml is available, add to serialisers
        try:
            import yaml  # noqa
        except ImportError:
            pass
        else:
            SETTINGS["SERIALIZATION_MODULES"]["yaml"] = "tagulous.serializers.pyyaml"

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
                DATABASE_TEST = {
                    "TEST": {"CHARSET": "utf8", "COLLATION": "utf8_general_ci"}
                }
                DATABASE.update(DATABASE_TEST)

            else:
                raise ValueError("Unknown database engine")

            DATABASE["NAME"] = os.environ.get(
                "DATABASE_NAME", "test_tagulous_%s" % testenv
            )
            for key in ["USER", "PASSWORD", "HOST", "PORT"]:
                if "DATABASE_" + key in os.environ:
                    DATABASE[key] = os.environ["DATABASE_" + key]
        SETTINGS["DATABASES"] = {"default": DATABASE, "test": DATABASE}

        # Make sure the django migration loader will find MIGRATION_MODULES
        # This will be cleaned away after each test
        tests_migration_path = os.path.join(
            os.path.dirname(__file__), "tests", "tagulous_tests_migration",
        )
        if not os.path.isdir(tests_migration_path):
            raise ValueError("tests.tagulous_tests_migration not found")

        tests_migration_module_path = os.path.join(
            tests_migration_path, tests_migration_module_name,
        )
        if not os.path.exists(tests_migration_module_path):
            os.mkdir(tests_migration_module_path)

        tests_migration_module_init = os.path.join(
            tests_migration_module_path, "__init__.py",
        )
        if not os.path.exists(tests_migration_module_init):
            open(tests_migration_module_init, "a").close()

        # Configure
        settings.configure(**SETTINGS)

    execute_from_command_line(args[:1] + ["test"] + (args[2:] or ["tests"]))


if len(sys.argv) > 1 and sys.argv[1] == "test":
    runtests(sys.argv)
    sys.exit()

setup(
    name="django-tagulous",
    version=VERSION,
    author="Richard Terry",
    author_email="code@radiac.net",
    description=("Fabulous Tagging for Django"),
    license="BSD",
    keywords="django tagging",
    url="http://radiac.net/projects/django-tagulous/",
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
    ],
    install_requires=["Django>=2.2"],
    extras_require={
        "dev": ["tox", "jasmine", "djangorestframework~=3.0"],
        "devdb": ["psycopg2", "mysqlclient"],
    },
    zip_safe=True,
    packages=find_packages(exclude=("docs", "tests*",)),
    include_package_data=True,
)
