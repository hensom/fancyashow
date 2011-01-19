from django.conf.urls.defaults import patterns, url
from fancyashow.ui.fancy_admin import views

urlpatterns = patterns('',
  url(r'^$',                                     views.summary,          name = 'admin-summary'),
  url(r'^shows/$',                               views.shows,            name = 'admin-shows'),
  url(r'^artists/$',                             views.artists,          name = 'admin-artists'),
  url(r'^media/$',                               views.media,            name = 'admin-media'),
  url(r'^parser-stats/$',                        views.parser_stats,     name = 'admin-parser-stats'),
  url(r'^resource-domains/$',                    views.resource_domains, name = 'admin-resource-domains'),
  url(r'^best-artists/$',                        views.best_artists,     name = 'admin-best-artists'),
  url(r'^artist-stats/$',                        views.artist_stats,     name = 'admin-artist-stats'),
  url(r'^artist/new/$',                          views.artist_new,       name = 'admin-artist-new'),
  url(r'^artist/(?P<artist_id>[^/]+)?/edit/$',   views.artist_edit,      name = 'admin-artist-edit'),
  url(r'show/(?P<show_id>[^/]+)?/edit/$',        views.show_edit,        name = 'admin-show-edit'),
  url(r'show/(?P<show_id>[^/]+)?/link-artist/(?P<artist_position>\d+)/$', views.show_link_artist, name = 'admin-show-link-artist'),
  url(r'^system-stats/$',                        views.system_stats,     name = 'admin-system-stats'),
  url(r'^missing-venues/$',                      views.missing_venues,   name = 'admin-missing-venues'),
  url(r'^geo/$',                                 views.geo,              name = 'admin-geo'),
)