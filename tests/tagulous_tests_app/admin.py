from django.contrib import admin

from tests.tagulous_tests_app import models


class SimpleMixedTestAdmin(admin.ModelAdmin):
    """
    For testing tagged models
    For use with models.SimpleMixedTest
    """

    list_display = ("name", "singletag", "tags")
    list_filter = ["singletag", "tags"]
    fields = ("name", "singletag", "tags")
    list_display_links = [None]


class SimpleMixedTestInline(admin.TabularInline):
    """
    For testing tagged model inlines on tag model admin
    """

    model = models.SimpleMixedTest
    extra = 3


class SimpleMixedTestSingletagAdmin(admin.ModelAdmin):
    "For testing FK inlines"
    inlines = [SimpleMixedTestInline]


class SimpleMixedTestTagsAdmin(admin.ModelAdmin):
    """
    For testing attribute overrides on TagModels
    For use with models.SimpleMixedTest.tags.tag_model
    """

    list_display = ["name"]
    list_filter = ["count"]
    exclude = ["name"]
    actions = []
    inlines = [SimpleMixedTestInline]
