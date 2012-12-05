# -*- coding: utf-8 -*-"""views.py: Django simple_history"""
import json

import logging
from pprint import pformat
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import ListView

__author__ = 'Steven Klass'
__date__ = '9/18/12 10:46 PM'
__copyright__ = 'Copyright 2012 IC Manage. All rights reserved.'
__credits__ = ['Steven Klass', ]

log = logging.getLogger(__name__)

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
        """ Serialize the historical data.  Used in AJAX requests to load the table data. """

        results = []
        fields = self.get_model_obj()._meta.fields

        href = '<a href="{}">{}</a>'
        for index, item in enumerate(self.get_queryset()):
            # 0 - Date
            # 1 - Who
            # 2 - Object (if not specific)
            # 3 - Action
            # 4 - Field
            # 5 - Previous
            # 6 - Current

            data = {"DT_RowId": item.pk, 0: '', 1: '', 2: '', 3: '-', 4: '-', 5: '-', 6: '-'}
            data[0] = item.history_date.strftime("%m/%d/%y %H:%M")
            try:
                data[1] = href.format(item.history_user.profile.get_absolute_url(),
                                      item.history_user.get_full_name())
            except AttributeError: data[1] = "Administrator*"

            try:
                data_obj = self.get_object(id=item.id)
                data[2] = href.format(data_obj.get_absolute_url(), str(data_obj))
            except ObjectDoesNotExist:
                data[2] = "Deleted"
            except AttributeError:
                data[2] = str(data_obj)

            data[3] = item.get_history_type_display()
            if item.history_type == "+":
                results.append(data)
                continue # The first one was created.

            try:
                previous_item = self.get_queryset()[index - 1]
            except AssertionError:
                previous_item = None
            changed_fields, prev_values, cur_values = [], [], []
            for field in fields:
                if field.name == "modified_date": continue

                prev_value = getattr(previous_item, field.name, "-")
                prev_value = prev_value if prev_value else "-"

                curr_value = getattr(item, field.name, "-")
                curr_value = curr_value if curr_value else "-"

                # Handle nice choices keys
                if hasattr(field, '_choices') and len(field._choices) and curr_value != '-':
                    curr_value = next(
                        (x[1] for x in field._choices if str(x[0]) == str(curr_value)))
                # Handle foreign keys.
                elif hasattr(field, 'related') and curr_value != '-':
                    try:
                        curr_value = field.related.parent_model.objects.get(id=curr_value)
                    except ObjectDoesNotExist: curr_value = "Deleted"

                if hasattr(field, '_choices') and len(field._choices) and prev_value != '-':
                    prev_value = next(
                        (x[1] for x in field._choices if str(x[0]) == str(prev_value)))
                elif hasattr(field, 'related') and prev_value != '-':
                    try:
                        prev_value = field.related.parent_model.objects.get(id=prev_value)
                    except ObjectDoesNotExist: prev_value = "Deleted"

                if prev_value != curr_value:
                    changed_fields.append(field.name)
                    prev_values.append(prev_value)
                    cur_values.append(curr_value)
            if len(changed_fields):
                data[4] = u"<br />".join([unicode(x) for x in changed_fields])
                data[5] = u"<br />".join([unicode(x) for x in prev_values])
                data[6] = u"<br />".join([unicode(x) for x in cur_values])
                results.append(data)
        results.reverse()
        #log.debug(pformat(results))
        return results

    def get(self, context, **kwargs):
        if self.request.is_ajax():
            result = self.get_serialized_data()
            return HttpResponse(json.dumps({"aaData": result}), mimetype="application/json")
        return super(HistoryListView, self).get(context, **kwargs)
