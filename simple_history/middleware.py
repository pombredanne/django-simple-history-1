# -*- coding: utf-8 -*-
"""models.py: Simple History Middleware - sued for capturing the user"""

from __future__ import unicode_literals

from base64 import b64decode

from django.db.models import signals
from django.utils.functional import curry
from django.utils.decorators import decorator_from_middleware
from django.contrib.auth.models import User

from registration import FieldRegistry

__author__    = 'Marty Alchin'
__date__      = '2011/08/29 20:43:34'
__credits__   = ['Marty Alchin', 'Corey Bertram', 'Steven Klass']


class CurrentUserMiddleware(object):

    def process_request(self, request):
        if request.method in ['GET', 'HEAD', 'OPTIONS', 'TRACE']:
            # We aren't doing anything return..
            return

        if 'HTTP_AUTHORIZATION' in request.META:
            try:
                username, password = b64decode(request.META['HTTP_AUTHORIZATION']).split(':')
                user = User.objects.get(username=username)
                if not user.check_password(password):
                    user = None
            except:
                user = None
        else:
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            else:
                user = None

        update_users = curry(self.update_users, user)
        signals.pre_save.connect(update_users, dispatch_uid=request, weak=False)

    def update_users(self, user, sender, instance, **kwargs):
        registry = FieldRegistry()
        if sender in registry:
            for field in registry.get_fields(sender):
                setattr(instance, field.name, user)

    def process_response(self, request, response):
        signals.pre_save.disconnect(dispatch_uid=request)
        return response

record_current_user = decorator_from_middleware(CurrentUserMiddleware)
