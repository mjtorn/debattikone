# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

from debattikone.web import views, ajax_views

from django.conf import settings

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^topic/new/$', views.new_topic, name='new_topic'),
    url(r'^debate/(?P<debate_id>\d+)/(?P<slug>[\w-]+)/$', views.debate, name='debate'),
    url(r'^debate/(?P<debate_id>\d+)/(?P<slug>[\w-]+)/participate/', views.participate, name='participate'),
    url(r'^debate/(?P<debate_id>\d+)/(?P<slug>[\w-]+)/follow', ajax_views.follow, name='follow_debate'),
    url(r'^debate/(?P<debate_id>\d+)/(?P<slug>[\w-]+)/unfollow', ajax_views.unfollow, name='unfollow_debate'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        # Static
        (r'^media/(?P<path>.*)/?$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )


# EOF

