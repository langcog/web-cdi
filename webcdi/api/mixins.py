import json
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from researcher_UI.models import Study

class StudyOwnerMixin (object):
    permission_denied_message = None

    def dispatch (self, request, *args, **kwargs):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        user = authenticate(username=username, password=password)
        if not user:
            self.permission_denied_message = "Invalid User Credentials"
            #raise PermissionDenied('Invalid User')
        study = Study.objects.get(pk=kwargs['pk'])
        if study.researcher != user:
            self.permission_denied_message = "You do not have access to this Study"
            #raise PermissionDenied(self.get_permission_denied_message())
        return super().dispatch(request, *args, **kwargs)
    
    def get_permission_denied_message(self):
        """
        Override this method to override the permission_denied_message attribute.
        """
        return self.permission_denied_message

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
       