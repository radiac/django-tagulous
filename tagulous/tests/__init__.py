#
# Install the test app and run tests
#

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading

settings.INSTALLED_APPS += ('tagulous.tests_app',)
loading.cache.loaded = False

# Load all tests
from tagulous.tests.test_options import *
from tagulous.tests.test_utils import *
from tagulous.tests.test_models_tagmodel import *
from tagulous.tests.test_models_singletagfield import *
from tagulous.tests.test_models_tagfield import *
from tagulous.tests.test_models_order import *
from tagulous.tests.test_models_queryset import *
from tagulous.tests.test_forms import *
