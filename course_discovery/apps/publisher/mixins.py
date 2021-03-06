from functools import wraps

from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import method_decorator

from course_discovery.apps.publisher.models import Course, Seat
from course_discovery.apps.publisher.utils import is_internal_user, is_publisher_admin, is_publisher_user


class PublisherPermissionMixin(object):

    permission = None

    def get_course(self):
        publisher_object = self.get_object()
        if isinstance(publisher_object, Course):
            return publisher_object
        if isinstance(publisher_object, Seat):
            return publisher_object.course_run.course
        if hasattr(publisher_object, 'course'):
            return publisher_object.course

        return None

    def has_user_access(self, user):
        course = self.get_course()
        return (
            check_roles_access(user) or
            check_course_organization_permission(user, course, self.permission)
        )

    def permission_failed(self):
        return HttpResponseForbidden()

    def dispatch(self, request, *args, **kwargs):
        if not self.has_user_access(request.user):
            return self.permission_failed()

        return super(PublisherPermissionMixin, self).dispatch(request, *args, **kwargs)


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class FormValidMixin(object):
    change_state = False

    def form_valid(self, form):
        user = self.request.user
        publisher_object = form.save(commit=False)
        publisher_object.changed_by = user
        publisher_object.save()
        form.save_m2m()

        self.object = publisher_object

        return HttpResponseRedirect(self.get_success_url())


def check_roles_access(user):
    """ Return True if user is part of a role that gives implicit access. """
    return is_publisher_admin(user) or is_internal_user(user)


def check_course_organization_permission(user, course, permission):
    """ Return True if user has view permission on organization. """
    if not hasattr(course, 'organizations'):
        return False

    return any(
        [
            user.has_perm(permission, org.organization_extension)
            for org in course.organizations.all()
        ]
    )


def publisher_user_required(func):
    """
    View decorator that requires that the user is part any publisher group
    permissions.
    """
    @wraps(func)
    def wrapped(request, *args, **kwargs):  # pylint: disable=missing-docstring
        if is_publisher_user(request.user):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(u"Must be Publisher user to perform this action.")

    return wrapped


class PublisherUserRequiredMixin(object):
    """
    Mixin to view the user is part of any publisher app group.
    """
    @method_decorator(publisher_user_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PublisherUserRequiredMixin, self).dispatch(request, *args, **kwargs)


class LanguageModelSelect2Multiple(autocomplete.ModelSelect2Multiple):
    """
    QuerySet support for LanguageTag choices.

    django.autocomplete queryset expects id field to filter choices but LanguageTag
    does not have id field in it. It has code as primary key instead of id.
    """

    def filter_choices_to_render(self, selected_choices):
        # pylint: disable=no-member
        self.choices.queryset = self.choices.queryset.filter(
            code__in=[c for c in selected_choices if c]
        )
