from django.conf.urls.defaults import *
from fancyashow.ui.fancy_main  import views

urlpatterns = patterns('',
  url(r'^$',                                             views.root,               name = 'root'),
  url(r'^d/(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)/$', views.shows_by_date,      name = 'shows-by-date'),
  url(r'^p/weekend/$',                                   views.shows_this_weekend, name = 'shows-this-weekend'),
  url(r'^v/(?P<venue>[^\/]+)/$',                         views.shows_by_venue,     name = 'shows-at-venue'),
  url(r'^artist/n/(?P<name>.+)/$',                       views.artist_info,        name = 'artist-info'),
)