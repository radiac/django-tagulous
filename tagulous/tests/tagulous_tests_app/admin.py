from django.contrib import admin

class SimpleMixedTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'singletag', 'tags')
    list_filter = ['singletag', 'tags']
    fields = ('name', 'singletag', 'tags')
    
    # No links for changelist
    # ++ TODO: Change to None when supported by all Django versions
    # Docs say this will work when set to None, but unclear which version of
    # django started supporting it. Certainly after 1.5.
    list_display_links = ['none']
