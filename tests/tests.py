#
# Install the test app and run tests
#
from __future__ import absolute_import, unicode_literals

import django


# Load all tests, if necessary
if django.VERSION < (1, 6):
    from tests.test_options import *  # noqa
    from tests.test_utils import *  # noqa
    from tests.test_models_tagmodel import *  # noqa
    from tests.test_models_singletagfield import *  # noqa
    from tests.test_models_tagfield import *  # noqa
    from tests.test_models_order import *  # noqa
    from tests.test_models_tagged import *  # noqa
    from tests.test_models_tree import *  # noqa
    from tests.test_migrations_south import *  # noqa
    from tests.test_migrations_django import *  # noqa
    from tests.test_serializers import *  # noqa
    from tests.test_forms_singletagfield import *  # noqa
    from tests.test_forms_tagfield import *  # noqa
    from tests.test_forms_mixed import *  # noqa
    from tests.test_views import *  # noqa
    from tests.test_commands import *  # noqa
    from tests.test_admin import *  # noqa
