from django.conf                      import settings
from django.http                      import HttpResponseRedirect, HttpResponse, HttpResponseServerError, Http404
from django.shortcuts                 import render_to_response
from django.core.urlresolvers         import reverse
from django.template                  import RequestContext
from datetime                         import datetime, timedelta
from fancyashow.db.models             import Show, Artist, Venue, City
from fancyashow.ui.fancy_main.context import ShowContext, InvalidContextFilter
def root(request):
  today = datetime.today()
  
  return shows(request, today.year, today.month, today.day)
  
def shows(request, year = None, month = None, day = None, period = None, city = None, neighborhood = None, venue = None):
  show_context = None
  
  try:
    show_context = ShowContext.from_request(year, month, day, period, city, neighborhood, venue)
  except InvalidContextFilter, e:
    raise Http404

  context = {
    'show_context': show_context
  }

  return show_list(request, show_context.shows, 'fancy_main/shows_on_date.html', context)

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

  return render_to_response(template, RequestContext(request, context))
  
def shows_at_venue(request, venue):
  venue = Venue.objects.get(slug = venue)
  
  start = datetime.today()
  end   = start + timedelta(days = 60)

  show_context = ShowContext(start, end, venue = venue)

  shows = list(show_context.shows)

  shows.sort(key = lambda s: s.date)
  
  shows_by_rank = list(shows)
  shows_by_rank.sort(key = lambda s: s.rank)
  
  shows_by_date = list(shows)
  shows_by_date.sort(key = lambda s: s.date)
  
  venues_near_by = list(Venue.objects.filter(city = venue.city, neighborhood = venue.neighborhood).order_by('name'))
  
  venue_index    = venues_near_by.index(venue)
  
  prev_venue, next_venue = None, None
  
  if venue_index > 0:
    prev_venue = venues_near_by[venue_index - 1]
    
  if venue_index + 1 < len(venues_near_by):
    next_venue = venues_near_by[venue_index + 1]

  context = {
    'show_context':  show_context,
    'shows_by_rank': shows_by_rank,
    'shows_by_date': shows_by_date,
    'prev_venue':    prev_venue,
    'next_venue':    next_venue
  }

  return show_list(request, shows, 'fancy_main/shows_at_venue.html', context)
  
def show_details(request, venue, year, month, day, artist):
  venue = Venue.objects.get(slug = venue)
  day   = datetime(int(year), int(month), int(day))
  today = datetime.today()

  matching_shows = Show.objects(venue__url = venue.url, date = day)
  show           = None
  
  for prospect in matching_shows:
    if prospect.slug() == artist:
      show = prospect
      
      break
      
  if not show:
    return show_list(request, matching_shows, 'fancy_main/shows_at_venue.html', {'venue': venue, 'day': day})

  artist_ids      = { }
  artist_map      = { }
  artists         = []
  shows_by_artist = { }

  for info in filter(lambda x: x.artist_id, show.artists):
    if info.artist_id not in artist_map:
      artist_ids[info.artist_id] = True

  if artist_ids:
    artist_shows = Show.objects(artist_ids__in = artist_ids.keys(), id__ne = show.id, date__gte = today).order_by('date')

    for artist_show in artist_shows:
      for info in filter(lambda x: x.artist_id, artist_show.artists):
        if info.artist_id not in shows_by_artist:
          shows_by_artist[info.artist_id] = []
  
        shows_by_artist[info.artist_id].append(artist_show)
  
    artist_map = Artist.objects.in_bulk(artist_ids.keys())
  
  for artist_info in show.artists:
    artists.append({'info': artist_info, 'artist': artist_map.get(artist_info.artist_id), 'shows': shows_by_artist.get(artist_info.artist_id, [])})

  venues = list(Venue.objects())

  context = {
    'show':    show,
    'artists': artists,
    'venue':   Venue.objects.get(url = show.venue.url),
    'venues':  venues
  }

  return render_to_response('fancy_main/show_details.html', RequestContext(request, context))

def venues(request):
  neighborhood_map = { }
  
  today = datetime.now().date()

  show_context = ShowContext(today, today)
  
  shows_by_venue = { }
  
  for show in show_context.shows:
    if not show.venue.url in shows_by_venue:
      shows_by_venue[show.venue.url] = [ ]

    shows_by_venue[show.venue.url].append(show)

  for v in Venue.objects.order_by('name'):
    key = (v.city, v.neighborhood)

    if key not in neighborhood_map:
      neighborhood_map[key] = []

    neighborhood_map[key].append({'venue': v, 'shows': shows_by_venue.get(v.url, [])})

  cities = [ ]

  for city in City.objects():
    city_info = {
      'city':          city,
      'neighborhoods': []
    }

    cities.append(city_info)

    for neighborhood in city.neighborhoods:
      city_info['neighborhoods'].append({
        'neighborhood': neighborhood,
        'venues':       neighborhood_map.get( (city.slug, neighborhood.slug), [])
      })

  context = {
    'cities': cities
  }

  return render_to_response('fancy_main/venues.html', RequestContext(request, context))