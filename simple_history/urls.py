# -*- coding: utf-8 -*-
"""urls.py: Django simple_history"""

from __future__ import unicode_literals

import logging
from django.conf.urls import patterns, url
from .views import HistoryListView, HistoryDataTableView

__author__ = 'Steven Klass'
__date__ = '9/18/12 10:46 PM'
__copyright__ = 'Copyright 2012 IC Manage. All rights reserved.'
__credits__ = ['Steven Klass', ]

log = logging.getLogger(__name__)


urlpatterns = patterns(
    '',
    url(r'^list/(?P<app_label>\w+)/(?P<model>\w+)/(?P<field>\w+)/(?P<constraint>\w+)$',
        HistoryDataTableView.as_view(), name='historical_list'),
    url(r'^list/ajax/(?P<app_label>\w+)/(?P<model>\w+)/(?P<field>\w+)/(?P<constraint>\w+)$',
        HistoryDataTableView.as_view(),name='historical_ajax_list'),
)

