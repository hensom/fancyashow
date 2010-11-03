import urllib
from datetime import datetime, timedelta
from django   import template
from django.core.urlresolvers import reverse
from django.conf              import settings

register = template.Library()

def static_url(base, path, version = None):
  if not version:
    version = settings.RESOURCE_VERSION
    
  return '%s/%s/%s/%s' % (settings.STATIC_BASE_URL.rstrip('/'), version, base, path)

@register.simple_tag
def css_url(path):
  return static_url('css', path)

@register.simple_tag
def js_url(path):
  return static_url('js', path)  

@register.inclusion_tag('fancy_main/templatetags/show_list.html')
def show_list(shows, artist_map, venue_map):
  return {'shows': shows, 'artist_map': artist_map, 'venue_map': venue_map}
  
@register.inclusion_tag('fancy_main/templatetags/artist_profiles.html')
def artist_profiles(artist_info, artist_map):
  profiles = []

  if artist_info.artist_id:
    artist = artist_map[artist_info.artist_id]
    
    profiles = artist.profiles

  return {'profiles': profiles}
  
@register.inclusion_tag('fancy_main/templatetags/venue_options.html')
def venue_options(show, venue_map):
  venue = venue_map.get(show.venue.url)

  return {'show': show, 'venue': venue}

@register.inclusion_tag('fancy_main/templatetags/nav.html')
def day_nav(venues, day, period):
  return nav(venues, chosen_day = day, period = period)

@register.inclusion_tag('fancy_main/templatetags/nav.html')
def venue_nav(venues, venue):
  return nav(venues, venue = venue)

def nav(venues, venue = None, chosen_day = None, period = None):
  today    = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  tomorrow = today + timedelta(days = 1)
  
  venues_by_city_map = { }
  
  venues.sort(key = lambda v: v.name)
  
  for v in venues:
    if v.city not in venues_by_city_map:
      venues_by_city_map[v.city] = []

    venue_info = {
      'name':          v.name,
      'show_list_url': reverse('shows-at-venue', kwargs = {'venue': v.normalized_name})
    }

    venues_by_city_map[v.city].append(venue_info)
    
  venues_by_city = [{'city': city, 'venues': venues} for city, venues in venues_by_city_map.iteritems()]
  
  venues_by_city.sort(key = lambda g: g['city'])

  def choice(day, label = None, classes = ''):
    if not label:
      label = day.strftime('%a, %b %d')
      
    if day and chosen_day == day:
      classes += ' chosen'

    return {'url': reverse('shows-by-date', kwargs = {'year': day.year, 'month': day.month, 'day': day.day}), 'classes': classes.strip(), 'label': label}

  days = [ choice(today, 'Tonight'), choice(tomorrow, 'Tomorrow') ]

  weekend = {'label': 'This Weekend', 'url': reverse('shows-this-weekend')}
  
  if period == 'this-weekend':
    weekend['classes'] = 'chosen'

  days.append(weekend)
    
  this_week = []
  
  sunday = today
  
  while sunday.weekday() != 0:
    sunday -= timedelta(days = 1)
  
  for i in xrange(0, 6):
    week_day = sunday + timedelta(days = i)
    show_url = reverse('shows-by-date', kwargs = {'year': week_day.year, 'month': week_day.month, 'day': week_day.day})

    this_week.append({'date': week_day, 'show_list_url': show_url})

  return {'days': days, 'venues_by_city': venues_by_city, 'venue': venue, 'this_week': this_week, 'period': period}