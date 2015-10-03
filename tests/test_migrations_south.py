"""
Tagulous test: south migrations

Modules tested:
    tagulous.models.migrations
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import inspect
import os
import sys
import shutil
import warnings

from django.conf import settings
from django.core.management import call_command
from django.db import DatabaseError
from django.utils import six

from tests.lib import *
from tests import tagulous_tests_migration

try:
    import south
except ImportError:
    south = None

try:
    eval("u'string'")
except SyntaxError:
    # South doesn't support Python 3.2
    south = None

# If True, display output from call_command - use for debugging tests
DISPLAY_CALL_COMMAND = False

app_name = 'tagulous_tests_migration'
app_module = sys.modules['tests.%s' % app_name]
migrations_name = 'migrations_%s' % testenv
migrations_module = 'tests.%s.%s' % (app_name, migrations_name)
migrations_path = None


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Util functions
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def clear_migrations():
    "Clear cached mentions of south migrations to force a reload"
    from south.migration import Migrations
    
    # Clear metaclass cache
    if app_name in Migrations.instances:
        del Migrations.instances[app_name]
    
    # Remove loaded migrations
    if hasattr(app_module, migrations_name):
        delattr(app_module, migrations_name)
    
    for key in list(sys.modules.keys()):
        if key.startswith(migrations_module):
            del sys.modules[key]
    
def get_migrations():
    "Clears migration cache and gets migrations for the test app"
    from south.migration import Migrations
    clear_migrations()
    return Migrations(
        tagulous_tests_migration, force_creation=True, verbose_creation=False,
    )
    
def get_migrations_dir():
    "Get migration dir"
    if migrations_path is None:
        globals()['migrations_path'] = get_migrations().migrations_dir()
    return migrations_path

def get_expected_dir():
    return os.path.normpath(
        os.path.join(
            get_migrations_dir(),
            '..',
            'south_migrations_expected',
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
        raise ValueError('Migrations dir has unexpected name')
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
    
    # Clear south's migration cache
    clear_migrations()


def migrate_app(target=None):
    "Apply migrations"
    clear_migrations()
    
    if DISPLAY_CALL_COMMAND:
        print(">> manage.py migrate %s target=%s" % (app_name, target))
    
    try:
        with Capturing() as output:
            with warnings.catch_warnings(record=True) as cw:
                call_command(
                    'migrate',
                    app_name,       # app to migrate
                    target=target,  # Optional target
                    verbosity=1,    # Silent
                )
    except Exception as e:
        print(">> Migration failed:")
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

@unittest.skipIf(django.VERSION >= (1, 7), 'South tests not run for Django 1.7+')
@unittest.skipIf(south is None, 'South not installed')
@unittest.skipIf(
    'south' not in settings.INSTALLED_APPS, 'South not in INSTALLED_APPS'
)
class SouthMigrationTest(TagTestManager, TransactionTestCase):
    """
    Test south migrations
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
    
    def _import_migration(self, path, name):
        "Import the named migration from the given file path"
        root = os.path.dirname(__file__)
        if not path.startswith(root):
            return self.fail(
                'Could not find common root between test and migration dir:\n'
                '  %s\n  %s' % __file__, path
            )
            
        module_name = '.'.join(
            ['tests'] + path[len(root) + 1:].split(os.sep) + [name]
        )
        module = __import__(module_name, {}, {}, ['Migration'])
        
        return module
    
    def _parse_migration_function(self, fn):
        """
        Parse a migration function into a dict
        
        Dict will have keys for each db method called, with values as dicts of
        whatever makes them unique and the arguments.
        
        There will also be a 'vars' dict with variable definitions
        """
        import ast
        lines, firstlineno = inspect.getsourcelines(fn.__code__)
        
        # De-indent and parse into an AST
        indent = len(lines[0]) - len(lines[0].lstrip())
        lines = [line[indent:] for line in lines]
        root = ast.parse(''.join(lines))
        
        def ast_dump(*nodes):
            "Dump ast node without unicode strings"
            return ', '.join(
                ast.dump(node).replace(
                    "Str(s=u'", "Str(s='"
                ).replace(
                    "{u'", "{'"
                )
                for node in nodes
            )
        
        def parse_field(field):
            "Parse a field into a tuple of (cls_name, 'ast value')"
            if isinstance(field.func, ast.Attribute):
                # Call to self.gf
                field_cls = six.text_type(
                    field.func.value.id + '.' + field.func.attr
                )
            else:
                # Direct ref to field
                field_cls = six.text_type(field.func.args[0].s)
            
            attrs = {}
            for keyword in field.keywords:
                attrs[keyword.arg] = ast_dump(keyword.value)
            return (field_cls, attrs)
        
        # Find all db object method calls
        data = {
            'create_table':         {},
            'send_create_signal':   {},
            'create_unique':        {},
            'add_column':           {},
            'shorten_name':         {},
            'delete_table':         {},
        }
        ast_state = {}
        
        # This seemed like such a good idea at the time
        for node in root.body[0].body:
            # db.create_table( <arguments> )
            dbcall = node.value
            self.assertEqual(dbcall.func.value.id, 'db')
            method = dbcall.func.attr
            
            # Shift arguments node tree into dict
            if method == 'create_table':
                # <table>, <fields tuple>
                if isinstance(dbcall.args[0], ast.Str):
                    table_name = six.text_type(dbcall.args[0].s)
                elif isinstance(dbcall.args[0], ast.Name):
                    var_name = dbcall.args[0].id
                    self.assertTrue(var_name in ast_state)
                    table_name = ast_state[var_name]
                self.assertFalse(table_name in data[method])
                
                fields = {}
                for field_tuple in dbcall.args[1].elts:
                    # <field name>, self.gf(<type>)(<args>)
                    field_name = six.text_type(field_tuple.elts[0].s)
                    self.assertFalse(field_name in fields)
                    fields[field_name] = parse_field(field_tuple.elts[1])
                data[method][table_name] = fields
            
            elif method == 'send_create_signal':
                # <app name>, [<model name>]
                model_name = six.text_type(dbcall.args[1].elts[0].s)
                self.assertFalse(model_name in data[method])
                data[method][model_name] = ast_dump(dbcall)
            
            elif method == 'create_unique':
                # <table name>, [<field name>]
                if isinstance(dbcall.args[0], ast.Str):
                    table_name = six.text_type(dbcall.args[0].s)
                elif isinstance(dbcall.args[0], ast.Name):
                    var_name = dbcall.args[0].id
                    self.assertTrue(var_name in ast_state)
                    table_name = ast_state[var_name]
                self.assertFalse(table_name in data[method])
                data[method][table_name] = ast_dump(dbcall.args[1])
            
            elif method == 'add_column':
                # <table name>, <field name>, self.gf(<type>)(<args>), keep_default=<?>
                field_id = six.text_type(
                    dbcall.args[0].s) + '.' + str(dbcall.args[1].s
                )
                self.assertFalse(field_id in data[method])
                data[method][field_id] = [
                    parse_field(dbcall.args[2]),
                    ast_dump(*dbcall.args[3:]),
                ]
            
            elif method == 'shorten_name':
                # <var> = db.shorten_name(<table name>)
                table_name = six.text_type(dbcall.args[0].s)
                self.assertFalse(field_id in data[method])
                data[method][table_name] = ast_dump(node.targets[0])
                ast_state[node.targets[0].id] = table_name
            
            else:
                self.fail('Unrecognised db method: %s' % method)
        
        return data
        
        
    #
    # Extra assertions
    #
    
    def assertValidMigration(self, module):
        "Basic validation of an imported migration"
        self.assertTrue('Migration' in module.__dict__)
        self.assertTrue(issubclass(module.Migration, south.v2.SchemaMigration))
        self.assertTrue(hasattr(module.Migration, 'forwards'))
        self.assertTrue(hasattr(module.Migration, 'backwards'))
        self.assertTrue(hasattr(module.Migration, 'models'))
    
    def assertMigrationExpected(self, name):
        "Compare two migration files"
        # Import and validate the migrations
        mig1 = self._import_migration(get_migrations_dir(), name)
        self.assertValidMigration(mig1)
        
        mig2 = self._import_migration(get_expected_dir(), name)
        self.assertValidMigration(mig2)
        
        # Fn to standardise models dict string type
        def fix_text_type(val):
            if isinstance(val, six.string_types):
                val = val.replace("u'", "'")
                if six.PY3:
                    return bytes(val, 'utf8')
                return bytes(val)
            elif isinstance(val, dict):
                dct = val
                for key, val in dct.items():
                    del dct[key]
                    dct[fix_text_type(key)] = fix_text_type(val)
                return dct
            else:
                # Assume it's an iterable
                val = [fix_text_type(v) for v in val]
        
        # Compare models - some strings will be unicode, some not
        self.assertEqual(
            fix_text_type(mig1.Migration.models),
            fix_text_type(mig2.Migration.models),
        )
        
        data1 = self._parse_migration_function(mig1.Migration.forwards)
        data2 = self._parse_migration_function(mig2.Migration.forwards)
        self.assertEqual(data1, data2)
        
    
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
        
        # Ensure migration dir exists - we're using a custom one, so South
        # won't create it
        migrations_dir = get_migrations_dir()
        os.mkdir(migrations_dir)
        open(os.path.join(migrations_dir, '__init__.py'), 'a').close()
        
        # Run schemamigration --initial
        with Capturing() as output:
            call_command(
                'schemamigration',
                # First two args not named - kwarg 'name' clashes
                app_name,       # app to migrate
                'initial',      # name - Name of migration to create
                initial=True,   # This is the initial schema migration
                verbosity=0,    # Silent
            )
        
        # Check the files were created as expected
        migrations = get_migrations()
        migrations = [six.text_type(m) for m in migrations]
        self.assertEqual(len(migrations), 1)
        self.assertEqual(migrations[0], '%s:0001_initial' % app_name)
        self.assertMigrationExpected('0001_initial')
        
        # Check they apply correctly
        output = migrate_app()
        self.assertSequenceEqual(output, [
            'Running migrations for tagulous_tests_migration:',
            ' - Migrating forwards to 0001_initial.',
            ' > tagulous_tests_migration:0001_initial',
            ' - Loading initial data for tagulous_tests_migration.',
            'Installed 0 object(s) from 0 fixture(s)'
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
        
        # Run schemamigration --auto
        with Capturing() as output:
            call_command(
                'schemamigration',
                app_name,       # app to migrate
                'tagged',       # name - Name of migration to create
                auto=True,      # This is an auto schema migration
                verbosity=0,    # Silent
            )
        
        # Check the files were created as expected
        migrations = get_migrations()
        migrations = [six.text_type(m) for m in migrations]
        self.assertEqual(len(migrations), 2)
        self.assertEqual(migrations[0], '%s:0001_initial' % app_name)
        self.assertEqual(migrations[1], '%s:0002_tagged' % app_name)
        self.assertMigrationExpected('0002_tagged')
        
        # Check they apply correctly
        output = migrate_app()
        '''
        self.assertSequenceEqual(output, [
            'Running migrations for tagulous_tests_migration:',
            ' - Migrating forwards to 0002_tagged.',
            ' > tagulous_tests_migration:0002_tagged',
            ' - Loading initial data for tagulous_tests_migration.',
            'Installed 0 object(s) from 0 fixture(s)'
        ])
        '''
        
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
        
        # We can't create a schema migration here; because we're adding a null
        # field, South would ask us questions we don't want to answer anyway,
        # because we'd replace the add_column call with a call to
        # tagulous.models.migration.add_unique_column. We'll therefore use one
        # we prepared earlier, 0003_tree.py
        #
        # But first, confirm schemamigration would have correctly detected the
        # tag model base has changed to a BaseTagTreeModel:
        frozen_singletag = south.creator.freezer.prep_for_freeze(
            model_tree.singletag.tag_model
        )
        self.assertSequenceEqual(
            frozen_singletag['Meta']['_bases'],
            ['tagulous.models.BaseTagModel'],
        )
        
        frozen_tags = south.creator.freezer.prep_for_freeze(
            model_tree.tags.tag_model
        )
        self.assertSequenceEqual(
            frozen_tags['Meta']['_bases'],
            ['tagulous.models.BaseTagTreeModel'],
        )
        
        # Add in the prepared schemamigration for the tree
        migrations_dir = get_migrations_dir()
        expected_dir = get_expected_dir()
        shutil.copy(
            os.path.join(expected_dir, '0003_tree.py'),
            migrations_dir
        )
        
        # Check the files were created as expected
        migrations = get_migrations()
        migrations = [six.text_type(m) for m in migrations]
        self.assertEqual(len(migrations), 3)
        self.assertEqual(migrations[0], '%s:0001_initial' % app_name)
        self.assertEqual(migrations[1], '%s:0002_tagged' % app_name)
        self.assertEqual(migrations[2], '%s:0003_tree' % app_name)
        
        # Check they apply correctly
        output = migrate_app()
        '''
        self.assertSequenceEqual(output, [
            'Running migrations for tagulous_tests_migration:',
            ' - Migrating forwards to 0003_tree.',
            ' > tagulous_tests_migration:0003_tree',
            ' - Loading initial data for tagulous_tests_migration.',
            'Installed 0 object(s) from 0 fixture(s)'
        ])
        '''
        
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
        migrations = [six.text_type(m) for m in migrations]
        self.assertEqual(len(migrations), 4)
        self.assertEqual(migrations[0], '%s:0001_initial' % app_name)
        self.assertEqual(migrations[1], '%s:0002_tagged' % app_name)
        self.assertEqual(migrations[2], '%s:0003_tree' % app_name)
        self.assertEqual(migrations[3], '%s:0004_data' % app_name)
        
        # Check they apply correctly
        output = migrate_app()
        self.assertSequenceEqual(output, [
            'Running migrations for tagulous_tests_migration:',
            ' - Migrating forwards to 0004_data.',
            ' > tagulous_tests_migration:0004_data',
            " - Migration 'tagulous_tests_migration:0004_data' is "
                "marked for no-dry-run.",
            ' - Loading initial data for tagulous_tests_migration.',
            'Installed 0 object(s) from 0 fixture(s)'
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
