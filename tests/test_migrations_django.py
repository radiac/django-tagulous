"""
Tagulous test: django migrations

Modules tested:
    tagulous.models.migrations
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from importlib import import_module
import os
import sys
import shutil
import warnings

from django.core.management import call_command
from django.db import DatabaseError
from django.utils import six

from tests.lib import *
from tests import tagulous_tests_migration


# If True, display output from call_command - use for debugging tests
DISPLAY_CALL_COMMAND = False

app_name = 'tagulous_tests_migration'
app_module = sys.modules['tests.%s' % app_name]
migrations_name = 'migrations_%s' % testenv
migrations_module = 'tests.%s.%s' % (app_name, migrations_name)
migrations_path = None

# Django 1.8 has extra lines
RENDERING_MODEL_STATES = [] if django.VERSION < (1, 8) else [
    '  Rendering model states... DONE'
]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Util functions
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def clear_migrations():
    "Clear cached mentions of django migrations to force a reload"
    # Remove loaded migrations
    if hasattr(app_module, migrations_name):
        delattr(app_module, migrations_name)
    
    for key in list(sys.modules.keys()):
        if key.startswith(migrations_module):
            del sys.modules[key]
    
    try:
        from importlib import invalidate_caches
    except ImportError:
        pass
    else:
        invalidate_caches()
    
def get_migrations():
    """
    Clears migration cache and gets migrations for the test app which have not
    yet been applied
    """
    from django.db.migrations.loader import MigrationLoader
    clear_migrations()
    loader = MigrationLoader(None, ignore_no_migrations=True)
    graph = loader.graph
    return graph.leaf_nodes(app_name)

def get_migrations_dir():
    "Get migration dir"
    if migrations_path is None:
        globals()['migrations_path'] = os.path.join(
            os.path.dirname(tagulous_tests_migration.__file__),
            migrations_name
        )
    return migrations_path

def get_expected_dir():
    return os.path.normpath(
        os.path.join(
            get_migrations_dir(),
            '..',
            'django_migrations_expected',
        ),
    )

def clean_all():
    "Clean everything - roll back and delete any migrations, forget any loaded"
    # Delete migrations
    migrations_dir = get_migrations_dir()
    expected_dir = get_expected_dir()
    if not (
        app_name in migrations_dir
        and migrations_dir.endswith(migrations_name)
    ):
        # Catch unexpected path - don't want to delete anything important
        raise ValueError('Migrations dir has unexpected name: %s' % migrations_dir)
    if os.path.isdir(migrations_dir):
        shutil.rmtree(migrations_dir)
    elif os.path.exists(migrations_dir):
        raise ValueError('Migrations dir is not a dir')
    
    # Try to roll back to zero using expected migrations
    shutil.copytree(expected_dir, migrations_dir)
    
    try:
        migrate_app(target='zero')
    except DatabaseError:
        # Guess it didn't exist - that's ok, nothing to reverse
        pass
    shutil.rmtree(migrations_dir)
    
    # Empty models
    tagulous_tests_migration.models.unset_model()
    
    # Clear django's migration cache
    clear_migrations()

def make_migration(name):
    "Make a migration with the given name"
    # Django 1.7 doesn't support --name, so create it with auto-gen name and
    # rename it
    try:
        with Capturing() as output:
            call_command(
                'makemigrations',
                app_name,       # app to make migration for
                verbosity=0,    # Silent
            )
    except Exception as e:
        print(">> makemigration failed:")
        print("\n".join(output))
        print("<<<<<<<<<<")
        raise e
    
    # Find file using same numeric prefix
    migrations = get_migrations()
    last_migration = migrations[-1][1]
    if not name.startswith(last_migration[:5]):
        raise ValueError('Was expecting migration %s to start %s' % (
            name, last_migration[:5]),
        )
    clear_migrations()
    
    # Rename file
    migrations_dir = get_migrations_dir()
    old_py = os.path.join(migrations_dir, '%s.py' % last_migration)
    new_py = os.path.join(migrations_dir, '%s.py' % name)
    os.rename(old_py, new_py)
    if os.path.exists(old_py + 'c'):
        os.remove(old_py + 'c')
    

def migrate_app(target=None):
    "Apply migrations"
    clear_migrations()
    
    if DISPLAY_CALL_COMMAND:
        print(">> manage.py migrate %s target=%s" % (app_name, target))
    
    args = [app_name]
    if target is not None:
        args.append(target)
    kwargs = {
        'interactive':  False, # no user input
        'verbosity':    1,     # basic reporting
    }
    
    try:
        with Capturing() as output:
            with warnings.catch_warnings(record=True) as cw:
                call_command('migrate', *args, **kwargs)
    except Exception as e:
        print(">> migration failed: %s" % e)
        if not DISPLAY_CALL_COMMAND:
            print(">> manage.py migrate %s target=%s" % (app_name, target))
        print("\n".join(output))
        print("<<<<<<<<<<")
        raise e
    
    # Ensure caught warnings are expected
    if django.VERSION < (1, 6):
        assert len(cw) == 0
    else:
        for w in cw:
            assert issubclass(w.category, PendingDeprecationWarning)
        
    if DISPLAY_CALL_COMMAND:
        print('\n'.join(output))
        print("<<<<<<<<<<")
    
    return output


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Tests
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@unittest.skipIf(
    django.VERSION < (1, 7),
    'Django migration tests not run for Django 1.6 or older'
)
class DjangoMigrationTest(TagTestManager, TransactionTestCase):
    """
    Test django migrations
    """
    #
    # Test management - ensure it's clean before and after
    #
    
    @classmethod
    def setUpClass(self):
        "Clean everything before each test in case previous run failed"
        clean_all()
    
    def tearDownExtra(self):
        "Clean away the model so it's not installed by TestCase"
        clean_all()
        
    @classmethod
    def tearDownClass(cls):
        "Leave everything clean at the end of the tests"
        clean_all()
    
    #
    # Migration file analysis
    #
    
    def _import_migration(self, name):
        "Import the named migration"
        path = get_migrations_dir()
        root = os.path.dirname(__file__)
        if not path.startswith(root):
            return self.fail(
                'Could not find common root between test and migration dir:\n'
                '  %s\n  %s' % __file__, path
            )
        
        module_name = '.'.join(
            ['tests'] + path[len(root) + 1:].split(os.sep) + [name]
        )
        module = import_module(module_name)
        return module
    
        
    #
    # Extra assertions
    #
    
    def assertMigrationExpected(self, name):
        "Compare two migration files"
        # Import and validate the migrations
        mod1 = self._import_migration(name)
        self.assertValidMigration(mod1)
        mig1 = mod1.Migration
        
        mod2 = self._import_migration(name)
        self.assertValidMigration(mod2)
        mig2 = mod2.Migration
        
        # Compare dependencies
        # Straight list of tuples
        self.assertEqual(mig1.dependencies, mig2.dependencies)
        
        # Compare operations
        # They're list of Operation classes, which provide __eq__
        self.assertEqual(mig1.operations, mig2.operations)
        
    def assertValidMigration(self, module):
        "Basic validation of an imported migration"
        from django.db.migrations.migration import Migration
        self.assertTrue('Migration' in module.__dict__)
        self.assertTrue(issubclass(module.Migration, Migration))
        self.assertTrue(hasattr(module.Migration, 'dependencies'))
        self.assertTrue(hasattr(module.Migration, 'operations'))
    
    
    #
    # Tests
    #
    
    def migrate_initial(self):
        """
        Load the initial test app's model, and create and apply an initial
        schema migration. Check that the migration worked.
        """
        model_initial = tagulous_tests_migration.models.set_model_initial()
        self.assertFalse(
            issubclass(model_initial, tag_models.tagged.TaggedModel)
        )
        
        # Make the migration
        make_migration('0001_initial')
        
        # Check the files were created as expected
        migrations = get_migrations()
        self.assertEqual(len(migrations), 1)
        self.assertEqual(migrations[0], (app_name, '0001_initial'))
        self.assertMigrationExpected('0001_initial')
        
        # Check they apply correctly
        output = migrate_app()
        self.assertEqual(output, [
            'Operations to perform:',
            '  Apply all migrations: tagulous_tests_migration',
            'Running migrations:',
            ] + RENDERING_MODEL_STATES + [
            '  Applying tagulous_tests_migration.0001_initial... OK',
        ])
        
        return model_initial

    def migrate_tagged(self):
        """
        After migrating to the initial model, switch the test app to the
        tagged model, and create and apply a schema migration. Check that the
        migration worked.
        """
        # First need to migrate to initial - re-run that migration
        self.migrate_initial()
        
        # Now switch model
        model_tagged = tagulous_tests_migration.models.set_model_tagged()
        self.assertTrue(issubclass(model_tagged, tag_models.tagged.TaggedModel))
        
        # Make the migration
        make_migration('0002_tagged')
        
        # Check the files were created as expected
        migrations = get_migrations()
        self.assertEqual(len(migrations), 1)
        self.assertEqual(migrations[0], (app_name, '0002_tagged'))
        self.assertMigrationExpected('0002_tagged')
        
        # Check they apply correctly
        output = migrate_app()
        self.assertEqual(output, [
            'Operations to perform:',
            '  Apply all migrations: tagulous_tests_migration',
            'Running migrations:',
            ] + RENDERING_MODEL_STATES + [
            '  Applying tagulous_tests_migration.0002_tagged... OK',
        ])
        
        return model_tagged
    
    def migrate_tree(self):
        """
        After migrating to the tagged model, switch the test app to the tree
        model, load some test data, and apply the pre-written schema migration
        which uses add_unique_column. Check that the migration worked.
        """
        # Migrate to tagged
        model_tagged = self.migrate_tagged()
        
        # Add some test data
        model_tagged.tags.tag_model.objects.create(name='one/two/three')
        model_tagged.tags.tag_model.objects.create(name='uno/dos/tres')
        self.assertTagModel(model_tagged.tags.tag_model, {
            'one/two/three': 0,
            'uno/dos/tres':  0,
        })
        
        # Now switch model
        model_tree = tagulous_tests_migration.models.set_model_tree()
        self.assertTrue(issubclass(model_tree, tag_models.tagged.TaggedModel))
        self.assertTagModel(model_tagged.tags.tag_model, {
            'one/two/three': 0,
            'uno/dos/tres':  0,
        })
        
        # We can't automaticallly create a migration here; because we're adding
        # a null field, makemigration would ask us questions we don't want to
        # answer anyway, because we'd replace the AddField operation with a
        # tagulous.models.mgiration.AddUniqueField operation. We'll therefore
        # use one we prepared earlier, 0003_tree.py
        
        # Add in the prepared schemamigration for the tree
        migrations_dir = get_migrations_dir()
        expected_dir = get_expected_dir()
        shutil.copy(
            os.path.join(expected_dir, '0003_tree.py'),
            migrations_dir
        )
        
        # Check the files were created as expected
        migrations = get_migrations()
        self.assertEqual(len(migrations), 1)
        self.assertEqual(migrations[0], (app_name, '0003_tree'))
        
        # Check they apply correctly
        output = migrate_app()
        self.assertSequenceEqual(output, [
            'Operations to perform:',
            '  Apply all migrations: tagulous_tests_migration',
            'Running migrations:',
            ] + RENDERING_MODEL_STATES + [
            '  Applying tagulous_tests_migration.0003_tree... OK',
        ])
        
        # Data shouldn't have changed yet
        self.assertTagModel(model_tree.tags.tag_model, {
            'one/two/three':    0,
            'uno/dos/tres':     0,
        })
        self.assertEqual(model_tree.tags.tag_model.objects.get(pk=1).path, '1')
        self.assertEqual(model_tree.tags.tag_model.objects.get(pk=2).path, '2')
        
        # Rebuild tree
        model_tree.tags.tag_model.objects.rebuild()
        
        # We should now have nicely-built trees
        self.assertTagModel(model_tree.tags.tag_model, {
            'one':              0,
            'one/two':          0,
            'one/two/three':    0,
            'uno':              0,
            'uno/dos':          0,
            'uno/dos/tres':     0,
        })
        tag_objects = model_tree.tags.tag_model.objects
        self.assertEqual(tag_objects.get(name='one').path, 'one')
        self.assertEqual(tag_objects.get(name='one/two').path, 'one/two')
        self.assertEqual(tag_objects.get(name='one/two/three').path, 'one/two/three')
        self.assertEqual(tag_objects.get(name='uno').path, 'uno')
        self.assertEqual(tag_objects.get(name='uno/dos').path, 'uno/dos')
        self.assertEqual(tag_objects.get(name='uno/dos/tres').path, 'uno/dos/tres')

        return model_tree
    

    def migrate_data(self):
        """
        After migrating to the tree model, apply the pre-written data migration
        which tests tag fields and models. Check that the migration worked.
        """
        model_tree = self.migrate_tree()
        
        # Empty the tags from the test model added by migrate_tree
        model_tree.tags.tag_model.objects.all().delete()
        self.assertTagModel(model_tree.tags.tag_model, {})
        
        # Add some test data to the model itself
        model_tree.objects.create(
            name='Test 1', singletag='Mr', tags='one/two, uno/dos',
        )
        model_tree.objects.create(
            name='Test 2', singletag='Mrs', tags='one/two',
        )
        model_tree.objects.create(
            name='Test 3', singletag='Mr', tags='uno/dos',
        )
        self.assertTagModel(model_tree.singletag.tag_model, {
            'Mr':       2,
            'Mrs':      1,
        })
        self.assertTagModel(model_tree.tags.tag_model, {
            'one':      0,
            'one/two':  2,
            'uno':      0,
            'uno/dos':  2,
        })
        
        # Add in the datamigration
        migrations_dir = get_migrations_dir()
        expected_dir = get_expected_dir()
        shutil.copy(
            os.path.join(expected_dir, '0004_data.py'),
            migrations_dir
        )
        
        # Check the files were created as expected
        migrations = get_migrations()
        self.assertEqual(len(migrations), 1)
        self.assertEqual(migrations[0], (app_name, '0004_data'))
        
        # Check they apply correctly
        output = migrate_app()
        self.assertSequenceEqual(output, [
            'Operations to perform:',
            '  Apply all migrations: tagulous_tests_migration',
            'Running migrations:',
            ] + RENDERING_MODEL_STATES + [
            '  Applying tagulous_tests_migration.0004_data... OK',
        ])
        

    #
    # Tests
    #
    
    # Individual tests for development purposes
    # No point running each of them - test_data() will run them as its setup
    '''
    def test_initial(self):
        "Test initial migration is created and can be applied and used"
        self.migrate_initial()

    def test_tagged(self):
        "Test tagged migration is created and can be applied and used"
        self.migrate_tagged()
    
    def test_tree(self):
        "Test migration to Tree model using add_unique_column"
        self.migrate_tree()
    '''
    
    def test_data(self):
        "Test data migration"
        self.migrate_data()
