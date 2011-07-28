from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.core.urlresolvers import reverse
from django import forms

from couchdbkit.ext.django.paginator import Paginator

class BaseAdmin(object):
    #class based views
    create = None
    update = None
    delete = None
    index = None
    history = None
    
    raw_id_fields = ()
    fields = None
    exclude = None
    fieldsets = None
    form = forms.ModelForm
    filter_vertical = ()
    filter_horizontal = ()
    radio_fields = {}
    prepopulated_fields = {}
    formfield_overrides = {}
    readonly_fields = ()
    ordering = None
    
    
    list_display = ('__unicode__',)
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_editable = ()
    search_fields = ()
    date_hierarchy = None
    save_as = False
    save_on_top = False
    paginator = Paginator
    inlines = []

    # Custom templates (designed to be over-ridden in subclasses)
    add_form_template = None
    change_form_template = None
    change_list_template = None
    delete_confirmation_template = None
    delete_selected_confirmation_template = None
    object_history_template = None

    # Actions
    actions = []
    #action_form = helpers.ActionForm
    actions_on_top = True
    actions_on_bottom = False
    actions_selection_counter = True
    
    def __init__(self, model, admin_site):
        self.model = model
        self.admin_site = admin_site
        self.declared_fieldsets = None
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = {'admin':self, 'admin_site':self.admin_site}
        
        # Admin-site-wide views.
        urlpatterns = patterns('',
            url(r'^$',
                wrap(self.index.as_view(**init)),
                name='index'),
            url(r'^add/$',
                wrap(self.create.as_view(**init)),
                name='add'),
            url(r'^(?P<pk>.+)/history/$',
                wrap(self.history.as_view(**init)),
                name='history'),
            url(r'^(?P<pk>.+)/delete/$',
                wrap(self.delete.as_view(**init)),
                name='delete'),
            url(r'^(?P<pk>.+)/$',
                wrap(self.update.as_view(**init)),
                name='change'),
        )
        return urlpatterns
    
    def urls(self):
        return self.get_urls()
    urls = property(urls)
    
    def _media(self):
        from django.conf import settings
        from django import forms

        js = ['js/core.js', 'js/admin/RelatedObjectLookups.js',
              'js/jquery.min.js', 'js/jquery.init.js']
        if self.actions is not None:
            js.extend(['js/actions.min.js'])
        if self.prepopulated_fields:
            js.append('js/urlify.js')
            js.append('js/prepopulate.min.js')
        #if self.opts.get_ordered_objects():
        #    js.extend(['js/getElementsBySelector.js', 'js/dom-drag.js' , 'js/admin/ordering.js'])

        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js])
    media = property(_media)
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def as_view(self, view, cacheable=False):
        return self.admin_site.admin_view(view, cacheable)
    
    def log_addition(self, request, object):
        """
        Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry, ADDITION
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            #content_type_id = ContentType.objects.get_for_model(object).pk,
            content_type_id = None,
            object_id       = object.get_id,
            object_repr     = force_unicode(object),
            action_flag     = ADDITION
        )
    
    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry, CHANGE
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            #content_type_id = ContentType.objects.get_for_model(object).pk,
            content_type_id = None,
            object_id       = object.get_id,
            object_repr     = force_unicode(object),
            action_flag     = CHANGE,
            change_message  = message
        )
    
    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method is called
        before the deletion.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry, DELETION
        LogEntry.objects.log_action(
            user_id         = request.user.id,
            #content_type_id = ContentType.objects.get_for_model(self.model).pk,
            content_type_id = None,
            object_id       = object.get_id,
            object_repr     = object_repr,
            action_flag     = DELETION
        )
    
    def get_model_perms(self, request):
        return {
            'add': self.has_add_permission(request),
            'change': self.has_change_permission(request),
            'delete': self.has_delete_permission(request),
        }
    
    def get_changelist(self, request):
        from changelist import ChangeList
        return ChangeList
    
    def queryset(self, request):
        return lambda **kwargs: self.model.view('_all_docs', **kwargs)
    
    def get_paginator(self, request, query_set, paginate_by):
        return self.paginator(query_set, paginate_by)
    
    def get_fieldsets(self, request, obj=None):
        "Hook for specifying fieldsets for the add form."
        if self.declared_fieldsets:
            return self.declared_fieldsets
        #form = self.get_form(request, obj)
        #fields = form.base_fields.keys() + list(self.get_readonly_fields(request, obj))
        return [(None, {'fields': self.model._properties.keys()})]
    
    def get_readonly_fields(self, request):
        return []
    
    def reverse(self, name, *args, **kwargs):
        return ''

import views

class DocumentAdmin(BaseAdmin):
    create = views.CreateView
    update = views.UpdateView
    delete = views.DeleteView
    index = views.IndexView
    history = views.HistoryView

