"""
Tagulous test: Admin

Modules tested:
    tagulous.admin
"""
from __future__ import absolute_import
import re
import copy

import django
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import CookieStorage
from django.http import HttpRequest, QueryDict

from tests.lib import *


MOCK_PATH = 'mock/path'
def MockRequest(GET=None, POST=None):
    """
    Create a fake Request object based on the GET and POST kwargs
    """
    r = HttpRequest()
    r.path = MOCK_PATH
    r.method = 'POST' if POST is not None else 'GET'
    r.GET = GET or QueryDict('')
    r.POST = POST or QueryDict('')
    r._messages = CookieStorage(r)
    return r
request = MockRequest()

def _monkeypatch_modeladmin():
    """
    ModelAdmin changes between django versions.
    
    Monkeypatch it where necessary to allow tests to function, without making
    any changes to ModelAdmin which would affect the code being tested.
    """
    # Django 1.4 ModelAdmin doesn't have get_list_filter
    # Monkeypatch in; only used to simplify tests
    if not hasattr(admin.ModelAdmin, 'get_list_filter'):
        if django.VERSION >= (1, 5):
            raise AttributeError(
                'Only old versions of django are expected to be missing '
                'ModelAdmin.get_list_filter'
            )
        admin.ModelAdmin.get_list_filter = lambda self, request: self.list_filter
_monkeypatch_modeladmin()


class AdminTestManager(object):
    """
    Add per-test site urls to global urlpatterns
    """
    def setUp(self):
        super(AdminTestManager, self).setUp()
        
        if not hasattr(self, 'site'):
            return
        
        # Try to clear the resolver cache
        try:
            # Django 1.4 - 1.6
            from django.core.urlresolvers import _resolver_cache
        except ImportError:
            # Django 1.7+
            from django.core.urlresolvers import get_resolver
            if hasattr(get_resolver, 'cache_clear'):
                get_resolver.cache_clear()
        else:
            _resolver_cache.clear()
        
        # Store the old urls and make a copy
        self.old_urls = test_urls.urlpatterns
        test_urls.urlpatterns = copy.copy(
            test_urls.urlpatterns
        )
        
        # Add the site to the copy
        from django.conf.urls import include, url
        test_urls.urlpatterns += test_urls.mk_urlpatterns(
            url(r'^tagulous_tests_app/admin/', include(self.site.urls))
        )
        
    def tearDown(self):
        super(AdminTestManager, self).tearDown()
        if not hasattr(self, 'old_urls'):
            return
        
        # Restore the original urls
        test_urls.urlpatterns = self.old_urls


###############################################################################
####### Admin registration
###############################################################################

class AdminRegisterTest(TagTestManager, TestCase):
    """
    Test Admin registration of tagged model
    """
    def setUpExtra(self):
        self.admin = test_admin.SimpleMixedTestAdmin
        self.model = test_models.SimpleMixedTest
        self.model_singletag = self.model.singletag.tag_model
        self.model_tags = self.model.tags.tag_model
        self.site = admin.AdminSite(name='tagulous_admin')
        
    def test_register_site(self):
        "Check register with site"
        self.assertFalse(self.model in self.site._registry)
        tag_admin.register(self.model, self.admin, site=self.site)
        self.assertTrue(self.model in self.site._registry)
        ma = self.site._registry[self.model]
        self.assertIsInstance(ma, tag_admin.TaggedModelAdmin)
    
    def test_register_no_site(self):
        "Check register without site"
        # Replace admin.site with our own
        old_admin_site = admin.site
        admin.site = self.site
        self.assertFalse(self.model in self.site._registry)
        tag_admin.register(self.model, self.admin)
        self.assertTrue(self.model in self.site._registry)
        ma = self.site._registry[self.model]
        self.assertIsInstance(ma, tag_admin.TaggedModelAdmin)
        
        # Return admin.site
        admin.site = old_admin_site
    
    def test_register_models(self):
        "Check register refuses multple models"
        with self.assertRaises(exceptions.ImproperlyConfigured) as cm:
            tag_admin.register([self.model, self.model], self.admin, site=self.site)
        self.assertEqual(
            str(cm.exception),
            'Tagulous can only register a single model with admin.',
        )
        self.assertFalse(self.model in self.site._registry)
        
    def test_register_auto(self):
        "Check register without admin dynamically creates admin class"
        self.assertFalse(self.model in self.site._registry)
        tag_admin.register(self.model, site=self.site)
        self.assertTrue(self.model in self.site._registry)
        ma = self.site._registry[self.model]
        self.assertIsInstance(ma, tag_admin.TaggedModelAdmin)
    
    def test_register_options(self):
        "Check register with options dynamically creates admin class"
        self.assertFalse(self.model in self.site._registry)
        tag_admin.register(
            self.model, self.admin, site=self.site,
            list_display=['name']
        )
        self.assertTrue(self.model in self.site._registry)
        ma = self.site._registry[self.model]
        self.assertIsInstance(ma, tag_admin.TaggedModelAdmin)
        self.assertItemsEqual(ma.get_list_display(request), ['name'])

    def test_register_tag_descriptor(self):
        "Check register tag descriptor creates correct admin class"
        self.assertFalse(self.model_singletag in self.site._registry)
        tag_admin.register(self.model.singletag, self.admin, site=self.site)
        self.assertTrue(self.model_singletag in self.site._registry)
        ma = self.site._registry[self.model_singletag]
        self.assertIsInstance(ma, tag_admin.TagModelAdmin)

    def test_register_tag_model(self):
        "Check register tag model creates correct admin class"
        self.assertFalse(self.model_singletag in self.site._registry)
        tag_admin.register(self.model_singletag, site=self.site)
        self.assertTrue(self.model_singletag in self.site._registry)
        ma = self.site._registry[self.model_singletag]
        self.assertIsInstance(ma, tag_admin.TagModelAdmin)
    
    def test_register_tag_model_class_properties(self):
        """
        Check list_display, list_filter, exclude and actions can be set in a
        tag modeladmin which doesn't explicitly subclass TagModelAdmin
        """
        # register class SimpleMixedTestTagsAdmin(admin.ModelAdmin):
        # against self.model
        self.assertFalse(self.model.singletag.tag_model in self.site._registry)
        tag_admin.register(
            self.model.singletag.tag_model,
            test_admin.SimpleMixedTestTagsAdmin,
            site=self.site,
        )
        self.assertTrue(self.model.singletag.tag_model in self.site._registry)
        ma = self.site._registry[self.model.singletag.tag_model]
        self.assertIsInstance(ma, tag_admin.TagModelAdmin)
        self.assertEqual(ma.list_display, ['name'])
        self.assertEqual(ma.list_filter, ['count'])
        self.assertEqual(ma.exclude, ['name'])
        self.assertEqual(ma.actions, [])
    
    def test_register_tag_tree_model(self):
        "Check register tag tree model creates correct admin class"
        tag_model = test_models.TreeTest.tags.tag_model
        self.assertFalse(tag_model in self.site._registry)
        tag_admin.register(tag_model, site=self.site)
        self.assertTrue(tag_model in self.site._registry)
        ma = self.site._registry[tag_model]
        self.assertIsInstance(ma, tag_admin.TagModelAdmin)


###############################################################################
####### Tagged ModelAdmin
###############################################################################

class TaggedAdminTest(AdminTestManager, TagTestManager, TestCase):
    """
    Test ModelAdmin enhancements
    """
    def setUpExtra(self):
        self.admin = test_admin.SimpleMixedTestAdmin
        self.model = test_models.SimpleMixedTest
        self.model_singletag = self.model.singletag.tag_model
        self.model_tags = self.model.tags.tag_model
        self.site = admin.AdminSite(name='tagulous_admin')
        tag_admin.register(self.model, self.admin, site=self.site)
        self.ma = self.site._registry[self.model]
        self.cl = None
    
    def get_changelist(self, req=request):
        list_display = self.ma.get_list_display(req)
        list_display_links = self.ma.get_list_display_links(req, list_display)
        list_filter = self.ma.get_list_filter(req)
        ChangeList = self.ma.get_changelist(req)
        self.cl = ChangeList(req, self.model, list_display,
            list_display_links, list_filter, self.ma.date_hierarchy,
            self.ma.search_fields, self.ma.list_select_related,
            self.ma.list_per_page, self.ma.list_max_show_all, self.ma.list_editable,
            self.ma
        )
        return self.cl
        
    def get_changelist_results(self, req=request):
        self.get_changelist(req)
        results = self.cl.get_results(req)
        return self.cl.result_list
    
    
    #
    # Tests
    #
    
    def test_changelist_display(self):
        "Check display fields have registered ok and return valid values"
        t1 = self.model.objects.create(name='Test 1', singletag='Mr', tags='red, blue')
        self.assertItemsEqual(
            self.ma.get_list_display(request),
            ['name', 'singletag', '_tagulous_display_tags'],
        )
        results = self.get_changelist_results()
        self.assertEqual(len(results), 1)
        r1 = results[0]
        self.assertEqual(t1.pk, r1.pk)
        
        # Find what it's showing
        from django.contrib.admin.templatetags.admin_list import items_for_result
        row = [
            list(items_for_result(self.cl, result, None))
            for result in results
        ][0]
        
        # Before comparing, strip class attrs
        row = [
            re.sub(r' class=".+?"', '', r)
            for r in row
        ]
        self.assertItemsEqual(row, [
            u'<td>Test 1</td>',
            u'<td>Mr</td>',
            u'<td>blue, red</td>',
        ])
    
    def test_changelist_filter(self):
        t1 = self.model.objects.create(name='Test 1', singletag='Mr', tags='red, blue')
        t2 = self.model.objects.create(name='Test 2', singletag='Mrs', tags='red, green')
        t3 = self.model.objects.create(name='Test 3', singletag='Mr', tags='green, blue')
        
        # Check filters are listed
        self.assertItemsEqual(
            self.ma.get_list_filter(request),
            ['singletag', 'tags'],
        )
        
        # Filter by singletag
        singletag_request = MockRequest(GET={
            'singletag__id__exact': self.model_singletag.objects.get(name='Mr').pk,
        })
        results = sorted(
            self.get_changelist_results(singletag_request),
            key=lambda r: r.name
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].pk, t1.pk)
        self.assertEqual(results[1].pk, t3.pk)
        
        # Filter by tag
        tag_request = MockRequest(GET={
            'tags__id__exact': self.model_tags.objects.get(name='green').pk,
        })
        results = sorted(
            self.get_changelist_results(tag_request),
            key=lambda r: r.name
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].pk, t2.pk)
        self.assertEqual(results[1].pk, t3.pk)
    
    def test_form_fields(self):
        "Check forms get the correct widget"
        db_singletag = self.model._meta.get_field('singletag')
        field_singletag = self.ma.formfield_for_dbfield(db_singletag)
        self.assertIsInstance(field_singletag.widget, tag_forms.AdminTagWidget)
        
        db_tags = self.model._meta.get_field('tags')
        field_tags = self.ma.formfield_for_dbfield(db_tags)
        self.assertIsInstance(field_tags.widget, tag_forms.AdminTagWidget)


###############################################################################
####### Tag ModelAdmin
###############################################################################

class TagAdminTest(AdminTestManager, TagTestManager, TestCase):
    """
    Test Admin registration of a tag model
    """
    def setUpExtra(self):
        self.tagged_model = test_models.SimpleMixedTest
        self.model = self.tagged_model.tags.tag_model
        self.site = admin.AdminSite(name='tagulous_admin')
        tag_admin.register(self.model, site=self.site)
        self.ma = self.site._registry[self.model]
        self.cl = None
        
    def get_changelist(self, req=request):
        list_display = self.ma.get_list_display(req)
        list_display_links = self.ma.get_list_display_links(req, list_display)
        list_filter = self.ma.get_list_filter(req)
        ChangeList = self.ma.get_changelist(req)
        self.cl = ChangeList(req, self.model, list_display,
            list_display_links, list_filter, self.ma.date_hierarchy,
            self.ma.search_fields, self.ma.list_select_related,
            self.ma.list_per_page, self.ma.list_max_show_all, self.ma.list_editable,
            self.ma
        )
        return self.cl
    
    def get_cl_queryset(self, cl, request):
        "Because ModelAdmin.get_query_set is deprecated in 1.6"
        if hasattr(cl, 'get_queryset'):
            return cl.get_queryset(request)
        return cl.get_query_set(request)
    
    def populate(self):
        self.o1 = self.tagged_model.objects.create(
            name='Test 1', singletag='Mr', tags='red, blue',
        )
        self.o2 = self.tagged_model.objects.create(
            name='Test 2', singletag='Mrs', tags='red, green',
        )
        self.o3 = self.tagged_model.objects.create(
            name='Test 3', singletag='Mr', tags='green, blue',
        )
        self.red = self.model.objects.get(name='red')
        self.blue = self.model.objects.get(name='blue')
        self.green = self.model.objects.get(name='green')
        
    def assertContains(self, content, *seeks):
        for seek in seeks:
            self.assertTrue(seek in content, msg='Missing %s' % seek)
    
    def assertNotContains(self, content, *seeks):
        for seek in seeks:
            self.assertFalse(seek in content, msg='Unexpected %s' % seek)
    
    
    #
    # Tests
    #
    
    def test_merge_action(self):
        "Check merge_tags action exists"
        self.assertTrue('merge_tags' in self.ma.actions)
        actions = self.ma.get_actions(request)
        self.assertTrue('merge_tags' in actions)
        self.assertTrue(hasattr(actions['merge_tags'][0], '__call__'))
        self.assertEqual(actions['merge_tags'][1], 'merge_tags')
        self.assertEqual(actions['merge_tags'][2], 'Merge selected tags...')
    
    def test_merge_form_empty(self):
        "Check the merge_tags action fails when no tags selected"
        request = MockRequest(POST=QueryDict('action=merge_tags'))
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, self.get_cl_queryset(cl, request))
        msgs = list(messages.get_messages(request))
        
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].message, (
            'Items must be selected in order to perform actions on them. No '
            'items have been changed.'
        ))
        self.assertEqual(response, None)
        
    def test_merge_form_one(self):
        "Check the merge_tags action fails when only one tag selected"
        self.populate()
        request = MockRequest(POST=QueryDict(
            'action=merge_tags&%s=%s' % (admin.ACTION_CHECKBOX_NAME, self.red.pk)
        ))
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, self.get_cl_queryset(cl, request))
        msgs = list(messages.get_messages(request))

        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0].message, 'You must select at least two tags to merge'
        )
        self.assertTrue('Location: %s' % MOCK_PATH in str(response))

    def test_merge_form_two(self):
        "Check the merge_tags form when two tag selected"
        self.populate()
        request = MockRequest(POST=QueryDict('&'.join(
            ['action=merge_tags'] + [
                '%s=%s' % (admin.ACTION_CHECKBOX_NAME, pk)
                for pk in [self.red.pk, self.green.pk]
            ]
        )))
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, self.get_cl_queryset(cl, request))
        msgs = list(messages.get_messages(request))
        
        # Check response is appropriate
        # Django 1.4 doesn't support assertInHTML, so have to do it manually
        self.assertEqual(len(msgs), 0)
        content = str(response)
        content_form = content[
            content.index('<form ') : content.index('</form>') + 7
        ]
        self.assertHTMLEqual(
            content_form[:content_form.index('<option')],
            (
                '<form action="" method="POST">'
                '<p><label for="id_merge_to">Merge to:</label>'
                '<select id="id_merge_to" name="merge_to">'
            )
        )
        
        # Can't be sure of options order
        options_raw = content_form[
            content_form.index('<option') : content_form.index('</select>')
        ]
        option1 = options_raw[:options_raw.index('<option', 1)]
        option2 = options_raw[len(option1):options_raw.index('<option', len(option1)+1)]
        option3 = options_raw[len(option1) + len(option2):]
        options = [option.strip() for option in [option1, option2, option3]]
        self.assertTrue(
            '<option value="" selected="selected">---------</option>' in options
        )
        self.assertTrue(
            '<option value="%d">%s</option>' % (self.red.pk, self.red.name) in options
        )
        self.assertTrue(
            '<option value="%d">%s</option>' % (self.green.pk, self.green.name) in options
        )
        
        # Check _selected_action input tags
        inputs_raw = content_form[
            # First input, convenient
            content_form.index('<input') : content_form.index('<div>')
        ]
        input1 = inputs_raw[:inputs_raw.index('<input', 1)]
        input2 = inputs_raw[len(input1):]
        inputs = [
            # Some versions of django may insert a </p> here.
            input_tag.replace('</p>', '').strip()
            for input_tag in [input1, input2]
        ]
        self.assertTrue(any('id="id__selected_action_0"' in i for i in inputs))
        self.assertTrue(any('id="id__selected_action_1"' in i for i in inputs))
        for input_tag in inputs:
            input_tag = re.sub(
                'id__selected_action_\d', 'id__selected_action_x', input_tag,
            )
            expected = (
                '<input id="id__selected_action_x" type="hidden"'
                ' name="_selected_action" value="%d" />'
            )
            try:
                self.assertHTMLEqual(input_tag, expected % self.red.pk)
            except AssertionError:
                self.assertHTMLEqual(input_tag, expected % self.green.pk)
        
        # Check end of form
        self.assertHTMLEqual(
            content_form[
                content_form.index('<div>') : content_form.index('</div>')
            ], (
                '<div>'
                '<input type="submit" name="merge" value="Merge tags">'
                '<input class="default" type="hidden" name="action"'
                ' value="merge_tags">'
                '</div>'
            )
        )
        
        # And just confirm blue wasn't there
        self.assertNotContains(
            content,
            '<option value="%d">%s</option>' % (self.blue.pk, self.blue.name),
        )
    
    def test_merge_form_submit(self):
        self.populate()
        request = MockRequest(POST=QueryDict('&'.join(
            [
                # Submitting
                'action=merge_tags',
                'merge=Merge%%20Tags',
            ] + [
                # These were selected on the changelist, the ones we're merging
                '%s=%s' % (admin.ACTION_CHECKBOX_NAME, pk)
                for pk in [self.red.pk, self.green.pk]
            ] + [
                # This is the one we're merging to
                'merge_to=%s' % self.red.pk,
            ]
        )))
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, self.get_cl_queryset(cl, request))
        msgs = list(messages.get_messages(request))
        
        # Check response is appropriate
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0].message, 'Tags merged'
        )
        self.assertTrue('Location: %s' % MOCK_PATH in str(response))


###############################################################################
####### Tagged inlines on tag ModelAdmin
###############################################################################

class TaggedInlineSingleAdminTest(AdminTestManager, TagTestManager, TestCase):
    """
    Test inlines of tagged models on tag modeladmins
    """
    admin_cls       = test_admin.SimpleMixedTestSingletagAdmin
    tagged_model    = test_models.SimpleMixedTest
    model           = test_models.SimpleMixedTest.singletag.tag_model
    
    def setUpExtra(self):
        self.site = admin.AdminSite(name='tagulous_admin')
        tag_admin.register(self.model, admin_class=self.admin_cls, site=self.site)
        self.ma = self.site._registry[self.model]
        self.cl = None
        
        # Set up client
        User.objects.create_superuser('test', 'test@example.com', 'user')
        result = self.client.login(username='test', password='user')
        self.assertEqual(result, True)
        
    def tearDownExtra(self):
        test_urls.urlpatterns = self.old_urls
        self.client.logout()
    
    def get_url(self, name, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        return reverse(
            'admin:%s_%s_%s' % (content_type.app_label, content_type.model, name),
            args=args, kwargs=kwargs
        )
    
    
    #
    # Tests
    #
    
    def test_add_renders(self):
        "Check inline add renders without error"
        response = self.client.get(self.get_url('add'))
        self.assertContains(response, '<h2>Simple mixed tests</h2>')
        # assertHTMLEquals isn't going to be particularly helpful here
        # Just check that a few attributes exist, to indicate all is well
        # Real test will be done in next test
        self.assertContains(response, 'id="id_simplemixedtest_set-TOTAL_FORMS')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-singletag"')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-name"')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-tags"')
        # There should be 3 empty fields, zero-indexed
        self.assertContains(response, 'id="id_simplemixedtest_set-2-singletag"')
        self.assertNotContains(response, 'id="id_simplemixedtest_set-3-singletag"')
    
    def test_add_submits(self):
        "Check inline add saves without error, and increments tag model"
        data = {
            'simplemixedtest_set-TOTAL_FORMS': 3,
            'simplemixedtest_set-INITIAL_FORMS': 0,
            'simplemixedtest_set-MAX_NUM_FORMS': 1000,
            '_save': u'Save',
            'name': 'Mr',
            'slug': 'mr',
            'simplemixedtest_set-0-name': 'Test 1',
            'simplemixedtest_set-0-tags': 'tag1, tag2',
        }
        response = self.client.post(self.get_url('add'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tagged_model.objects.count(), 1)
        
        t1 = self.tagged_model.objects.get(name='Test 1')
        self.assertInstanceEqual(t1, name='Test 1', singletag='Mr', tags=['tag1', 'tag2'])
        self.assertTagModel(self.model, {'Mr': 1})
        self.assertTagModel(self.tagged_model.tags.tag_model, {
            'tag1': 1,
            'tag2': 1,
        })
    
    def test_edit_renders(self):
        "Check inline edit renders without error"
        obj1 = self.tagged_model.objects.create(
            name='Test 1', singletag='Mr', tags=['tag1', 'tag2'],
        )
                
        response = self.client.get(self.get_url('change', obj1.singletag.pk))
        self.assertContains(response, '<h2>Simple mixed tests</h2>')
        self.assertContains(response, 'id="id_simplemixedtest_set-TOTAL_FORMS')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-singletag"')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-name"')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-tags"')
        # There should be 1 full field and 3 empty fields, zero-indexed
        self.assertContains(response, 'id="id_simplemixedtest_set-3-singletag"')
        self.assertNotContains(response, 'id="id_simplemixedtest_set-4-singletag"')
        
        # Check the fk is an id, to confirm it's using TaggedInlineFormSet
        html = response.content
        i_name = html.index('name="simplemixedtest_set-0-singletag"')
        i_open = html.rindex('<', 0, i_name)
        i_close = html.index('>', i_name)
        self.assertHTMLEqual(html[i_open : i_close + 1], (
            '<input type="hidden" name="simplemixedtest_set-0-singletag" '
            'value="1" id="id_simplemixedtest_set-0-singletag" />'
        ))
        
    
    def test_edit_saves(self):
        """
        Check inline edit saves without error
        
        Also check changing tag fields in inlines
        """
        # Create and confirm
        obj1 = self.tagged_model.objects.create(
            name='Test 1', singletag='Mr', tags=['tag1', 'tag2'],
        )
        obj2 = self.tagged_model.objects.create(
            name='Test 2', singletag='Mr', tags=['tag3', 'tag4'],
        )
        tag1 = obj1.singletag
        self.assertEqual(self.tagged_model.objects.count(), 2)
        self.assertTagModel(self.model, {'Mr': 2})
        self.assertTagModel(self.tagged_model.tags.tag_model, {
            'tag1': 1, 'tag2': 1, 'tag3': 1, 'tag4': 1,
        })
        
        data = {
            'simplemixedtest_set-TOTAL_FORMS': 5,
            'simplemixedtest_set-INITIAL_FORMS': 2,
            'simplemixedtest_set-MAX_NUM_FORMS': 1000,
            '_save': u'Save',
            'name': 'Mr',
            'slug': 'mr',
            
            'simplemixedtest_set-0-name':   'Test 1e',
            'simplemixedtest_set-0-tags':   'tag1, tag2e',
            'simplemixedtest_set-0-id':     '%d' % obj1.pk,
            'simplemixedtest_set-0-singletag': '%d' % tag1.pk,
            'simplemixedtest_set-0-DELETE': '',
            
            'simplemixedtest_set-1-name':   'Test 2e',
            'simplemixedtest_set-1-tags':   'tag3, tag4e',
            'simplemixedtest_set-1-id':     '%d' % obj2.pk,
            'simplemixedtest_set-1-singletag': '%d' % tag1.pk,
            'simplemixedtest_set-1-DELETE': '',
        }
        response = self.client.post(
            self.get_url('change', tag1.pk), data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tagged_model.objects.count(), 2)
        
        self.assertInstanceEqual(
            obj1, name='Test 1e', singletag='Mr', tags=['tag1', 'tag2e'],
        )
        self.assertInstanceEqual(
            obj2, name='Test 2e', singletag='Mr', tags=['tag3', 'tag4e'],
        )
        
        self.assertTagModel(self.model, {'Mr': 2})
        self.assertTagModel(self.tagged_model.tags.tag_model, {
            'tag1': 1, 'tag2e': 1, 'tag3': 1, 'tag4e': 1,
        })

