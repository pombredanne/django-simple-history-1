# -*- coding: utf-8 -*-
"""manager.py: Simple History Manager"""

from __future__ import unicode_literals
from django.db import models

__author__ = 'Marty Alchin'
__date__ = '2011/08/29 20:43:34'
__credits__ = ['Marty Alchin', 'Corey Bertram', 'Steven Klass']


class HistoryDescriptor(object):
    def __init__(self, model):
        self.model = model

    def __get__(self, instance, owner):
        if instance is None:
            return HistoryManager(self.model)
        return HistoryManager(self.model, instance)


class HistoryManager(models.Manager):
    def __init__(self, model, instance=None):
        super(HistoryManager, self).__init__()
        self.model = model
        self.instance = instance

    def get_queryset(self):
        if self.instance is None:
            return super(HistoryManager, self).get_query_set()

        if isinstance(self.instance._meta.pk, models.OneToOneField) and not (
            self.instance._meta.pk.name).endswith("_ptr"):
            filter = {self.instance._meta.pk.name + "_id": self.instance.pk}
        else:
            filter = {self.instance._meta.pk.name: self.instance.pk}
        return super(HistoryManager, self).get_query_set().filter(**filter)


    def latest(self, *args, **kwargs):
        if not self.instance:
            raise TypeError("Can't use most_recent() without a %s instance." %\
                            self.instance._meta.object_name)

        if isinstance(self.instance._meta.pk, models.OneToOneField) and not (
            self.instance._meta.pk.name).endswith("_ptr"):
            filter = {self.instance._meta.pk.name + "_id": self.instance.pk}
        else:
            filter = {self.instance._meta.pk.name: self.instance.pk}

        filter.update(**kwargs)

        items = super(HistoryManager, self).get_query_set().filter(**filter).order_by("-history_id")
        try:
            return items[0]
        except IndexError:
            raise self.instance.DoesNotExist(
                "%s has no historical record." % self.instance._meta.object_name)

    def most_recent(self):
        """
        Returns the most recent copy of the instance available in the history.
        """
        if not self.instance:
            raise TypeError("Can't use most_recent() without a %s instance." %\
                            self.instance._meta.object_name)

        latest = self.latest()
        if latest.history_type == '-':
            raise self.instance.DoesNotExist("%s had already been deleted." %\
                                             self.instance._meta.object_name)

        kwargs = {}
        for field in self.instance._meta.fields:
            field_name = field.name
            if isinstance(field, models.ForeignKey):
                field_name = field.name + "_id"

            kwargs[field_name] = getattr(latest, field.name)

        return self.instance.__class__(**kwargs)

    def as_of(self, date):
        """
        Returns an instance of the original model with all the attributes set
        according to what was present on the object on the date provided.
        """
        if not self.instance:
            raise TypeError("Can't use as_of() without a %s instance." %\
                            self.instance._meta.object_name)

        latest = self.latest(history_date__lte=date)
        if latest.history_type == '-':
            raise self.instance.DoesNotExist("%s had already been deleted." %\
                                             self.instance._meta.object_name)

        kwargs = {}
        for field in self.instance._meta.fields:
            field_name = field.name
            if isinstance(field, models.ForeignKey):
                field_name = field.name + "_id"

            kwargs[field_name] = getattr(latest, field.name)

        return self.instance.__class__(**kwargs)

    def log(self):
        "Dumps a log for an instance"
        if not self.instance:
            raise TypeError("Can't use as_of() without a %s instance." %\
                            self.instance._meta.object_name)

        if isinstance(self.instance._meta.pk, models.OneToOneField) and not (
            self.instance._meta.pk.name).endswith("_ptr"):
            filter = {self.instance._meta.pk.name + "_id": self.instance.pk}
        else:
            filter = {self.instance._meta.pk.name: self.instance.pk}

        results = []
        # initialize variables for the loop below
        _created, _created_by = None, None

        fields = self.instance._meta.fields
        items = super(HistoryManager, self).get_query_set().filter(**filter).order_by("history_id")

        for index, item in enumerate(items):
            if index == 0:
                _created = item.history_date
                _created_by = item.history_user
                continue
            previous_item = items[index - 1]
            changed = {'changes': {}}
            for field in fields:
                prev_value = getattr(previous_item, field.name)
                if prev_value in ['', None]:
                    prev_value = ''
                curr_value = getattr(item, field.name)
                if curr_value in ['', None]:
                    curr_value = ''
                if prev_value != curr_value:
                    changed['changes'][field.name] = (
                        getattr(previous_item, field.name), getattr(item, field.name))
            if len(changed['changes'].keys()):
                changed['via_admin'] = False
                changed['changed'] = item.history_date
                changed['changed_by'] = item.history_user
                if not item.history_user:
                    changed['via_admin'] = True
                changed['change_type'] = item.history_type
                results.append(changed)
        results.reverse()
        via_admin = False
        if not _created_by:
            via_admin = True
        return {'items': results, 'created': _created, 'created_by': _created_by,
                'via_admin': via_admin}
