from django.conf.urls.defaults import *
from fancyashow.ui.fancy_main  import views
from fancyashow.ui.fancy_main  import auth

DATE   = '(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)'
PERIOD = '(?P<period>[^/]+)'

urlpatterns = patterns('',
  url(r'^$',                                                              views.root,  name = 'root'),
  url(r'^$',                                                              views.root,  name = 'shows'),
  url(r'^login/$',                                                        auth.login,  name = 'login'),
  url(r'^logout/$',                                                       auth.logout, name = 'logout'),
  url(r'^shows/%s' % DATE,                                                views.shows, name = 'shows-on-date'),
  url(r'^shows/%s' % PERIOD,                                              views.shows, name = 'shows-during-period'),
  url(r'^me/',                                                            views.my_shows, name = 'my-shows'),
  url(r'^city/(?P<city>[^\/]+)/shows/%s' % DATE,                          views.shows, name = 'shows-in-city-on-date'),
  url(r'^city/(?P<city>[^\/]+)/shows/%s' % PERIOD,                        views.shows, name = 'shows-in-city-during-period'),
  url(r'^city/(?P<city>[^\/]+)/(?P<neighborhood>.*?)/shows/%s' % DATE,    views.shows, name = 'shows-in-neighborhood-on-date'),
  url(r'^city/(?P<city>[^\/]+)/(?P<neighborhood>.*?)/shows/%s' % PERIOD,  views.shows, name = 'shows-in-neighborhood-during-period'),
  url(r'^venues/$',                                                                                views.venues,         name = 'venues'),
  url(r'^venues/(?P<venue>[^\/]+)/$',                                                              views.shows_at_venue, name = 'shows-at-venue'),
  url(r'^venues/(?P<venue>[^\/]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<artist>[^\/]+)?$', views.show_details,   name = 'show-details'),
  url(r'^festivals/$',                                                                             views.festivals,      name = 'festivals'),
  url(r'^festivals/(?P<festival>[^\/]+)$',                                                         views.shows_at_festival, name = 'shows-at-festival'),
)
