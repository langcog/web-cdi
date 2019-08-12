from django.core.exceptions import PermissionDenied

class StudyOwnerMixin (object):
    permission_denied_message = "You do not have access to edit Administrations in this Study"
    
    def dispatch (self, request, *args, **kwargs):
        if self.get_object().study.researcher != request.user:
            print(self.get_object().study.researcher, request.user)
            raise PermissionDenied(self.get_permission_denied_message())
        return super(StudyOwnerMixin, self).dispatch(request, *args, **kwargs)
    
    def get_permission_denied_message(self):
        """
        Override this method to override the permission_denied_message attribute.
        """
        return self.permission_denied_message

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())