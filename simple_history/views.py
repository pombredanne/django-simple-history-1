# -*- coding: utf-8 -*-
"""views.py: Django simple_history"""

from __future__ import unicode_literals

import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils import formats
from django.views.generic import ListView
try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
    get_user_model = lambda: User

from datatableview.views import DatatableView

__author__ = 'Steven Klass'
__date__ = '9/18/12 10:46 PM'
__copyright__ = 'Copyright 2012 Pivotal Energy Solutions. All rights reserved.'
__credits__ = ['Steven Klass', ]

log = logging.getLogger(__name__)

class HistoryDataTableView(DatatableView):
    template_name = "simple_history/history_list.html"
    datatable_options = {
        'columns': [
            ('Date', ['history_date'], 'get_column_Date_data'),
            ('User', ['history_user__username', 'history_user__first_name',
                      'history_user__last_name'],
             'get_column_User_data'),
            ('Object', ['history_object'], 'get_column_Object_data'),
            ('Type', ['history_type'], 'get_column_Type_data'),
            ('Fields', None, 'get_column_Fields_data'),
            ('Previous Values', None, 'get_column_Previous_data'),
            ('Updated Values', None, 'get_column_Updated_data'),
        ],
        'ordering': ['Add Remove Reject', 'name'],
    }

    def get_model_obj(self):
        """Return the generic model object"""
        if hasattr(self, 'model_obj'): return self.model_obj
        model_ct = ContentType.objects.get(
            app_label=self.kwargs.get('app_label'), model=self.kwargs.get('model'))
        self.model_obj = model_ct.model_class()
        return self.model_obj

    def get_object(self, id=None):
        """If we have a pk then we know the row"""
        if id is None and self.kwargs.get('field') == 'id':
            id = self.kwargs.get('constraint')
        self.object = self.get_model_obj().objects.get(pk=id)
        return self.object

    def get_queryset(self):
        """Narrow this based on your company"""
        filter = {self.kwargs.get('field'): self.kwargs.get('constraint')}
        try:
            filter['content_type'] = int(self.request.GET.get('content_type_id'))
        except:
            pass
        data = self.get_model_obj().history.filter(**filter).order_by("history_id")
        keep_ids, _discard = [], []
        for item in list(data.values()):
            retained = item.copy()
            keep_id = item.pop('history_id')
            [item.pop(k, None) for k in ['history_date', 'modified_date']]
            if len(_discard) and _discard[-1] == item:
                continue
            _discard.append(item)
            keep_ids.append(keep_id)
        update = self.get_model_obj().history.filter(history_id__in=keep_ids).order_by("history_id")
        if not hasattr(self, '_fields'):
            self._user_dict = {}
            self._object_dict = {}
            self._related_dict = {}
            self._get_fields_changed_current_deltas(update)
        return update

    def _get_fields_changed_current_deltas(self, queryset):
        """This will iterate over the changes and collect the deltas"""
        fields = self.get_model_obj()._meta.fields
        object_list = []
        olist = queryset.values()
        for item in olist:
            item.pop('history_date', 'modified_date')
            object_list.append(item)
        self._fields = {}
        for index in range(len(object_list)):
            _id = object_list[index]['history_id']
            self._fields[_id] = self._get_fields_changed_current_delta(index, object_list)

    def _get_fields_changed_current_delta(self, index, object_list):
        """Given an index number get the delta between the prior item"""
        fields = self.get_model_obj()._meta.fields
        item = object_list[index]

        previous_item = {}
        for old_item in reversed(object_list[:index]):
            if old_item.get('id') == item.get('id'):
                previous_item = old_item
                break

        changed_fields, prev_values, cur_values = [], [], []
        for field in fields:
            prev_value = previous_item.get(field.name, "-")
            prev_value = prev_value if prev_value else "-"
            curr_value = item.get(field.name, "-")
            curr_value = curr_value if curr_value else "-"

            # Handle nice choices keys
            if hasattr(field, '_choices') and len(field._choices) and curr_value != '-':
                try:
                    curr_value = next((x[1] for x in field._choices if str(x[0]) == str(curr_value)))
                except StopIteration:
                    pass
            # Handle foreign keys.
            elif hasattr(field, 'related') and curr_value != '-':
                try:
                    curr_value = self._related_dict[(field.name, curr_value)]
                    # log.debug("Related (current) Dict - Query Saved {} = {}".format(field.name, curr_value))
                except KeyError:
                    _v = '-'
                    try:
                        _v = field.related.parent_model.objects.get(id=curr_value).__unicode__()
                        if hasattr(self.request, 'user') and self.request.user.is_superuser:
                            _v = "[{}] {}".format(curr_value, _v)
                    except ObjectDoesNotExist:
                        _v = 'Deleted'
                    # log.debug("Setting C Related ({}, {}) = {}".format(field.name, curr_value,_v))
                    self._related_dict[(field.name, curr_value)] = _v
                    curr_value = self._related_dict[(field.name, curr_value)]

            if hasattr(field, '_choices') and len(field._choices) and prev_value != '-':
                try:
                    prev_value = next((x[1] for x in field._choices if str(x[0]) == str(prev_value)))
                except StopIteration:
                    pass

            elif hasattr(field, 'related') and prev_value != '-':
                try:
                    prev_value = self._related_dict[(field.name, prev_value)]
                    # log.debug("Related (prev) Dict - Query Saved {} = {}".format(field.name, prev_value))
                except KeyError:
                    _v = '-'
                    try:
                        _v = field.related.parent_model.objects.get(id=prev_value).__unicode__()
                        if hasattr(self.request, 'user') and self.request.user.is_superuser:
                            _v = "[{}] {}".format(prev_value, _v)
                    except ObjectDoesNotExist:
                        _v = 'Deleted'
                    # log.debug("Setting P Related ({}, {}) = {}".format(field.name, prev_value,_v))
                    self._related_dict[(field.name, prev_value)] = _v
                    prev_value = self._related_dict[(field.name, prev_value)]

            if field.__class__.__name__ == "DateTimeField":
                try:
                    curr_value = curr_value.strftime('%m/%d/%y %H:%M')
                except AttributeError:
                    pass
                try:
                    prev_value = prev_value.strftime('%m/%d/%y %H:%M')
                except AttributeError:
                    pass

            if field.__class__.__name__ == "DateField":
                try:
                    curr_value = curr_value.strftime('%m/%d/%y')
                except AttributeError:
                    pass
                try:
                    prev_value = prev_value.strftime('%m/%d/%y')
                except AttributeError:
                    pass

            if prev_value != curr_value:
                changed_fields.append(field.name)
                prev_values.append(prev_value)
                cur_values.append(curr_value)
        result = {'fields': [], 'previous': [], 'updated': []}
        if len(changed_fields):
            result = {'fields': [unicode(x) for x in changed_fields],
                      'previous': [unicode(x) for x in prev_values],
                      'updated': [unicode(x) for x in cur_values]}
        return result

    def get_column_Date_data(self, obj, *args, **kwargs):
        tz = self.request.user.timezone_preference
        dts = obj.history_date.astimezone(tz)
        return formats.date_format(dts, 'SHORT_DATETIME_FORMAT')

    def get_column_User_data(self, obj, *args, **kwargs):

        try:
            return self._user_dict[obj.history_user_id]
        except KeyError:
            link = ''
            try:
                name = obj.history_user.get_full_name()
                url = obj.history_user.get_absolute_url()
                link = "<a href='{}'>{}</a>".format(url, name)
            except (AttributeError, ObjectDoesNotExist):
                link = "Administrator*"
            self._user_dict[obj.history_user_id] = link
            return link

    def get_column_Object_data(self, obj, *args, **kwargs):
        try:
            return self._object_dict[obj.id]
        except KeyError:
            link, data_obj = '', ''
            try:
                data_obj = self.get_object(id=obj.id)
                name = data_obj.__unicode__()
                name = name if len(name) < 32 else name[0:32] + " ..."
                link = "<a href='{}'>{}</a>".format(data_obj.get_absolute_url(), name)
            except ObjectDoesNotExist:
                link = "Deleted"
            except AttributeError:
                link = data_obj.__unicode__()
            self._object_dict[obj.id] = link
            return link

    def get_column_Type_data(self, obj, *args, **kwargs):
        type_choices = (('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted'))
        return next((x[1] for x in type_choices if x[0] == obj.history_type), '-')

    def get_column_Fields_data(self, obj, *args, **kwargs):
        return "<br>".join(self._fields[obj.history_id]['fields'])

    def get_column_Previous_data(self, obj, *args, **kwargs):
        return "<br>".join(self._fields[obj.history_id]['previous'])

    def get_column_Updated_data(self, obj, *args, **kwargs):
        return "<br>".join(self._fields[obj.history_id]['updated'])


class HistoryListView(ListView):
    """History List View"""
    template_name = "simple_history/historical_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Ensure we have access"""
        return super(HistoryListView, self).dispatch(*args, **kwargs)

    def get_model_obj(self):
        """Return the generic model object"""
        if hasattr(self, 'model_obj'): return self.model_obj
        model_ct = ContentType.objects.get(
            app_label=self.kwargs.get('app_label'), model=self.kwargs.get('model'))
        self.model_obj = model_ct.model_class()
        return self.model_obj

    def get_object(self, id=None):
        """If we have a pk then we know the row"""
        if id is None and self.kwargs.get('field') == 'id':
            id = self.kwargs.get('constraint')
        self.object = self.get_model_obj().objects.get(pk=id)
        return self.object

    def get_queryset(self):
        """Narrow this based on your company"""
        filter = {self.kwargs.get('field'): self.kwargs.get('constraint')}
        return self.get_model_obj().history.filter(**filter).order_by("history_id")

    def get_context_data(self, **kwargs):
        context = super(HistoryListView, self).get_context_data(**kwargs)
        context['model'] = self.get_model_obj()
        context['object'] = self.get_object()
        context['app_label'] = self.kwargs.get('app_label')
        context['model'] = self.kwargs.get('model')
        context['field'] = self.kwargs.get('field')
        context['constraint'] = self.kwargs.get('constraint')
        return context

    def get_serialized_data(self):
        """Serialize the historical data.  Used in AJAX requests to load the table data."""
        results = []
        fields = self.get_model_obj()._meta.fields

        user_dict = {}
        object_dict = {}
        related_dict = {}

        object_list = self.get_queryset().distinct().values()

        href = '<a href="{}">{}</a>'
        type_choices = (('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted'))
        for index, item in enumerate(object_list):
            data = {"DT_RowId": item.get('history_id'), 0: '',
                    1: '', 2: '', 3: '-', 4: '-', 5: '-', 6: '-'}

            # 0 - Date
            # 1 - Who
            # 2 - Object (if not specific)
            # 3 - Action
            # 4 - Field
            # 5 - Previous
            # 6 - Current
            data[0] = item.get('history_date').strftime("%m/%d/%y %H:%M")

            try:
                data[1] = user_dict[item.get('history_user_id')]
            except KeyError:
                link = ''
                try:
                    user = get_user_model().objects.get(id=item.get('history_user_id'))
                    link = href.format(user.get_absolute_url(),user.get_full_name())
                except ObjectDoesNotExist:
                    link = "Administrator*"
                user_dict[item.get('history_user_id')] = link
                data[1] = user_dict[item.get('history_user_id')]

            try:
                data[2] = object_dict[item.get('id')]
            except KeyError:
                link, data_obj = '', ''
                try:
                    data_obj = self.get_object(id=item.get('id'))
                    name = data_obj.__unicode__()
                    name = name if len(name) < 32 else name[0:32] + " ..."
                    link = href.format(data_obj.get_absolute_url(), name)
                except ObjectDoesNotExist:
                    link = "Deleted"
                except AttributeError:
                    link = data_obj.__unicode__()
                object_dict[item.get('id')] = link
                data[2] = object_dict[item.get('id')]

            data[3] = next((y for x, y in type_choices if x == item.get('history_type')), "-")


            try:
                previous_item = object_list[index - 1]
            except AssertionError:
                previous_item = {}
            changed_fields, prev_values, cur_values = [], [], []
            for field in fields:
                if field.name == "modified_date":
                    continue
                prev_value = previous_item.get(field.name, "-")
                prev_value = prev_value if prev_value else "-"
                curr_value = item.get(field.name, "-")
                curr_value = curr_value if curr_value else "-"

                # Handle nice choices keys
                if hasattr(field, '_choices') and len(field._choices) and curr_value != '-':
                    curr_value = next((x[1] for x in field._choices if str(x[0]) == str(curr_value)))
                # Handle foreign keys.
                elif hasattr(field, 'related') and curr_value != '-':
                    try:
                        curr_value = related_dict[(field.name, curr_value)]
                        # log.debug("Related (current) Dict - Query Saved {} = {}".format(field.name, curr_value))
                    except KeyError:
                        _v = '-'
                        try:
                            _v = field.related.parent_model.objects.get(id=curr_value).__unicode__()
                        except ObjectDoesNotExist:
                            _v = 'Deleted'
                        # log.debug("Setting C Related ({}, {}) = {}".format(field.name, curr_value,_v))
                        related_dict[(field.name, curr_value)] = _v
                        curr_value = related_dict[(field.name, curr_value)]

                if hasattr(field, '_choices') and len(field._choices) and prev_value != '-':
                    prev_value = next((x[1] for x in field._choices if str(x[0]) == str(prev_value)))

                elif hasattr(field, 'related') and prev_value != '-':
                    try:
                        prev_value = related_dict[(field.name, prev_value)]
                        # log.debug("Related (prev) Dict - Query Saved {} = {}".format(field.name, prev_value))
                    except KeyError:
                        _v = '-'
                        try:
                            _v = field.related.parent_model.objects.get(id=prev_value).__unicode__()
                        except ObjectDoesNotExist:
                            _v = 'Deleted'
                        # log.debug("Setting P Related ({}, {}) = {}".format(field.name, prev_value,_v))
                        related_dict[(field.name, prev_value)] = _v
                        prev_value = related_dict[(field.name, prev_value)]

                if field.__class__.__name__ == "DateTimeField":
                    try:
                        curr_value = curr_value.strftime('%m/%d/%y %H:%M')
                    except AttributeError:
                        pass
                    try:
                        prev_value = prev_value.strftime('%m/%d/%y %H:%M')
                    except AttributeError:
                        pass

                if field.__class__.__name__ == "DateField":
                    try:
                        curr_value = curr_value.strftime('%m/%d/%y')
                    except AttributeError:
                        pass
                    try:
                        prev_value = prev_value.strftime('%m/%d/%y')
                    except AttributeError:
                        pass

                if prev_value != curr_value:
                    changed_fields.append(field.name)
                    prev_values.append(prev_value)
                    cur_values.append(curr_value)
            if len(changed_fields):
                data[4] = "<br />".join([unicode(x) for x in changed_fields])
                data[5] = "<br />".join([unicode(x) for x in prev_values])
                data[6] = "<br />".join([unicode(x) for x in cur_values])
                results.append(data)

        results.reverse()
        return results

    def get(self, context, **kwargs):
        if self.request.is_ajax():
            result = self.get_serialized_data()
            return HttpResponse(json.dumps({"aaData": result}), mimetype="application/json")
        return super(HistoryListView, self).get(context, **kwargs)
