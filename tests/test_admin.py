"""
Tagulous test: Admin

Modules tested:
    tagulous.admin
"""

import copy
import re
from typing import cast

import django
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import CookieStorage
from django.core import exceptions
from django.forms import Media
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from django.urls import get_resolver, re_path, reverse
from django.urls.resolvers import _get_cached_resolver
from django.utils.datastructures import MultiValueDict

from tagulous import admin as tag_admin
from tagulous import forms as tag_forms
from tests.lib import TagTestManager, tagfield_html
from tests.tagulous_tests_app import admin as test_admin
from tests.tagulous_tests_app import models as test_models
from tests.tagulous_tests_app import urls as test_urls

MOCK_PATH = "mock/path"


def dict_to_querydict(data: dict | QueryDict | None) -> QueryDict:
    if isinstance(data, QueryDict):
        return data
    qd = QueryDict("", mutable=True)
    if data:
        for key, value in data.items():
            qd[key] = value
    return qd


class TestRequestMixin(object):
    def mock_request(
        self, GET: dict | QueryDict | None = None, POST: dict | QueryDict | None = None
    ):
        """
        Create a fake Request object based on the GET and POST kwargs
        """
        r = HttpRequest()
        r.path = MOCK_PATH
        r.method = "POST" if POST is not None else "GET"
        r.GET = dict_to_querydict(GET)
        r.POST = dict_to_querydict(POST)
        r._messages = CookieStorage(r)
        r.user = User.objects.get_or_create(username="test_user")[0]
        return r


class AdminTestManager(object):
    """
    Add per-test site urls to global urlpatterns
    """

    def setUp(self):
        super(AdminTestManager, self).setUp()

        if not hasattr(self, "site"):
            return

        # Try to clear the resolver cache
        _get_cached_resolver.cache_clear()

        # Store the old urls and make a copy
        self.old_urls = test_urls.urlpatterns
        test_urls.urlpatterns = copy.copy(test_urls.urlpatterns)

        # Add the site to the copy
        test_urls.urlpatterns += [
            re_path(r"^tagulous_tests_app/admin/", self.site.urls)
        ]

    def tearDown(self):
        super(AdminTestManager, self).tearDown()
        if not hasattr(self, "old_urls"):
            return

        # Restore the original urls
        test_urls.urlpatterns = self.old_urls


# ##############################################################################
# ###### Admin registration
# ##############################################################################


class AdminRegisterTest(TestRequestMixin, TagTestManager, TestCase):
    """
    Test Admin registration of tagged model
    """

    def setUpExtra(self):
        self.admin = test_admin.SimpleMixedTestAdmin
        self.model = test_models.SimpleMixedTest
        self.model_singletag = self.model.singletag.tag_model
        self.model_tags = self.model.tags.tag_model
        self.site = admin.AdminSite(name="tagulous_admin")

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
        "Check register refuses multiple models"
        with self.assertRaises(exceptions.ImproperlyConfigured) as cm:
            tag_admin.register([self.model, self.model], self.admin, site=self.site)
        self.assertEqual(
            str(cm.exception),
            "Tagulous can only register a single model with admin.",
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
            self.model, self.admin, site=self.site, list_display=["name"]
        )
        self.assertTrue(self.model in self.site._registry)
        ma = self.site._registry[self.model]
        self.assertIsInstance(ma, tag_admin.TaggedModelAdmin)
        self.assertSequenceEqual(ma.get_list_display(self.mock_request()), ["name"])

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
        self.assertEqual(ma.list_display, ("name",))
        self.assertEqual(ma.list_filter, ["count"])
        self.assertEqual(ma.exclude, ["name"])
        self.assertEqual(ma.actions, [])

    def test_register_tag_tree_model(self):
        "Check register tag tree model creates correct admin class"
        tag_model = test_models.TreeTest.tags.tag_model
        self.assertFalse(tag_model in self.site._registry)
        tag_admin.register(tag_model, site=self.site)
        self.assertTrue(tag_model in self.site._registry)
        ma = self.site._registry[tag_model]
        self.assertIsInstance(ma, tag_admin.TagModelAdmin)


# ##############################################################################
# ###### Tagged ModelAdmin
# ##############################################################################


class TaggedAdminTest(TestRequestMixin, AdminTestManager, TagTestManager, TestCase):
    """
    Test ModelAdmin enhancements
    """

    def setUpExtra(self):
        self.admin = test_admin.SimpleMixedTestAdmin
        self.model = test_models.SimpleMixedTest
        self.model_singletag = self.model.singletag.tag_model
        self.model_tags = self.model.tags.tag_model
        self.site = admin.AdminSite(name="tagulous_admin")
        tag_admin.register(self.model, self.admin, site=self.site)
        self.ma = self.site._registry[self.model]
        self.cl = None

    def get_changelist(self, req=None):
        if not req:
            req = self.mock_request()
        list_display = self.ma.get_list_display(req)
        list_display_links = self.ma.get_list_display_links(req, list_display)
        list_filter = self.ma.get_list_filter(req)
        ChangeList = self.ma.get_changelist(req)
        changelist_args = [
            req,
            self.model,
            list_display,
            list_display_links,
            list_filter,
            self.ma.date_hierarchy,
            self.ma.search_fields,
            self.ma.list_select_related,
            self.ma.list_per_page,
            self.ma.list_max_show_all,
            self.ma.list_editable,
            self.ma,
            self.ma.get_sortable_by(req),
        ]
        if django.VERSION >= (4, 0, 0):
            changelist_args.extend(
                [
                    self.ma.search_help_text,
                ]
            )
        self.cl = ChangeList(*changelist_args)
        return self.cl

    def get_changelist_results(self, req=None):
        if not req:
            req = self.mock_request()
        self.get_changelist(req)
        self.cl.get_results(req)
        return self.cl.result_list

    #
    # Tests
    #

    def test_changelist_display(self):
        "Check display fields have registered ok and return valid values"
        t1 = self.model.objects.create(name="Test 1", singletag="Mr", tags="red, blue")
        self.assertSequenceEqual(
            self.ma.get_list_display(self.mock_request()),
            ["name", "singletag", "_tagulous_display_tags"],
        )
        results = self.get_changelist_results()
        self.assertEqual(len(results), 1)
        r1 = results[0]
        self.assertEqual(t1.pk, r1.pk)

        # Find what it's showing
        from django.contrib.admin.templatetags.admin_list import items_for_result

        row = [list(items_for_result(self.cl, result, None)) for result in results][0]

        # Before comparing, strip class attrs
        row = [re.sub(r' class=".+?"', "", r) for r in row]
        self.assertSequenceEqual(
            row, ["<td>Test 1</td>", "<td>Mr</td>", "<td>blue, red</td>"]
        )

    def test_changelist_filter(self):
        t1 = self.model.objects.create(name="Test 1", singletag="Mr", tags="red, blue")
        t2 = self.model.objects.create(
            name="Test 2", singletag="Mrs", tags="red, green"
        )
        t3 = self.model.objects.create(
            name="Test 3", singletag="Mr", tags="green, blue"
        )

        # Check filters are listed
        self.assertSequenceEqual(
            self.ma.get_list_filter(self.mock_request()), ["singletag", "tags"]
        )

        # Filter by singletag
        singletag_request = self.mock_request(
            GET={"singletag__id__exact": self.model_singletag.objects.get(name="Mr").pk}
        )
        results = sorted(
            self.get_changelist_results(singletag_request), key=lambda r: r.name
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].pk, t1.pk)
        self.assertEqual(results[1].pk, t3.pk)

        # Filter by tag
        tag_request = self.mock_request(
            GET={"tags__id__exact": self.model_tags.objects.get(name="green").pk}
        )
        results = sorted(self.get_changelist_results(tag_request), key=lambda r: r.name)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].pk, t2.pk)
        self.assertEqual(results[1].pk, t3.pk)

    def test_form_fields(self):
        "Check forms get the correct widget"
        db_singletag = self.model._meta.get_field("singletag")
        field_singletag = self.ma.formfield_for_dbfield(db_singletag)
        self.assertIsInstance(field_singletag.widget, tag_forms.AdminTagWidget)

        db_tags = self.model._meta.get_field("tags")
        field_tags = self.ma.formfield_for_dbfield(db_tags)
        self.assertIsInstance(field_tags.widget, tag_forms.AdminTagWidget)


class TaggedAdminHttpTest(TestRequestMixin, AdminTestManager, TagTestManager, TestCase):
    """
    Test ModelAdmin enhancements via Http
    """

    def setUpExtra(self):
        self.admin = test_admin.SimpleMixedTestAdmin
        self.model = test_models.SimpleMixedTest
        self.model_singletag = self.model.singletag.tag_model
        self.model_tags = self.model.tags.tag_model
        self.site = admin.AdminSite(name="tagulous_admin")
        tag_admin.register(self.model, self.admin, site=self.site)

        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        self.client.login(username="admin", password="password")

    def get_url_name(self, view: str) -> str:
        meta = self.model._meta
        return f"admin:{meta.app_label}_{meta.model_name}_{view}"

    def test_form_field__html_rendered(self):
        "Check form widget JS is present"
        t1 = self.model.objects.create(name="Test 1", singletag="Mr", tags="red, blue")
        url = reverse(self.get_url_name("change"), args=[t1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form", html=False)

        expected_single = (
            '<input type="text" name="singletag" id="id_singletag" value="Mr"'
            ' data-tag-type="single"'
            ' data-theme="admin-autocomplete"'
            ' data-tag-list="[&quot;Mr&quot;]"'
            ' data-tag-options="{&quot;max_count&quot;: 1, &quot;required&quot;: false}"'
            ' data-tagulous="true"'
            ' autocomplete="off">'
        )
        expected_multiple = tagfield_html(
            '<input type="text" name="tags" id="id_tags" value="blue, red"'
            ' data-theme="admin-autocomplete"'
            ' data-tag-list="[&quot;blue&quot;, &quot;red&quot;]"'
            ' data-tag-options="{&quot;required&quot;: false}"'
            ' data-tagulous="true"'
            ' autocomplete="off">'
        )
        if django.VERSION >= (5, 1):
            expected_single = expected_single.replace(
                ">",
                ' data-context="available-source">',
            )
            expected_multiple = expected_multiple.replace(
                ">",
                ' data-context="available-source">',
            )

        self.assertContains(response, expected_single, html=True)
        self.assertContains(response, expected_multiple, html=True)

    def test_form_field__media_js_in_order(self):
        "Check form widget's media JS is present"
        t1 = self.model.objects.create(name="Test 1", singletag="Mr", tags="red, blue")
        url = reverse(self.get_url_name("change"), args=[t1.pk])
        response = self.client.get(url)

        # Check if static files are loaded
        media: Media = response.context["media"]
        actual = media._js
        if django.VERSION >= (4, 0):
            expected = [
                "admin/js/vendor/jquery/jquery.min.js",
                "tagulous/tagulous.js",
                "tagulous/adaptor/select2-4.js",
                "admin/js/jquery.init.js",
            ]

        else:
            # Django 3.2
            expected = [
                "admin/js/vendor/jquery/jquery.min.js",
                "tagulous/tagulous.js",
                "admin/js/vendor/select2/select2.full.min.js",
                "tagulous/adaptor/select2-4.js",
                "admin/js/jquery.init.js",
            ]

        # Check that all expected files are loaded, in the expected order
        found = []
        for actual_file in actual:
            # This should be the next one
            if (
                actual_file == expected[0]
                or actual_file.replace(".min", "") == expected[0]
            ):
                found.append(expected.pop(0))

            if not expected:
                # Found everything
                break

        if expected:
            # Debug info on stdout
            print("Actual:\n  ", "\n  ".join(actual))
            print("Found:\n  ", "\n  ".join(found))
            print("Expected:\n", "\n  ".join(expected))
            self.fail(
                f"Expected JS file not found in order: {actual=} {found=} {expected=}"
            )


# ##############################################################################
# ###### Tag model admin tools
# ##############################################################################


class TagAdminTestManager(TestRequestMixin, AdminTestManager, TagTestManager, TestCase):
    """
    Test Admin registration of a tag model
    """

    def setUpModels(self):
        raise NotImplementedError()

    def setUpExtra(self):
        self.setUpModels()
        self.site = admin.AdminSite(name="tagulous_admin")
        tag_admin.register(self.model, site=self.site)
        self.ma = self.site._registry[self.model]
        self.cl = None

    def get_changelist(self, req=None):
        if not req:
            req = self.mock_request()
        list_display = self.ma.get_list_display(req)
        list_display_links = self.ma.get_list_display_links(req, list_display)
        list_filter = self.ma.get_list_filter(req)
        ChangeList = self.ma.get_changelist(req)
        changelist_args = [
            req,
            self.model,
            list_display,
            list_display_links,
            list_filter,
            self.ma.date_hierarchy,
            self.ma.search_fields,
            self.ma.list_select_related,
            self.ma.list_per_page,
            self.ma.list_max_show_all,
            self.ma.list_editable,
            self.ma,
            self.ma.get_sortable_by(req),
        ]
        if django.VERSION >= (4, 0, 0):
            changelist_args.extend(
                [
                    self.ma.search_help_text,
                ]
            )
        self.cl = ChangeList(*changelist_args)
        return self.cl

    def assertContains(self, content, *seeks):
        for seek in seeks:
            self.assertTrue(seek in content, msg="Missing %s" % seek)

    def assertNotContains(self, content, *seeks):
        for seek in seeks:
            self.assertFalse(seek in content, msg="Unexpected %s" % seek)

    def do_test_merge_form(self, tags, excluded_tags, is_tree=False):
        "Request the form view and check it returns valid expected HTML"
        request = self.mock_request(
            POST=QueryDict(
                "&".join(
                    ["action=merge_tags"]
                    + [
                        "%s=%s" % (admin.helpers.ACTION_CHECKBOX_NAME, tag.pk)
                        for tag in tags
                    ]
                )
            )
        )
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, cl.get_queryset(request))
        msgs = list(messages.get_messages(request))

        # Check response is appropriate
        self.assertEqual(len(msgs), 0)
        content = response.content.decode("utf-8")
        content_form = content[content.index("<form ") : content.index("</form>") + 7]

        # Strip csrfmiddlewaretoken
        content_form = re.sub(
            r"""<input [^>]*name=["']csrfmiddlewaretoken["'][^>]*>""", "", content_form
        )

        # Check HTML up to first <option> tag
        self.assertHTMLEqual(
            content_form[: content_form.index("<option")],
            (
                '<form action="" method="POST">'
                '<p><label for="id_merge_to">Merge to:</label>'
                '<select id="id_merge_to" {{required}}name="merge_to">'
            ),
        )

        # Can't be sure of options order
        options_raw = content_form[
            content_form.index("<option") : content_form.index("</select>")
        ]
        options = [
            "<option %s" % opt.strip() for opt in options_raw.split("<option ") if opt
        ]
        self.assertTrue('<option value="" selected>---------</option>' in options)

        for tag in tags:
            self.assertContains(
                options, '<option value="%d">%s</option>' % (tag.pk, tag.name)
            )

        # Find remaining input tags
        inputs_raw = content_form[
            # First input, convenient
            content_form.index("<input") : content_form.index("<div>")
        ]

        # If it's a tree, it should have merge_children first
        if is_tree:
            merge_children_label = (
                '<label for="id_merge_children">Merge children:</label>'
            )
            self.assertContains(content_form, merge_children_label)
            merge_children_input, inputs_raw = inputs_raw.split(">", 1)
            self.assertHTMLEqual(
                merge_children_input + ">",
                (
                    '<input type="checkbox" name="merge_children" '
                    'id="id_merge_children" checked="checked">'
                ),
            )

        # Remaining input tags should be tag ids selected on previous page
        inputs = [
            "<input %s" % inpt.strip()
            for inpt in
            # Some versions of django may insert a </p> here.
            inputs_raw.replace("</p>", "").strip().split("<input ")
            if inpt
        ]
        for action_id in range(len(tags)):
            self.assertTrue(
                any(
                    'id="id__selected_action_%s"' % action_id in input_tag
                    for input_tag in inputs
                )
            )

        # Now check the tag IDs are all there
        found_tag_pks = []
        for input_tag in inputs:
            # First check tag is expected format (numbers change)
            self.assertHTMLEqual(
                re.sub(r"\d+", "X", input_tag),
                (
                    '<input id="id__selected_action_X" type="hidden"'
                    ' name="_selected_action" value="X" />'
                ),
            )
            # Now find ID
            matches = re.search(r'value="(\d+)"', input_tag)
            if not matches:
                raise ValueError("Could not find tag pk in %s" % input_tag)
            found_tag_pks.append(int(matches.group(1)))
        self.assertEqual(set(found_tag_pks), set([tag.pk for tag in tags]))

        # Check end of form
        self.assertHTMLEqual(
            content_form[content_form.index("<div>") : content_form.index("</div>")],
            (
                "<div>"
                '<input type="submit" name="merge" value="Merge tags">'
                '<input class="default" type="hidden" name="action"'
                ' value="merge_tags">'
                "</div>"
            ),
        )

        # And just confirm excluded tags weren't there
        for tag in excluded_tags:
            self.assertNotContains(
                content, '<option value="%d">%s</option>' % (tag.pk, tag.name)
            )

    def do_form_submit(self, tags, merge_to, params=None):
        "Submit the form and check it succeeds and returns valid expected HTML"
        if params is None:
            params = []
        request = self.mock_request(
            POST=QueryDict(
                "&".join(
                    [
                        # Submitting
                        "action=merge_tags",
                        "merge=Merge%%20Tags",
                    ]
                    + [
                        # These were selected on the changelist, the ones we're merging
                        "%s=%s" % (admin.helpers.ACTION_CHECKBOX_NAME, tag.pk)
                        for tag in tags
                    ]
                    + [
                        # This is the one we're merging to
                        "merge_to=%s" % merge_to.pk
                    ]
                    + params
                )
            )
        )
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, cl.get_queryset(request))
        msgs = list(messages.get_messages(request))

        # Check response is appropriate
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].message, "Tags merged")

        if django.VERSION >= (3, 2):
            location = response.headers["location"]
        else:
            location = response._headers["location"][1]
        self.assertEqual(location, MOCK_PATH)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   TagModel admin tools
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagAdminTest(TagAdminTestManager, TestRequestMixin):
    """
    Test TagModel admin tools
    """

    def setUpModels(self):
        self.tagged_model = test_models.SimpleMixedTest
        self.model = self.tagged_model.tags.tag_model

    def populate(self):
        self.o1 = self.tagged_model.objects.create(
            name="Test 1", singletag="Mr", tags="red, blue"
        )
        self.o2 = self.tagged_model.objects.create(
            name="Test 2", singletag="Mrs", tags="red, green"
        )
        self.o3 = self.tagged_model.objects.create(
            name="Test 3", singletag="Mr", tags="green, blue"
        )
        self.red = self.model.objects.get(name="red")
        self.blue = self.model.objects.get(name="blue")
        self.green = self.model.objects.get(name="green")

        self.assertTagModel(self.model, {"red": 2, "blue": 2, "green": 2})

    def test_merge_action(self):
        "Check merge_tags action exists"
        self.assertTrue("merge_tags" in self.ma.actions)
        request = self.mock_request()
        actions = self.ma.get_actions(request)
        self.assertTrue("merge_tags" in actions)
        self.assertTrue(hasattr(actions["merge_tags"][0], "__call__"))
        self.assertEqual(actions["merge_tags"][1], "merge_tags")
        self.assertEqual(actions["merge_tags"][2], "Merge selected tags...")

    def test_merge_form_empty(self):
        "Check the merge_tags action fails when no tags selected"
        request = self.mock_request(POST=QueryDict("action=merge_tags"))
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, cl.get_queryset(request))
        msgs = list(messages.get_messages(request))

        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0].message,
            (
                "Items must be selected in order to perform actions on them. No "
                "items have been changed."
            ),
        )
        self.assertEqual(response, None)

    def test_merge_form_one(self):
        "Check the merge_tags action fails when only one tag selected"
        self.populate()
        request = self.mock_request(
            POST=QueryDict(
                "action=merge_tags&%s=%s"
                % (admin.helpers.ACTION_CHECKBOX_NAME, self.red.pk)
            )
        )
        cl = self.get_changelist(request)
        response = self.ma.response_action(request, cl.get_queryset(request))
        msgs = list(messages.get_messages(request))

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].message, "You must select at least two tags to merge")

        if django.VERSION >= (3, 2):
            location = response.headers["location"]
        else:
            location = response._headers["location"][1]
        self.assertEqual(location, MOCK_PATH)

    def test_merge_form_two(self):
        "Check the merge_tags form when two tag selected"
        self.populate()
        self.do_test_merge_form(
            tags=[self.red, self.green], excluded_tags=[self.blue], is_tree=False
        )

    def test_merge_form_submit(self):
        "Check the merge_tag form submits and merges"
        self.populate()
        self.do_form_submit(tags=[self.red, self.green], merge_to=self.red)

        # Check they're merged
        self.assertTagModel(self.model, {"red": 3, "blue": 2})
        self.assertInstanceEqual(
            self.o1, name="Test 1", singletag="Mr", tags="blue, red"
        )
        self.assertInstanceEqual(self.o2, name="Test 2", singletag="Mrs", tags="red")
        self.assertInstanceEqual(
            self.o3, name="Test 3", singletag="Mr", tags="blue, red"
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   TagTreeModel admin tools
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagTreeAdminTest(TagAdminTestManager):
    """
    Test admin tools specific to TagTreeModel
    """

    def setUpModels(self):
        self.tagged_model = test_models.CustomTreeTest
        self.model = test_models.CustomTagTree

    def populate(self):
        # Normal Animal leaf nodes
        self.tagged_model.objects.create(name="cat1", tags="Animal/Mammal/Cat")
        self.tagged_model.objects.create(name="dog1", tags="Animal/Mammal/Dog")
        self.tagged_model.objects.create(name="bee1", tags="Animal/Insect/Bee")

        # Pet tree has Cat leaf and extra L2 not in Animal
        self.tagged_model.objects.create(name="cat2", tags="Pet/Mammal/Cat")
        self.tagged_model.objects.create(name="robin1", tags="Pet/Bird/Robin")

        # Food tree has Cat leaf and extra L3 not in Animal
        self.tagged_model.objects.create(name="cat3", tags="Food/Mammal/Cat")
        self.tagged_model.objects.create(name="pig1", tags="Food/Mammal/Pig")

        self.assertTagModel(
            self.model,
            {
                "Animal": 0,
                "Animal/Insect": 0,
                "Animal/Insect/Bee": 1,
                "Animal/Mammal": 0,
                "Animal/Mammal/Cat": 1,
                "Animal/Mammal/Dog": 1,
                "Pet": 0,
                "Pet/Mammal": 0,
                "Pet/Mammal/Cat": 1,
                "Pet/Bird": 0,
                "Pet/Bird/Robin": 1,
                "Food": 0,
                "Food/Mammal": 0,
                "Food/Mammal/Cat": 1,
                "Food/Mammal/Pig": 1,
            },
        )

    def test_merge_form(self):
        """
        Check merge_tags adds merge_children option
        """
        self.populate()
        tag_names = ["Animal/Mammal", "Pet/Mammal", "Food/Mammal"]
        excluded_tags = self.model.objects.exclude(name__in=tag_names)
        self.assertEqual(
            excluded_tags.count(), self.model.objects.all().count() - len(tag_names)
        )

        self.do_test_merge_form(
            tags=self.model.objects.filter(name__in=tag_names),
            excluded_tags=excluded_tags,
            is_tree=True,
        )

    def test_merge_form_l2_without_children_submit(self):
        self.populate()

        # Tag something with 'Pet/Mammal'
        t1 = self.tagged_model.objects.create(name="mammal1", tags="Pet/Mammal")
        self.assertEqual(self.model.objects.get(name="Pet/Mammal").count, 1)

        # Now merge
        tag_names = ["Animal/Mammal", "Pet/Mammal", "Food/Mammal"]
        self.do_form_submit(
            tags=self.model.objects.filter(name__in=tag_names),
            merge_to=self.model.objects.get(name="Animal/Mammal"),
        )

        self.assertTagModel(
            self.model,
            {
                "Animal": 0,
                "Animal/Insect": 0,
                "Animal/Insect/Bee": 1,
                "Animal/Mammal": 1,
                "Animal/Mammal/Cat": 1,
                "Animal/Mammal/Dog": 1,
                "Pet": 0,
                "Pet/Mammal": 0,
                "Pet/Mammal/Cat": 1,
                "Pet/Bird": 0,
                "Pet/Bird/Robin": 1,
                "Food": 0,
                "Food/Mammal": 0,
                "Food/Mammal/Cat": 1,
                "Food/Mammal/Pig": 1,
            },
        )
        self.assertInstanceEqual(t1, name="mammal1", tags="Animal/Mammal")

    def test_merge_form_l2_with_children_submit(self):
        self.populate()
        tag_names = ["Animal/Mammal", "Pet/Mammal", "Food/Mammal"]
        self.do_form_submit(
            tags=self.model.objects.filter(name__in=tag_names),
            merge_to=self.model.objects.get(name="Animal/Mammal"),
            params=["merge_children=on"],
        )

        self.assertTagModel(
            self.model,
            {
                "Animal": 0,
                "Animal/Insect": 0,
                "Animal/Insect/Bee": 1,
                "Animal/Mammal": 0,
                "Animal/Mammal/Cat": 3,
                "Animal/Mammal/Dog": 1,
                "Animal/Mammal/Pig": 1,
                "Pet": 0,
                "Pet/Bird": 0,
                "Pet/Bird/Robin": 1,
            },
        )


# ##############################################################################
# ###### Tagged inlines on tag ModelAdmin
# ##############################################################################


class TaggedInlineSingleAdminTest(AdminTestManager, TagTestManager, TestCase):
    """
    Test inlines of tagged models on tag modeladmins
    """

    admin_cls = test_admin.SimpleMixedTestSingletagAdmin
    tagged_model = test_models.SimpleMixedTest
    model = test_models.SimpleMixedTest.singletag.tag_model

    def setUpExtra(self):
        self.site = admin.AdminSite(name="tagulous_admin")
        tag_admin.register(self.model, admin_class=self.admin_cls, site=self.site)
        self.ma = self.site._registry[self.model]
        self.cl = None

        # Set up client
        User.objects.create_superuser("test", "test@example.com", "user")
        result = self.client.login(username="test", password="user")
        self.assertEqual(result, True)

    def tearDownExtra(self):
        test_urls.urlpatterns = self.old_urls
        self.client.logout()

    def get_url(self, name, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        return reverse(
            "admin:%s_%s_%s" % (content_type.app_label, content_type.model, name),
            args=args,
            kwargs=kwargs,
        )

    #
    # Tests
    #

    def test_add_renders(self):
        "Check inline add renders without error"
        response = self.client.get(self.get_url("add"))

        # Check the section is there
        h2_extra = ""
        if django.VERSION >= (5, 1):
            h2_extra = ' id="simplemixedtest_set-heading" class="inline-heading"'
        self.assertContains(
            response, f"<h2{h2_extra}>Simple mixed tests</h2>", html=True
        )

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
            "simplemixedtest_set-TOTAL_FORMS": 3,
            "simplemixedtest_set-INITIAL_FORMS": 0,
            "simplemixedtest_set-MAX_NUM_FORMS": 1000,
            "_save": "Save",
            "name": "Mr",
            "slug": "mr",
            "simplemixedtest_set-0-name": "Test 1",
            "simplemixedtest_set-0-tags": "tag1, tag2",
        }
        response = self.client.post(self.get_url("add"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tagged_model.objects.count(), 1)

        t1 = self.tagged_model.objects.get(name="Test 1")
        self.assertInstanceEqual(
            t1, name="Test 1", singletag="Mr", tags=["tag1", "tag2"]
        )
        self.assertTagModel(self.model, {"Mr": 1})
        self.assertTagModel(self.tagged_model.tags.tag_model, {"tag1": 1, "tag2": 1})

    def test_edit_renders(self):
        "Check inline edit renders without error"
        obj1 = self.tagged_model.objects.create(
            name="Test 1", singletag="Mr", tags=["tag1", "tag2"]
        )

        response = self.client.get(self.get_url("change", obj1.singletag.pk))

        # Check the section is there
        h2_extra = ""
        if django.VERSION >= (5, 1):
            h2_extra = ' id="simplemixedtest_set-heading" class="inline-heading"'
        self.assertContains(
            response, f"<h2{h2_extra}>Simple mixed tests</h2>", html=True
        )

        self.assertContains(response, 'id="id_simplemixedtest_set-TOTAL_FORMS')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-singletag"')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-name"')
        self.assertContains(response, 'id="id_simplemixedtest_set-0-tags"')
        # There should be 1 full field and 3 empty fields, zero-indexed
        self.assertContains(response, 'id="id_simplemixedtest_set-3-singletag"')
        self.assertNotContains(response, 'id="id_simplemixedtest_set-4-singletag"')

        # Check the fk is an id, to confirm it's using TaggedInlineFormSet
        html = response.content.decode("utf-8")
        i_name = html.index('name="simplemixedtest_set-0-singletag"')
        i_open = html.rindex("<", 0, i_name)
        i_close = html.index(">", i_name)
        self.assertHTMLEqual(
            html[i_open : i_close + 1],
            (
                '<input type="hidden" name="simplemixedtest_set-0-singletag" '
                'value="%d" id="id_simplemixedtest_set-0-singletag" />'
            )
            % obj1.singletag.pk,
        )

    def test_edit_saves(self):
        """
        Check inline edit saves without error

        Also check changing tag fields in inlines
        """
        # Create and confirm
        obj1 = self.tagged_model.objects.create(
            name="Test 1", singletag="Mr", tags=["tag1", "tag2"]
        )
        obj2 = self.tagged_model.objects.create(
            name="Test 2", singletag="Mr", tags=["tag3", "tag4"]
        )
        tag1 = obj1.singletag
        self.assertEqual(self.tagged_model.objects.count(), 2)
        self.assertTagModel(self.model, {"Mr": 2})
        self.assertTagModel(
            self.tagged_model.tags.tag_model,
            {"tag1": 1, "tag2": 1, "tag3": 1, "tag4": 1},
        )

        data = {
            "simplemixedtest_set-TOTAL_FORMS": 5,
            "simplemixedtest_set-INITIAL_FORMS": 2,
            "simplemixedtest_set-MAX_NUM_FORMS": 1000,
            "_save": "Save",
            "name": "Mr",
            "slug": "mr",
            "simplemixedtest_set-0-name": "Test 1e",
            "simplemixedtest_set-0-tags": "tag1, tag2e",
            "simplemixedtest_set-0-id": "%d" % obj1.pk,
            "simplemixedtest_set-0-singletag": "%d" % tag1.pk,
            "simplemixedtest_set-0-DELETE": "",
            "simplemixedtest_set-1-name": "Test 2e",
            "simplemixedtest_set-1-tags": "tag3, tag4e",
            "simplemixedtest_set-1-id": "%d" % obj2.pk,
            "simplemixedtest_set-1-singletag": "%d" % tag1.pk,
            "simplemixedtest_set-1-DELETE": "",
        }
        response = self.client.post(self.get_url("change", tag1.pk), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tagged_model.objects.count(), 2)

        self.assertInstanceEqual(
            obj1, name="Test 1e", singletag="Mr", tags=["tag1", "tag2e"]
        )
        self.assertInstanceEqual(
            obj2, name="Test 2e", singletag="Mr", tags=["tag3", "tag4e"]
        )

        self.assertTagModel(self.model, {"Mr": 2})
        self.assertTagModel(
            self.tagged_model.tags.tag_model,
            {"tag1": 1, "tag2e": 1, "tag3": 1, "tag4e": 1},
        )
