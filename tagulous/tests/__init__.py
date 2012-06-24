#
# Install the test app and run tests
#

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading

settings.INSTALLED_APPS += ('tagulous.tests_app',)
loading.cache.loaded = False

# Now test the models
from tagulous.tests.tests import *
