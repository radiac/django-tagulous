#
# Install the test app and run tests
#
from __future__ import absolute_import
from __future__ import unicode_literals

import warnings

import django
from django.conf import settings
from django.core.management import call_command
from django.utils import six


# Load all tests, if necessary
if django.VERSION < (1, 6):
    from tests.test_options import *
    from tests.test_utils import *
    from tests.test_models_tagmodel import *
    from tests.test_models_singletagfield import *
    from tests.test_models_tagfield import *
    from tests.test_models_order import *
    from tests.test_models_tagged import *
    from tests.test_models_tree import *
    from tests.test_migrations_south import *
    from tests.test_migrations_django import *
    from tests.test_serializers import *
    from tests.test_forms_singletagfield import *
    from tests.test_forms_tagfield import *
    from tests.test_forms_mixed import *
    from tests.test_views import *
    from tests.test_commands import *
    from tests.test_admin import *
