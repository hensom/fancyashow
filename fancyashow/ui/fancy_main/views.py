from django.conf                      import settings
from django.http                      import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.shortcuts                 import render_to_response
from django.core.urlresolvers         import reverse
from datetime                         import datetime, timedelta
from fancyashow.db.models             import Show, Artist, Venue
from fancyashow.ui.fancy_main.filters import ShowDateFilter, ShowDateRangeFilter, VenueFilter

def root(request):
  today = datetime.today()
  
  return shows_by_date(request, today.year, today.month, today.day)

def shows_by_date(request, year, month, day):
  requested_day  = datetime(int(year), int(month), int(day))
  prev_day       = requested_day - timedelta(days = 1)
  next_day       = requested_day + timedelta(days = 1)

  prev_day_url   = reverse('shows-by-date', kwargs = {'year': prev_day.year, 'month': prev_day.month, 'day': prev_day.day})
  next_day_url   = reverse('shows-by-date', kwargs = {'year': next_day.year, 'month': next_day.month, 'day': next_day.day})

  date_filter    = ShowDateFilter(requested_day)
  shows          = list(date_filter.apply(Show.objects).order_by('-rank'))

  context = {
    'day':          requested_day,
    'period':       None,
    'prev_day':     prev_day,
    'next_day':     next_day,
    'prev_day_url': prev_day_url,
    'next_day_url': next_day_url
  }
  
  return show_list(request, shows, 'fancy_main/shows_on_date.html', context)
  
def show_list(request, shows, template, context):
  today    = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  tomorrow = today + timedelta(days = 1)

  artist_map     = {}
  artist_to_show = {}
  venue_map      = dict((v.url, v) for v in Venue.objects())
  venues         = venue_map.values()
  
  venues.sort(key = lambda v: v.name.lower())

  for show in shows:
    for info in filter(lambda x: x.artist_id, show.artists):
      if info.artist_id not in artist_map:
        artist_to_show[info.artist_id] = {'artist': None, 'shows': []}

      artist_to_show[info.artist_id]['shows'].append(show)
      artist_map[info.artist_id] = True

  if artist_map:
    artist_map = Artist.objects.in_bulk(artist_map.keys())

    for artist_id, artist_info in artist_to_show.iteritems():
      artist_info['artist'] = artist_map[artist_id]

  artists = artist_to_show.values()

  artists.sort(key = lambda i: i['artist'].name.lower().strip(" \r\n"))
  
  context.update({
    'today':       today,
    'tomorrow':    tomorrow,
    'shows':       shows,
    'artist_map':  artist_map,
    'artists':     artists,
    'venue_map':   venue_map,
    'venues':      venues,
    'hot_ranking': settings.ARTIST_HOT_RANKING
  })

  return render_to_response(template, context)
  
def shows_by_venue(request, venue):
  venue = Venue.objects.get(normalized_name = venue)
  
  today = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  
  filters = (
    ShowDateFilter(today, method = 'gte'),
    VenueFilter(venue)
  )

  shows = Show.objects()

  for f in filters:
    shows = f.apply(shows)
    
  shows = list(shows.order_by('date').limit(60))

  return show_list(request, shows, 'fancy_main/shows_at_venue.html', {'venue': venue})
  
def shows_this_weekend(request):
  start = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  
  # 4, 5, 6 - Fri, Sat, Sun
  if start.weekday() not in (4, 5, 6):
    start += timedelta(4 - start.weekday())
    
  end = start + timedelta(days = 6 - start.weekday())
  
  range_filter = ShowDateRangeFilter(start, end)
  
  shows        = list(range_filter.apply(Show.objects).order_by('-rank'))
  
  context = {
    'day':          None,
    'period':       'this-weekend',
    'period_label': 'This Weekend'
  }

  return show_list(request, shows, 'fancy_main/shows_on_date.html', context)

def artist_info(req, name):
  pass