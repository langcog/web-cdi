from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


def login_candidates(identifier):
    """Accounts a login identifier (a username or an email address) refers to.

    Returns (users, matched_on). An exact username wins; then a username in
    any case; then, if the identifier looks like an email address, accounts
    with that email in any case. More than one user means it's ambiguous.
    """
    users = get_user_model()._default_manager
    exact = list(users.filter(username=identifier))
    if exact:
        return exact, "username"
    any_case = list(users.filter(username__iexact=identifier))
    if any_case:
        return any_case, "username"
    if "@" in identifier:
        return list(users.filter(email__iexact=identifier)), "email"
    return [], None


class UsernameOrEmailBackend(ModelBackend):
    """ModelBackend that also accepts an email address, case-insensitively
    (#722). Ambiguous identifiers don't authenticate; the login form asks
    for the username instead."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None
        users, _ = login_candidates(username)
        if len(users) != 1:
            # run the hasher anyway, as ModelBackend does, so a miss takes
            # about as long as a wrong password
            get_user_model()().set_password(password)
            return None
        user = users[0]
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
