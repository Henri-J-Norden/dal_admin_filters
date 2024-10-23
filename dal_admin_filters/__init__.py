# -*- encoding: utf-8 -*-
from dal import autocomplete, forward
from django import forms
from django.contrib.admin.filters import ListFilter, SimpleListFilter, FieldListFilter, EmptyFieldListFilter
from django.db.models import Count
from django.forms.widgets import Media, MEDIA_TYPES, media_property
from django.contrib.admin.utils import get_fields_from_path


class AutocompleteFilterMixin(ListFilter):
    template = "dal_admin_filters/autocomplete-filter.html"
    title = ''
    field_name = ''
    field_pk = 'id'
    use_pk_exact = True
    autocomplete_url = ''
    is_placeholder_title = False
    widget_attrs = {}
    forwards = []
    parameter_name = None

    class Media:
        css = {
            'all': (
                'dal_admin_filters/css/autocomplete-fix.css',
            )
        }
        js = (
            'dal_admin_filters/js/forward-fix.js',
            'dal_admin_filters/js/querystring.js',
        )

    def __init__(self, *args, **kwargs):
        if self.parameter_name is None:
            self.parameter_name = self.field_name
            if self.use_pk_exact:
                self.parameter_name += '__{}__exact'.format(self.field_pk)
        super().__init__(*args, **kwargs)

    def _init_autocomplete(self, request, params, model, model_admin):
        widget = self.get_widget(request)

        self._add_media(model_admin, widget)

        field = forms.ModelChoiceField(
            queryset=self.get_queryset_for_field(model, self.field_name),
            widget=widget
        )

        attrs = self.widget_attrs.copy()
        attrs['id'] = 'id-%s-dal-filter' % self.field_name
        if self.is_placeholder_title:
            attrs['data-placeholder'] = self.title
        self.rendered_widget = field.widget.render(
            name=self.parameter_name,
            value=self.used_parameters.get(self.parameter_name, ''),
            attrs=attrs
        )

    def get_queryset_for_field(self, model, name):
        field = get_fields_from_path(model, name)[-1]
        return self.get_queryset_for_field_obj(field)

    def get_queryset_for_field_obj(self, field):
        if field.is_relation:
            return field.related_model.objects.all()
        return field.model.objects.all()

    def _add_media(self, model_admin, widget):

        if not hasattr(model_admin, 'Media'):
            model_admin.__class__.Media = type('Media', (object,), dict())
            model_admin.__class__.media = media_property(model_admin.__class__)

        def _get_media(obj):
            return Media(media=getattr(obj, 'Media', None))

        media = _get_media(model_admin) + widget.media + _get_media(AutocompleteFilter) + _get_media(self)

        for name in MEDIA_TYPES:
            setattr(model_admin.Media, name, getattr(media, "_" + name))

    def get_forwards(self):
        return tuple(
            forward.Field(field, field) if isinstance(field, str) else field
            for field in self.forwards
        ) or None

    def get_widget(self, request):
        widget = autocomplete.ModelSelect2(
            url=self.get_autocomplete_url(request),
            forward=self.get_forwards(),
        )
        return widget

    def get_autocomplete_url(self, request):
        return self.autocomplete_url


class AutocompleteFilter(AutocompleteFilterMixin, SimpleListFilter):
    def __init__(self, request, params, model, model_admin):
        super(AutocompleteFilter, self).__init__(request, params, model, model_admin)
        self._init_autocomplete(request, params, model, model_admin)

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        return ()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value()})
        else:
            return queryset


class AutocompleteFieldFilter(AutocompleteFilterMixin, FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_name = field_path
        super().__init__(field, request, params, model, model_admin, field_path)
        self._init_autocomplete(request, params, model, model_admin)

    def get_queryset_for_field(self, model, name):
        return self.get_queryset_for_field_obj(self.field)

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, changelist):
        return ()


class AutocompleteEmptyFieldFilter(AutocompleteFilterMixin, EmptyFieldListFilter):
    null_override: bool | None = None
    empty_strings_allowed_override: bool | None = None
    empty: bool = True
    count_distinct: bool = True

    def __init__(self, field, request, params, model, model_admin, field_path):
        prev_field_null = field.null
        if self.empty:
            if self.null_override is not None:
                field.null = self.null_override
            if self.empty_strings_allowed_override is not None:
                field.empty_strings_allowed = self.empty_strings_allowed_override
        else:
            field.null = True

        self.field_name = field_path
        super().__init__(field, request, params, model, model_admin, field_path)
        self._init_autocomplete(request, params, model, model_admin)

        if not self.empty:
            field.null = prev_field_null

    def value(self):
        val = self.used_parameters.get(self.parameter_name)
        if isinstance(val, list):
            assert len(val) == 1
            return val[0]
        return val

    def get_queryset_for_field(self, model, name):
        return self.get_queryset_for_field_obj(self.field)

    def expected_parameters(self):
        return [self.parameter_name, *super().expected_parameters()]

    def queryset(self, request, queryset):
        queryset = super().queryset(request, queryset)
        if self.value():
            queryset = queryset.filter(**{self.parameter_name: self.value()})
        return queryset

    def choices(self, changelist):
        if not self.empty:
            return ()

        prev_get_query_string = changelist.get_query_string

        def override_get_query_string(*args, **kwargs):
            remove = list(kwargs.get("remove", None) or []) + [self.parameter_name]
            kwargs["remove"] = remove
            return prev_get_query_string(*args, **kwargs)

        changelist.get_query_string = override_get_query_string
        yield from super().choices(changelist)
        changelist.get_query_string = prev_get_query_string

    def get_facet_counts(self, pk_attname, filtered_qs):
        counts_dict = super().get_facet_counts(pk_attname, filtered_qs)
        for v in counts_dict.values():
            v.distinct = self.count_distinct
        return counts_dict
