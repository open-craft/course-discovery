from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import method_decorator

from course_discovery.apps.publisher.models import Course, Seat, OrganizationExtension
from course_discovery.apps.publisher.utils import is_publisher_admin, is_internal_user


class ViewPermissionMixin(object):

    def get_course(self):
        publisher_object = self.get_object()
        if isinstance(publisher_object, Course):
            return publisher_object
        if isinstance(publisher_object, Seat):
            return publisher_object.course_run.course
        if hasattr(publisher_object, 'course'):
            return publisher_object.course

        return None

    def check_user(self, user):
        course = self.get_course()
        return check_user_course_access(user, course)

    def permission_failed(self):
        return HttpResponseForbidden()

    def dispatch(self, request, *args, **kwargs):
        if not self.check_user(request.user):
            return self.permission_failed()

        return super(ViewPermissionMixin, self).dispatch(request, *args, **kwargs)


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

        if self.change_state:
            publisher_object.change_state(user=user)

        self.object = publisher_object

        return HttpResponseRedirect(self.get_success_url())


def check_roles_access(user):
    """ Return True if user is part of a role that gives implicit access. """
    if is_publisher_admin(user) or is_internal_user(user):
        return True

    return False


def check_course_organization_permission(user, course):
    """ Return True if user has view permission on organization. """
    if not hasattr(course, 'organizations'):
        return False

    return any(
        [
            user.has_perm(OrganizationExtension.VIEW_COURSE, org.organization_extension)
            for org in course.organizations.all()
        ]
    )


def check_user_course_access(user, course):
    """ Return True if user is admin/internal user or has access permission. """

    return check_roles_access(user) or check_course_organization_permission(user, course)
