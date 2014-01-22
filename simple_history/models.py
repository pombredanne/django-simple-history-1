# -*- coding: utf-8 -*-
"""models.py: Simple History Models"""

from __future__ import unicode_literals

import copy
import datetime

from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.utils.timezone import now
from django.conf import settings

from .manager import HistoryDescriptor
from .registration import FieldRegistry

__author__ = 'Marty Alchin'
__date__ = '2011/08/29 20:43:34'
__credits__ = ['Marty Alchin', 'Corey Bertram', 'Steven Klass']


# This is used to store the user id - else just None.
class CurrentUserField(models.ForeignKey):
    """A field to store the user id else None"""
    def __init__(self, recursive_to_user=False, **kwargs):
        # If the base model is the actual User model, it must be referenced by "self", not the full
        # app label.
        if recursive_to_user:
            user_model = 'self'
        else:
            user_model = settings.AUTH_USER_MODEL
        if 'null' in kwargs:
            del kwargs['null']
        if 'to' in kwargs:
            del kwargs['to']
        super(CurrentUserField, self).__init__(user_model, null=True, **kwargs)

    def contribute_to_class(self, cls, name):
        """Contributor
        :param name:  Name given
        :param cls: Class Object
        """
        super(CurrentUserField, self).contribute_to_class(cls, name)
        registry = FieldRegistry()
        registry.add_field(cls, self)


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^simple_history\.models\.CurrentUserField"])
except ImportError:
    pass


class HistoricalRecords(object):
    """Historical Record holder"""
    def contribute_to_class(self, cls, name):
        """Contributor
        :param name:  Name given
        :param cls: Class Object
        """
        self.manager_name = name
        models.signals.class_prepared.connect(self.finalize, sender=cls)

    def finalize(self, sender, **kwargs):
        """Define and finalize the object
        :param kwargs: Not used
        :param sender: Object being sent
        """
        history_model = self.create_history_model(sender)

        # The HistoricalRecords object will be discarded,
        # so the signal handlers can't use weak references.
        models.signals.post_save.connect(self.post_save, sender=sender,
                                         weak=False)
        models.signals.post_delete.connect(self.post_delete, sender=sender,
                                           weak=False)

        descriptor = HistoryDescriptor(history_model)
        setattr(sender, self.manager_name, descriptor)

    def create_history_model(self, model):
        """
        Creates a historical model to associate with the model provided.
        :param model: Model Objecgt
        """
        attrs = self.copy_fields(model)
        attrs.update(self.get_extra_fields(model))
        attrs.update(Meta=type(str('Meta'), (), self.get_meta_options(model)))
        name = 'Historical%s' % model._meta.object_name
        return type(str(name), (models.Model,), attrs)

    def copy_fields(self, model):
        """
        Creates copies of the model's original fields, returning
        a dictionary mapping field name to copied field object.
        :param model: Model Object
        """
        # Though not strictly a field, this attribute
        # is required for a model to function properly.
        fields = {'__module__': model.__module__}

        for field in model._meta.fields:
            field = copy.copy(field)

            if isinstance(field, models.AutoField):
                # The historical model gets its own AutoField, so any
                # existing one must be replaced with an IntegerField.
                field.__class__ = models.IntegerField

            if isinstance(field, models.ForeignKey):
                field.__class__ = models.IntegerField
                #ughhhh. open to suggestions here
                try:
                    field.rel = None
                except:
                    pass
                try:
                    field.related = None
                except:
                    pass
                try:
                    field.related_query_name = None
                except:
                    pass
                field.null = True
                field.blank = True
                fk = True
            else:
                fk = False

            if field.primary_key or field.unique:
                # Unique fields can no longer be guaranteed unique,
                # but they should still be indexed for faster lookups.
                field.primary_key = False
                field._unique = False
                field.db_index = True
                field.serialize = True
            if fk:
                fields[field.name + "_id"] = field
            else:
                fields[field.name] = field

        return fields

    def get_extra_fields(self, model):
        """
        Returns a dictionary of fields that will be added to the historical
        record model, in addition to the ones returned by copy_fields below.
        :param model: Model Object
        """
        rel_nm = '_%s_history' % model._meta.object_name.lower()
        is_user = settings.AUTH_USER_MODEL == ('%s.%s' % (model._meta.app_label,
                                                          model._meta.object_name))
        return {
            'history_id': models.AutoField(primary_key=True),
            'history_date': models.DateTimeField(default=now),
            'history_user': CurrentUserField(related_name=rel_nm, recursive_to_user=is_user),
            'history_type': models.CharField(max_length=1, choices=(
                ('+', 'Created'),
                ('~', 'Changed'),
                ('-', 'Deleted'),
            )),
            'history_object': HistoricalObjectDescriptor(model),
            '__unicode__': lambda self: '%s as of %s' % (self.history_object,
                                                         self.history_date)
        }

    def get_meta_options(self, model):
        """
        Returns a dictionary of fields that will be added to
        the Meta inner class of the historical record model.
        :param model: Model Object
        """
        return {
            'ordering': ('-history_date',),
        }

    def post_save(self, instance, created, **kwargs):
        """Post Save Trigger
        :param kwargs: Only used for raw
        :param created: Whether it was created or not
        :param instance: Instance Object
        """
        if not kwargs.get('raw', False):
            self.create_historical_record(instance, created and '+' or '~')

    def post_delete(self, instance, **kwargs):
        """Post Delete Trigger
        :param kwargs: Not Used
        :param instance: Instance Object
        """
        self.create_historical_record(instance, '-')

    def create_historical_record(self, instance, type_obj):
        """Create the record
        :param type_obj: The Type Object
        :param instance: The Instance in Question
        """
        manager = getattr(instance, self.manager_name)
        attrs = {}
        for field in instance._meta.fields:
            attrs[field.name] = getattr(instance, field.attname)
        if type_obj == '~':
            try:
                manager.get_or_create(defaults=dict(history_type=type_obj), **attrs)
            except MultipleObjectsReturned:
                pass
        else:
            manager.create(history_type=type_obj, **attrs)



class HistoricalObjectDescriptor(object):
    """The descriptor"""
    def __init__(self, model):
        self.model = model

    def __get__(self, instance, owner):
        """Given an owner get the objects"""
        values = (getattr(instance, f.name) for f in self.model._meta.fields)
        return self.model(*values)
