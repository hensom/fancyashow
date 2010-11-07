from django.conf.urls.defaults import *
from fancyashow.ui.fancy_main  import views

urlpatterns = patterns('',
  url(r'^$',                                                 views.root,               name = 'root'),
  url(r'^shows/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', views.shows_by_date,      name = 'shows-by-date'),
  url(r'^shows/weekend/$',                                   views.shows_this_weekend, name = 'shows-this-weekend'),
  url(r'^shows/(?P<venue>[^\/]+)/$',                         views.shows_by_venue,     name = 'shows-at-venue'),
  url(r'^shows/(?P<venue>[^\/]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<artist>[^\/]+)?$',                           views.show_details,       name = 'show-details')
)
