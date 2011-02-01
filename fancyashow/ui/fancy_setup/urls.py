import mongoadmin
from django.conf.urls.defaults import *
from django.conf import settings

mongoadmin.autodiscover('admin')

urlpatterns = patterns('',
  url(r'^%s(?P<path>.*)$' % settings.SHOW_MEDIA_URL.lstrip('/'), 'django.views.static.serve', {'document_root': settings.SHOW_MEDIA_DIR}),
  url(r'^admin/', include('fancyashow.ui.fancy_admin.urls')),
  url(r'^mongo-admin/', include(mongoadmin.site.urls, namespace='mongoadmin')),
  url(r'^password_required/$', 'password_required.views.login'),
  url(r'^api/', include('fancyashow.ui.fancy_api.urls')),
  url(r'^', include('fancyashow.ui.fancy_main.urls')),
)

if settings.DEBUG:
  urlpatterns += patterns('',
    url(r'^static/(?:[^\/]+)/(?P<path>.*)$',   'django.views.static.serve', {'document_root': settings.STATIC_BASE_DIR})
  )
