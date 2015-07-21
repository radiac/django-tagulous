#
# Install the test app and run tests
#

import warnings

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading

settings.INSTALLED_APPS += (
    'tagulous.tests.tagulous_tests_app',
    'tagulous.tests.tagulous_tests_app2',
    'tagulous.tests.tagulous_tests_migration',
)
loading.cache.loaded = False

# Load all tests
from tagulous.tests.test_options import *
from tagulous.tests.test_utils import *
from tagulous.tests.test_models_tagmodel import *
from tagulous.tests.test_models_singletagfield import *
from tagulous.tests.test_models_tagfield import *
from tagulous.tests.test_models_order import *
from tagulous.tests.test_models_tagged import *
from tagulous.tests.test_models_tree import *
from tagulous.tests.test_models_migrations import *
from tagulous.tests.test_forms_singletagfield import *
from tagulous.tests.test_forms_tagfield import *
from tagulous.tests.test_forms_mixed import *
from tagulous.tests.test_views import *
from tagulous.tests.test_commands import *
from tagulous.tests.test_admin import *
