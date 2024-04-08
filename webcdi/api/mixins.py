import json

from django.contrib.auth import authenticate
from django.http import JsonResponse

from researcher_UI.models import Study


class StudyOwnerMixin(object):
    permission_denied_message = None

    def dispatch(self, request, *args, **kwargs):
        data = json.loads(request.body)
        username = data["username"]
        password = data["password"]
        user = authenticate(username=username, password=password)
        if not user:
            self.permission_denied_message = "Invalid User Credentials"
            return JsonResponse(
                status=401, data={"error": self.permission_denied_message}
            )
            # raise PermissionDenied('Invalid User')
        study = Study.objects.get(pk=kwargs["pk"])
        if study.researcher != user:
            self.permission_denied_message = "You do not have access to this Study"
            # raise PermissionDenied(self.get_permission_denied_message())
            return JsonResponse(
                status=403, data={"error": self.permission_denied_message}
            )
        return super().dispatch(request, *args, **kwargs)
