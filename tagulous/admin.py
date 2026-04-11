import warnings

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.checks import ModelAdminChecks
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from . import forms as tag_forms
from . import models as tag_models

# ##############################################################################
# ########################################################## Admin classes
# ##############################################################################


class TaggedModelAdminChecks(ModelAdminChecks):
    """
    ModelAdminChecks subclass that suppresses admin.E109 for TagFields.

    Set as ``checks_class`` on ``TaggedBaseModelAdminMixin`` so that any
    admin class which includes the mixin (either explicitly or via
    auto-enhancement) does not get E109 errors for TagField names in
    ``list_display``.
    """

    def _check_list_display_item(self, obj, item, label):
        if not callable(item) and not hasattr(obj, item):
            try:
                field = obj.model._meta.get_field(item)
                if isinstance(field, tag_models.TagField):
                    return []  # skip E109 for TagFields
            except Exception:
                pass
        return super()._check_list_display_item(obj, item, label)


class TaggedBaseModelAdminMixin:
    """
    Mixin providing tagulous support for ModelAdmin subclasses.

    Can be used explicitly in a custom ModelAdmin. When TAGULOUS_ENHANCE_MODELS
    is True (the default), it is also automatically injected into
    ModelAdmin.__bases__ so that standard admin registration works without any
    tagulous-specific imports.
    """

    checks_class = TaggedModelAdminChecks

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Remove the RelatedFieldWidgetWrapper from tag fields, so they don't
        display popup buttons
        """
        formfield = super(TaggedBaseModelAdminMixin, self).formfield_for_dbfield(
            db_field, request=kwargs.pop("request", None), **kwargs
        )

        if (
            isinstance(db_field, (tag_models.SingleTagField, tag_models.TagField))
            and isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper)
            and isinstance(formfield.widget.widget, tag_forms.AdminTagWidget)
        ):
            formfield.widget = formfield.widget.widget
        return formfield

    def get_autocomplete_fields(self, request):
        """
        Ensure TagFields aren't listed in Django's autocomplete_fields - they don't
        play well with Django's autocomplete, and will use their own
        """
        autocomplete_fields = super().get_autocomplete_fields(request)
        safe_fields = [
            field
            for field in autocomplete_fields
            if not isinstance(
                self.opts.get_field(field),
                (tag_models.SingleTagField, tag_models.TagField),
            )
        ]
        return tuple(safe_fields)

    def get_list_display(self, request):
        """
        Replace TagField names in list_display with display callables, so that
        the changelist renders tag strings rather than rejecting M2M fields.
        """
        list_display = list(super().get_list_display(request))
        for i, item in enumerate(list_display):
            if not callable(item) and not hasattr(self.__class__, item):
                try:
                    field = self.model._meta.get_field(item)
                    if isinstance(field, tag_models.TagField):
                        display_name = "_tagulous_display_%s" % item
                        if not hasattr(self.__class__, display_name):
                            setattr(self.__class__, display_name, _create_display(item))
                        list_display[i] = display_name
                except Exception:
                    pass
        return list_display


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   ModelAdmin for Tagged models
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TaggedModelAdmin(TaggedBaseModelAdminMixin, admin.ModelAdmin):
    pass


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   ModelAdmin for TagModel models
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagModelAdmin(admin.ModelAdmin):
    list_display = ["name", "count", "protected"]
    list_filter = ["protected"]
    search_fields = ["name"]
    exclude = ["count"]
    actions = ["merge_tags"]
    prepopulated_fields = {"slug": ("name",)}

    def merge_tags(self, request, queryset):
        """
        Admin action to merge tags
        """
        # Thanks to:
        #   http://www.hoboes.com/Mimsy/hacks/django-actions-their-own-intermediate-page/

        # Create a form
        is_tree = issubclass(self.model, tag_models.TagTreeModel)

        class MergeForm(forms.Form):
            # Keep selected items in same field, admin.helpers.ACTION_CHECKBOX_NAME
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            # Allow use to select from selected items
            merge_to = forms.ModelChoiceField(queryset)

        if is_tree:

            class MergeForm(MergeForm):
                # Allow to merge recursively
                merge_children = forms.BooleanField(required=False)

        if "merge" in request.POST:
            merge_form = MergeForm(request.POST)
            if merge_form.is_valid():
                # Merge - with children if set
                merge_to = merge_form.cleaned_data["merge_to"]
                kwargs = {}
                if is_tree and merge_form.cleaned_data["merge_children"]:
                    kwargs["children"] = True
                merge_to.merge_tags(queryset, **kwargs)

                self.message_user(request, "Tags merged", messages.SUCCESS)
                return HttpResponseRedirect(request.get_full_path())

        else:
            tag_pks = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
            if len(tag_pks) < 2:
                self.message_user(
                    request,
                    "You must select at least two tags to merge",
                    messages.ERROR,
                )
                return HttpResponseRedirect(request.get_full_path())

            merge_form = MergeForm(
                initial={
                    admin.helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(
                        admin.helpers.ACTION_CHECKBOX_NAME
                    ),
                    "merge_children": True,
                }
            )

        return render(
            request,
            "tagulous/admin/merge_tags.html",
            {
                "title": "Merge tags",
                "opts": self.model._meta,
                "merge_form": merge_form,
                "tags": queryset,
            },
        )

    merge_tags.short_description = "Merge selected tags..."


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   ModelAdmin for TagTreeModel models
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagTreeModelAdmin(TagModelAdmin):
    exclude = ["count", "parent", "path", "label", "level"]


# ##############################################################################
# ########################################################## Admin registration
# ##############################################################################

# Give contrib.admin a default widget for tag fields
admin.options.FORMFIELD_FOR_DBFIELD_DEFAULTS.update(
    {
        tag_models.SingleTagField: {"widget": tag_forms.AdminTagWidget},
        tag_models.TagField: {"widget": tag_forms.AdminTagWidget},
    }
)


def _create_display(field):
    """
    ModelAdmin display function factory
    """

    def display(self, obj):
        return getattr(obj, field).get_tag_string()

    display.short_description = field.replace("_", " ")
    return display


def list_display_tag_links(field_name):
    """
    Factory for a list_display function that renders tag fields as admin links.

    Each tag links to its admin change view if the tag model is registered with
    the default admin site; otherwise tags are shown as plain text. Works for
    both SingleTagField and TagField.

    Usage::

        class MyAdmin(tagulous.admin.TaggedModelAdmin):
            list_display = ['name', 'tags_links']
            tags_links = tagulous.admin.list_display_tag_links('tags')

        tagulous.admin.register(MyModel, MyAdmin)
    """

    def display(self, obj):
        field = obj.__class__._meta.get_field(field_name)
        tag_model = field.tag_model
        tag_value = getattr(obj, field_name)

        if not admin.site.is_registered(tag_model):
            if isinstance(field, tag_models.SingleTagField):
                return str(tag_value) if tag_value is not None else ""
            return tag_value.get_tag_string()

        if isinstance(field, tag_models.SingleTagField):
            tags = [tag_value]
        else:
            tags = tag_value.all()

        links = []
        for tag in tags:
            url = reverse(
                "admin:%s_%s_change"
                % (tag_model._meta.app_label, tag_model._meta.model_name),
                args=[tag.pk],
            )
            links.append(format_html('<a href="{}">{}</a>', url, tag.name))
        return mark_safe(", ".join(links))

    display.short_description = field_name.replace("_", " ")
    return display


def enhance():
    """
    Apply tagulous enhancements to Django's admin framework globally.

    Called automatically by the tagulous ``AppConfig.ready()`` when
    ``TAGULOUS_ENHANCE_MODELS`` is ``True`` (the default).

    Patches ``AdminSite.register`` so that any model registered with the
    standard Django admin automatically gets:

    * ``TaggedBaseModelAdminMixin`` injected into the admin class, providing
      correct widget rendering, autocomplete filtering, and ``list_display``
      handling for tag fields. This also sets ``checks_class`` to
      ``TaggedModelAdminChecks``, suppressing ``admin.E109`` for tag fields.
    * ``TagModelAdmin`` or ``TagTreeModelAdmin`` injected for tag models
      (subclasses of ``BaseTagModel``), providing the merge action, sensible
      ``list_display``, and other tag-model-specific admin features.
    * Inline formset classes on tag model admins upgraded to
      ``TaggedInlineFormSet`` where needed.
    """
    from django.contrib.admin import AdminSite

    # Patch AdminSite.register to inject tagulous support into each registered
    # admin class at the point of registration.
    if getattr(AdminSite.register, "_tagulous_enhanced", False):
        return

    original_register = AdminSite.register

    def tagulous_register(site, model_or_iterable, admin_class=None, **options):
        model = model_or_iterable if isinstance(model_or_iterable, ModelBase) else None

        if model is not None and issubclass(model, tag_models.BaseTagModel):
            # Supply or inject the appropriate tag model admin class so that
            # tag models always get the merge action, sensible list_display,
            # count exclusion, etc.
            if admin_class is None:
                admin_class = (
                    TagTreeModelAdmin
                    if issubclass(model, tag_models.TagTreeModel)
                    else TagModelAdmin
                )
            else:
                if issubclass(model, tag_models.TagTreeModel):
                    if not issubclass(admin_class, TagTreeModelAdmin):
                        admin_class.__bases__ = (
                            TagTreeModelAdmin,
                        ) + admin_class.__bases__
                elif not issubclass(admin_class, TagModelAdmin):
                    admin_class.__bases__ = (TagModelAdmin,) + admin_class.__bases__

        if admin_class is not None:
            # Inject TaggedBaseModelAdminMixin before the existing bases so its
            # methods (get_list_display, formfield_for_dbfield, etc.) take
            # priority over ModelAdmin's own implementations in the MRO.
            if TaggedBaseModelAdminMixin not in admin_class.__mro__:
                admin_class.__bases__ = (
                    TaggedBaseModelAdminMixin,
                ) + admin_class.__bases__

            # For tag model admins with inlines for tagged models, upgrade the
            # inline formset to TaggedInlineFormSet so tags are saved correctly.
            if (
                model is not None
                and issubclass(model, tag_models.BaseTagModel)
                and hasattr(admin_class, "inlines")
            ):
                for inline_cls in admin_class.inlines:
                    if not issubclass(inline_cls, TaggedBaseModelAdminMixin):
                        inline_cls.__bases__ = (
                            TaggedBaseModelAdminMixin,
                        ) + inline_cls.__bases__
                    if issubclass(
                        inline_cls.model, tag_models.TaggedModel
                    ) and not issubclass(
                        inline_cls.formset, tag_forms.TaggedInlineFormSet
                    ):
                        orig_cls = inline_cls.formset
                        inline_cls.formset = type(
                            str("Tagged%s" % orig_cls.__name__),
                            (tag_forms.TaggedInlineFormSet, orig_cls),
                            {},
                        )

        return original_register(site, model_or_iterable, admin_class, **options)

    tagulous_register._tagulous_enhanced = True
    AdminSite.register = tagulous_register


def register(model, admin_class=None, site=None, **options):
    """
    Register a model with the admin site with tagulous support.

    .. deprecated::
        Use ``django.contrib.admin.site.register()`` directly. When
        ``TAGULOUS_ENHANCE_MODELS`` is ``True`` (the default), tagulous admin
        enhancements are applied automatically via :func:`enhance`.

    Arguments:
        model       Model or tag descriptor to register
        admin_class Admin class for model (optional)
        site        Admin site to register with (default: ``django.contrib.admin.site``)
        **options   Passed to the admin site
    """
    warnings.warn(
        "tagulous.admin.register() is deprecated, use django.contrib.admin.site.register() "
        "directly - see Upgrading documentation for details",
        DeprecationWarning,
        stacklevel=2,
    )

    if isinstance(model, tag_models.BaseTagDescriptor):
        model = model.tag_model
    elif not isinstance(model, ModelBase):
        raise ImproperlyConfigured(
            "Tagulous can only register a single model with admin."
        )

    if site is None:
        site = admin.site

    if admin_class is not None:
        site.register(model, admin_class, **options)
    else:
        site.register(model, **options)
