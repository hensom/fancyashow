import re
import urllib
from datetime import datetime, timedelta
from django   import template
from django.template          import Node
from django.core.urlresolvers import reverse
from django.conf              import settings
from django.utils             import simplejson
from fancyashow.db.models     import Show, Venue, City

from fancyashow.ui.fancy_api.resources import VisitorResource, ShowResource

register = template.Library()

def datetime_or_none(day):
  if day:
    return day.strftime('%F %H:%M:%S')
  else:
    return None
    
def show_json(show):
  kwargs = {
    'venue':  show.venue.slug(),
    'year':   show.date.year,
    'month':  show.date.month,
    'day':    show.date.day,
    'artist': show.slug()
  }
  
  info = {
    'id':        show.id_str,
    'title':     show.full_title(),
    'date':      datetime_or_none(show.date),
    'show_time': datetime_or_none(show.show_time),
    'door_time': datetime_or_none(show.door_time),
    'url':       reverse('show-details', kwargs = kwargs)
  }
  
  return info

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
  
@register.simple_tag
def show_url(show):
  kwargs = {
    'venue':  show.venue.slug(),
    'year':   show.date.year,
    'month':  show.date.month,
    'day':    show.date.day,
    'artist': show.slug()
  }
  return reverse('show-details', kwargs = kwargs)
  
@register.simple_tag
def show_title(show):
  return show.full_title()
  
@register.simple_tag
def show_list_json(request, shows):
  sr = ShowResource()
  return sr.serialize(request, [sr.full_dehydrate(show) for show in shows], 'application/json')
  
VIDEO_IMPL = {
  'youtube': '<iframe title="%(title)s" class="youtube-player" type="text/html" width="%(width)s" height="%(height)s" src="http://www.youtube.com/embed/%(media_id)s?rel=0&showinfo=1" frameborder="0"></iframe>',
  'vimeo':   '<iframe title ="%(title)s" src="http://player.vimeo.com/video/%(media_id)s?portrait=0&amp;color=ff9933" width="%(width)s" height="%(height)s" frameborder="0"></iframe>'  
}
  
@register.simple_tag
def artist_video(artist, width = 300, height = 200, number = 2):
  end   = datetime.today()
  start = end - timedelta(days = 30)
  
  videos = [(v, v.stats.stats_over(start, end)) for v in artist.videos]

  videos.sort(key = lambda i: i[1].number_of_plays, reverse = True)
  
  ret = []

  for video, stats in videos:
    if video.system_id in VIDEO_IMPL and len(ret) < number:
      context = {
        'title':    urllib.quote(video.title),
        'width':    width,
        'height':   height,
        'media_id': video.media_id
      }

      ret.append(VIDEO_IMPL[video.system_id] % context)
    
  return ''.join(ret)
  
@register.simple_tag
def visitor_info_json(request):
  if not request.user.is_authenticated():
    return '{}'
  else:
    vr = VisitorResource()
    return vr.serialize(request, vr.full_dehydrate(request.user), 'application/json')

@register.inclusion_tag('fancy_main/templatetags/show_featured_listing.html')
def show_featured_listing(show, saved_shows):
  return {'show': show, 'show_saved': show.id in saved_shows}
  
@register.inclusion_tag('fancy_main/templatetags/show_detailed_link.html')
def show_detailed_link(show):
  return {'show': show}

@register.inclusion_tag('fancy_main/templatetags/show_list.html')
def show_list(shows, artist_map, venue_map):
  featured_shows = shows[:9]
  other_shows    = shows[9:]
  
  return {'shows': shows, 'artist_map': artist_map, 'venue_map': venue_map, 'featured_shows': featured_shows, 'other_shows': other_shows }
  
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

@register.inclusion_tag('fancy_main/templatetags/title.html')
def show_list_title(show_context):
  return {'show_context': show_context}
  

@register.inclusion_tag('fancy_main/templatetags/nav.html')
def show_list_nav(show_context):
  today    = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
  tomorrow = today + timedelta(days = 1)
  
  if show_context.multiday and show_context.has_period:
    date_type  = '-during-period'
    date_args = {
      'period': show_context.period
    }
  else:
    date_type  = '-on-date'
    date_args = {
      'year':  show_context.start_date.year,
      'month': show_context.start_date.month,
      'day':   show_context.start_date.day
    }
    
  if show_context.location:
    if show_context.location.get('neighborhood'):
      location_type = '-in-neighborhood'
      location_args = {
        'city':         show_context.location.get('city').slug,
        'neighborhood': show_context.location.get('neighborhood').slug
      }
    else:
      location_type = '-in-city'
      location_args = {
        'city': show_context.location.get('city').slug
      }
  else:
    location_type = ''
    location_args = {}
    
  cities = []
  
  for city in City.objects.order_by('name'):
    city_args = date_args.copy()
    city_args['city'] = city.slug

    city_info = {    
      'name':          city.name,
      'set_url':       reverse('shows-in-city%s' % date_type, kwargs = city_args),
      'neighborhoods': []
    }
    
    for n in city.neighborhoods:
      neighborhood_args = date_args.copy()
      neighborhood_args.update({'city': city.slug, 'neighborhood': n.slug})

      city_info['neighborhoods'].append({
        'name':    n.name,
        'set_url': reverse('shows-in-neighborhood%s' % date_type, kwargs = neighborhood_args)
      })

    city_info['neighborhoods'].sort(key = lambda n: n['name'])
    
    cities.append(city_info)

  def choice(day, label = None, classes = ''):
    if not label:
      label = day.strftime('%a, %b %d')
      
    date_args = location_args.copy()
    
    date_args.update({'year': day.year, 'month': day.month, 'day': day.day})

    return {'url': reverse('shows%s-on-date' % location_type, kwargs = date_args), 'classes': classes.strip(), 'label': label}
    
  days = [ choice(today, 'Tonight'), choice(tomorrow, 'Tomorrow') ]
    
  for period_slug, period_name in show_context.supported_periods():
    period_args = location_args.copy()
    period_args.update({'period': period_slug})

    period = {
      'label': period_name, 'url': reverse('shows%s-during-period' % location_type, kwargs = period_args)
    }

    days.append(period)

  return {'days': days, 'cities': cities, 'show_context': show_context}

NEWLINE_RE = re.compile('\n')
SPACE_RE   = re.compile('\s+')

class SingleLineNode(Node):
  def __init__(self, nodelist):
    self.nodelist = nodelist

  def render(self, context):
    s = self.nodelist.render(context).strip()

    s = NEWLINE_RE.sub(' ', s)

    return SPACE_RE.sub(' ', s)

class AttributeNode(SingleLineNode):
  def render(self, context):
    return super(AttributeNode, self).render(context).replace('"', '\\"')

@register.tag
def singleline(parser, token):
    nodelist = parser.parse(('endsingleline',))
    parser.delete_first_token()

    return SingleLineNode(nodelist)

@register.tag
def attribute(parser, token):
    nodelist = parser.parse(('endattribute',))
    parser.delete_first_token()
    return AttributeNode(nodelist)
