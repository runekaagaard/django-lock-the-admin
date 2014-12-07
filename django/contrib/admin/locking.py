from __future__ import unicode_literals

from django.contrib.admin.utils import quote
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db import transaction, connection
from django.db.models.expressions import F
from django import forms
from django.template.defaultfilters import capfirst
from django.template.loader import render_to_string
from django.contrib.admin.exceptions import StaleObjectError
from django.utils.html import format_html

LOCK_VERSION_FIELD_NAME = 'lock_version'


def _get_or_create_lock(obj):
    from django.contrib.admin.models import Lock
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(obj)
    lock, _ = Lock.objects.get_or_create(content_type=content_type,
                                         object_id=obj.pk)

    return lock


def _increment_version(obj):
    from django.contrib.admin.models import Lock
    lock = _get_or_create_lock(obj)
    Lock.objects.filter(pk=lock.pk).update(version=F('version') + 1)


def _check_version(obj, version):
    lock = _get_or_create_lock(obj)
    version = int(version)
    if lock.version != version:
        raise StaleObjectError('{} is {} versions old.'.format(obj,
            lock.version - version))


def _exists_in_db(obj):
    # Using the "_state.adding" property is necessary because the "pk" property
    # of models with a "CharField" primary key gets populated before save.
    return obj is not None and obj.pk is not None and not obj._state.adding


def read_lock_version(_dict):
    try:
        return int(_dict[LOCK_VERSION_FIELD_NAME])
    except KeyError:
            raise Exception('Locking data is missing or has been tampered '
                            'with.')


def get_version(obj):
    if not _exists_in_db(obj):
        return None

    return _get_or_create_lock(obj).version


def save(func, obj, lock_version):
    if not _exists_in_db(obj):
        return func()

    # When using a database without transaction support, check the
    # version number before saving. In the context of the admin this
    # works most of the time, but TOCTTOU race conditions may occur.
    if not connection.features.supports_transactions:
        _check_version(obj, lock_version)
    result = func()
    if connection.features.supports_transactions:
        _check_version(obj, lock_version)
    _increment_version(obj)

    return result

def extend_formset(formset):
    class LockableFormset(formset):
        def add_fields(self, form, index):
            super(LockableFormset, self).add_fields(form, index)
            if _exists_in_db(form.instance):
                form.fields[LOCK_VERSION_FIELD_NAME] = forms.IntegerField(
                    initial=get_version(form.instance),
                    widget=forms.HiddenInput())

    return LockableFormset


def extend_formset_form(form):
    class LockableFormsetForm(form):
        def clean(self):
            if _exists_in_db(self.instance):
                read_lock_version(self.cleaned_data)
            super(LockableFormsetForm, self).clean()

        def save(self, commit=True):
            func = lambda: super(LockableFormsetForm, self).save(commit)
            if not _exists_in_db(self.instance):
                return func()
            else:
                return save(func, self.instance, read_lock_version(
                    self.cleaned_data))

    return LockableFormsetForm


def error_message(obj, lock_version, formsets, admin_site):
    def admin_link(model):
        name = capfirst(model._meta.verbose_name)
        try:
            path = '{}:{}_{}_change'.format(admin_site.name,
                model._meta.app_label, model._meta.model_name)
            admin_url = reverse(path, None, (quote(model._get_pk_val()), ))

            return format_html('{0}: <a href="{1}">{2}</a>', name, admin_url,
                               model)
        except NoReverseMatch:
            return format_html('{}: {}', name, model)

    errors = []
    try:
        _check_version(obj, lock_version)
    except StaleObjectError:
        errors.append(obj)

    for formset in formsets:
        for form in formset:
            instance = form.instance
            if not _exists_in_db(instance):
                continue
            try:
                _check_version(instance, read_lock_version(form.cleaned_data))
            except StaleObjectError:
                errors.append(form.instance)

    return render_to_string('admin/locking_error.html', {
        'errors': map(admin_link, errors),
        'num_errors': len(errors),
    })
