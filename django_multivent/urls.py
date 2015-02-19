from django.conf.urls import patterns, include, url
from django.contrib import admin
from example.views import TestPlanner

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_multivent.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    (r'svg/test/$', TestPlanner.as_view(), {}, "test_planner"),
)
