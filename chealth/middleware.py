import re
from datetime import datetime, timedelta
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.shortcuts import redirect
from social_django.middleware import SocialAuthExceptionMiddleware

from apps.session_security.utils import get_last_activity
from apps.session_security.settings import EXPIRE_AFTER


class GlobalLoginRequiredMiddleware(MiddlewareMixin):
    """
    Main idea from `Julien Phalip <https://www.julienphalip.com/blog/site-wide-login-protection-and-public-views/>`_
    .. note::
        Compatible with django 1.11+
    """

    def __init__(self, get_response=None):
        """
        initialize the middleware:
        - populate `public_patterns` from settings's `PUBLIC_VIEWS` (list) if exists
        - populate `public_views` from settings's `PUBLIC_PATHS` (list of regex) if exists
        :param get_response: the actual view or the next middleware in the chain. provided by django middleware system.
        """
        super(GlobalLoginRequiredMiddleware, self).__init__(get_response)
        self.public_patterns = []
        self.public_views = []
        if hasattr(settings, 'PUBLIC_VIEWS'):
            for view_path in settings.PUBLIC_VIEWS:
                view = self.get_view(view_path)
                self.public_views.append(view)
        if hasattr(settings, 'PUBLIC_PATHS'):
            for public_path in settings.PUBLIC_PATHS:
                self.public_patterns.append(re.compile(public_path))

    def get_view(self, view_path):
        """
        returns callable instance of view from view path
        :param view_path: view path, like `'django.contrib.auth.views.login'`
        :return: a callable instance of view, in this example `login`
        """
        i = view_path.rfind('.')
        module_path, view_name = view_path[:i], view_path[i + 1:]
        module = __import__(module_path, globals(), locals(), [view_name])
        return getattr(module, view_name)

    def matches_public_view(self, view):
        """
        Checks is the view is listed in `PUBLIC_VIEWS`, so it is not login required.
        :param callable view: the view
        :return: true if view was listed in `PUBLIC_VIEWS`.
        :rtype: bool
        """
        if self.public_views:
            if hasattr(view, 'view_class'):
                if view.view_class in self.public_views:
                    return True

            if view in self.public_views:
                return True

        return False

    def matches_public_path(self, path):
        """
        Checks if the request path is listed in `PUBLIC_PATHS`, so it is not login required.
        :param string path: the request path
        :return: true if view was listed in `PUBLIC_PATHS`.
        :rtype: bool
        """
        if self.public_patterns:
            for pattern in self.public_patterns:
                if pattern.match(path) is not None:
                    return True
        return False

    def is_login_not_required(self, view):
        """
        Checks if the view function decorated or not
        :param view: view function
        :rtype: bool
        """
        if hasattr(view, 'view_class'):
            if hasattr(view.view_class, 'LOGIN_NOT_REQUIRED'):
                return view.view_class.LOGIN_NOT_REQUIRED

        if hasattr(view, 'LOGIN_NOT_REQUIRED'):
            return view.LOGIN_NOT_REQUIRED

        return False

    def is_session_security_exempt(self, view):
        if hasattr(view, 'view_class'):
            if hasattr(view.view_class, 'SESSION_SECURITY_EXEMPT'):
                return view.view_class.SESSION_SECURITY_EXEMPT

        if hasattr(view, 'SESSION_SECURITY_EXEMPT'):
            return view.SESSION_SECURITY_EXEMPT

        return False

    def is_session_secure(self, request, view):
        if hasattr(request, 'session') and '_session_security' in request.session:
            delta = datetime.now() - get_last_activity(request.session)
            if not self.is_login_not_required(view) and not self.is_session_security_exempt(view) and \
                    delta > timedelta(seconds=EXPIRE_AFTER):
                # if not login_not_required and not session_security_exempt (i.e. login_required)
                # and session_security expires
                return False
        return True

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        checks if this view is not in excluded views (by `PUBLIC_VIEWS`, `PUBLIC_PATHS` or
        `login_not_required` decorator),
        adds `login_required` decorator for view, otherwise run the view itself.
        .. note::
            read the documentation at `djangoproject
            <https://docs.djangoproject.com/en/1.11/topics/http/middleware/#process-view>`_
        :param HttpRequest request: this will be passed to next process_view and finally will be passed to view.
        :param callable view_func: the view function
        :param view_args: the arguments that will be passed to view
        :param view_kwargs: the keyword arguments that will be passed to view
        :return: `None` in order to  continue processing **process_view** in middleware chain or ` HttpResponse`
        for braking middleware chain.
        """
        if self.matches_public_path(request.path) or self.matches_public_view(view_func) or \
                self.is_login_not_required(view_func):
            # login not required
            request.login_not_required = True
            return None
        elif request.user.is_authenticated and self.is_session_secure(request, view_func):
            # session security has not expired or session security is exempted
            return None
        else:
            # login or re-login is required
            namespace = request.resolver_match.namespaces[0] + ':' if request.resolver_match.namespaces else ''
            try:
                login_url = reverse('%sauth' % namespace)
            except NoReverseMatch:
                login_url = reverse('auth')
            return hard_login_required(view_func, login_url=login_url)(request, *view_args, **view_kwargs)


def hard_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: False,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def login_not_required(the_view):
    """
    Decorator which marks the given view as public (not login required).
    This decorator adds a read only property ``	LOGIN_NOT_REQUIRED`` to the view,
    and if it's value be ``True``, the middleware will not force for login.
    If you combine this with a ``login_required`` decorator, your view will be login required.
    """

    def getter(self):
        """
        returns actual value of property
        :param self:
        :return:
        :rtype bool
        """
        return getattr(self, '_LOGIN_NOT_REQUIRED', True)

    setattr(the_view, 'LOGIN_NOT_REQUIRED', property(getter))

    return the_view


def session_security_exempt(the_view):
    """
    Decorator
    """

    def getter(self):
        """
        returns actual value of property
        :param self:
        :return:
        :rtype bool
        """
        return getattr(self, '_SESSION_SECURITY_EXEMPT', True)

    setattr(the_view, 'SESSION_SECURITY_EXEMPT', property(getter))

    return the_view


class MySocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):

    def raise_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is not None:
            return strategy.setting('RAISE_EXCEPTIONS', False)
