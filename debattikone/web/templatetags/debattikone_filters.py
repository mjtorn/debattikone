# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.template import Library

register = Library()

@register.filter
def can_participate(debate, user):
    return debate.can_participate(user)

@register.filter
def can_send(debate, user):
    return debate.can_send(user)

# EOF

