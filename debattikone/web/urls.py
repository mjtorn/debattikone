# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

from debattikone.web import views

from django.conf import settings

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        # Static
        (r'^media/(?P<path>.*)/?$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )


# EOF

