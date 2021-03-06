import logging
from django.conf                      import settings
from django.http                      import HttpResponseRedirect, HttpResponse, HttpResponseServerError, Http404
from django.shortcuts                 import render_to_response
from django.core.urlresolvers         import reverse
from django.template                  import RequestContext
from datetime                         import datetime, timedelta
from mongoengine                      import Q
from fancyashow.db.models             import Show, Artist, Venue, City
from fancyashow.db.models             import Festival, FestivalSeason
from fancyashow.ui.fancy_main.context import ShowContext, InvalidContextFilter
from fancyashow.ui.fancy_main.forms   import ShowChoiceForm

LOG = logging.getLogger(__name__)

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
      
  saved_shows = { }

  if request.user.is_authenticated():
    saved_shows = request.user.starred_show_set.get_id_dict();

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
    'hot_ranking': settings.ARTIST_HOT_RANKING,
    'saved_shows': saved_shows
  })

  return render_to_response(template, RequestContext(request, context))
  
def shows_at_venue(request, venue):
  venue = Venue.objects.get(slug = venue)
  
  start = datetime.today()
  end   = start + timedelta(days = 60)

  show_context = ShowContext(start, end, venue = venue)

  shows = list(show_context.shows)
  
  shows_by_rank = list(shows)
  shows_by_rank.sort(key = lambda s: s.rank)
  
  shows_by_date = list(shows)
  shows_by_date.sort(key = lambda s: s.date)
  
  venues_near_by = list(Venue.objects.filter(city = venue.city, neighborhood = venue.neighborhood, id__ne = venue.id).order_by('name'))

  context = {
    'show_context':  show_context,
    'shows_by_rank': shows_by_rank,
    'shows_by_date': shows_by_date,
    'other_venues':  venues_near_by,
    'venue':         venue
  }

  return show_list(request, shows, 'fancy_main/shows_at_venue.html', context)
  
def show_details(request, venue, year, month, day, artist):
  venue = Venue.objects.get(slug = venue)
  day   = datetime(int(year), int(month), int(day))
  today = datetime.today()
  look_until = today + timedelta(days = 30)

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
    show_range   = Q(date__gte = today) & Q(date__lte = look_until)
    artist_shows = Show.objects(artist_ids__in = artist_ids.keys(), id__ne = show.id).filter(show_range).order_by('date')

    for artist_show in artist_shows:
      for info in filter(lambda x: x.artist_id, artist_show.artists):
        if info.artist_id not in shows_by_artist:
          shows_by_artist[info.artist_id] = []
  
        shows_by_artist[info.artist_id].append(artist_show)
  
    artist_map = Artist.objects.in_bulk(artist_ids.keys())
  
  for artist_info in show.artists:
    artists.append({'info': artist_info, 'artist': artist_map.get(artist_info.artist_id), 'shows': shows_by_artist.get(artist_info.artist_id, [])})

  venues = list(Venue.objects())
  
  saved_shows = { }
  
  if request.user.is_authenticated():
    saved_shows = request.user.starred_show_set.get_id_dict();

  context = {
    'show':        show,
    'shows':       [show],
    'artists':     artists,
    'venue':       Venue.objects.get(url = show.venue.url),
    'venues':      venues,
    'saved_shows': saved_shows
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
  
def my_shows(request):
  user = request.user
  
  upcoming_shows = []
  past_shows     = []
  shows          = []
  
  if user.is_authenticated() and user.starred_show_set.show_ids:
    shows = list(user.starred_show_set.shows().order_by('date'))

    today = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    
    upcoming_shows = filter(lambda s: s.date >= today, shows)
    past_shows     = filter(lambda s: s.date < today, shows)

  context = {
    'upcoming_shows': upcoming_shows,
    'past_shows':     past_shows
  }

  return show_list(request, shows, 'fancy_main/my_shows.html', context)
  
def festivals(request):
  today   = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  seasons = dict((s.festival_id, s) for s in FestivalSeason.objects.all()) #.filter(Q(start_date__gte = today) | Q(end_date__gte = today)))
  festivals = []
  all_shows = []
  
  for festival in Festival.objects().order_by('name'):
    season = seasons.get(festival.id)
    
    if season:
      shows = list(Show.objects.filter(id__in = season.show_set.show_ids).order_by('date'))[:6]
      
      all_shows.extend(shows)

      festivals.append({
        'festival': festival,
        'season':   season,
        'shows':    shows
      })
      
  saved_shows = { }

  if request.user.is_authenticated():
    saved_shows = request.user.starred_show_set.get_id_dict()
  
  context = {
    'festivals':   festivals,
    'shows':       all_shows,
    'saved_shows': saved_shows
  }
  
  return render_to_response('fancy_main/festivals.html', RequestContext(request, context))
  
def shows_at_festival(request, festival):
  today   = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  festival = Festival.objects.get(merge_key = festival)
  season   = FestivalSeason.objects.get(festival_id = festival.id)
  shows    = list(Show.objects.filter(id__in = season.show_set.show_ids).order_by('date'))
  
  upcoming_shows = []
  past_shows     = []
    
  upcoming_shows = filter(lambda s: s.date >= today, shows)
  past_shows     = filter(lambda s: s.date < today, shows)
  

  context = {
    'festival':       festival,
    'season':         season,
    'upcoming_shows': upcoming_shows,
    'past_shows':     past_shows,
    'saved_shows':    { },
    'shows':          shows
  }

  return show_list(request, shows, 'fancy_main/shows_at_festival.html', context)