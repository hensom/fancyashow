from datetime                         import datetime, timedelta
from fancyashow.db.models             import Show, Venue, City, Neighborhood
from fancyashow.ui.fancy_main.filters import ShowDateRangeFilter
from mongoengine.queryset             import DoesNotExist
from django.conf                      import settings
from django.core.urlresolvers         import reverse
from django.utils.safestring          import mark_safe
from django.utils                     import simplejson as json

class InvalidContextFilter(Exception):
  pass
    
class ShowContext(object):
  def __init__(self, start_date, end_date, location = None, venue = None):
    self.start_date = start_date
    self.end_date   = end_date
    self.location   = location
    self.venue      = venue
    self._shows     = None
    
  def toJSON(self):
    data = {
      'start_date': self.start_date.strftime('%F'),
      'end_date':   self.end_date.strftime('%F')
    }
    
    if self.venue:
      data['venue'] = True
    
    return mark_safe(json.dumps(data))

  @classmethod    
  def from_request(cls, year, month, day, period, city, neighborhood, venue):
    if period:
      start_date, end_date = cls._parse_period(period)
    else:
      try:
        start_date = datetime(int(year), int(month), int(day)).date()
        end_date   = start_date
      except ValueError, e:
        raise InvalidContextFilter(e)
        
    kwargs = { }
        
    if venue:
      try:
        kwargs['venue'] = Venue.objects.get(slug = venue)
      except DoesNotExist:
        raise InvalidContextFilter('Unable to find venue: %s' % venue)
    elif city:
      try:
        kwargs['location'] = {'city': City.objects.get(slug = city)}
      except DoesNotExist:
        raise InvalidContextFilter('Unable to find city: %s' % city)
        
      if neighborhood:
        try:
          matches = filter(lambda n: n.slug ==  neighborhood, kwargs['location']['city'].neighborhoods)

          kwargs['location']['neighborhood'] = matches[0]
        except IndexError:
          raise InvalidContextFilter('Unable to find neighborhood: %s' % neighborhood)
        
    return ShowContext(start_date, end_date, **kwargs)
    
  @classmethod
  def supported_periods(cls):
    periods_by_name, periods_by_date = cls._periods()
    
    periods = periods_by_name.values()
    
    periods.sort(key = lambda p: p['name'].lower())
    
    return ((period['slug'], period['name']) for period in periods)

  @classmethod
  def _periods(cls):
    periods_by_name, periods_by_date = {}, {}
    
    def add_period(name, display_name, start, end, visible = True):
      by_date_key = cls._date_key(start, end)
      
      period = {
        'slug':    name,
        'name':    display_name,
        'start':   start,
        'end':     end,
        'visible': visible
      }

      periods_by_name[name]        = period
      periods_by_date[by_date_key] = period

    add_period(*cls._weekend())

    return periods_by_name, periods_by_date

  @classmethod
  def _weekend(cls):
    start = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)

    # 4, 5, 6 - Fri, Sat, Sun
    if start.weekday() not in (4, 5, 6):
      start += timedelta(4 - start.weekday())

    end = start + timedelta(days = 6 - start.weekday())

    return ('weekend', 'This Weekend', start, end)
    
  @classmethod
  def _parse_period(cls, period):
    periods_by_name, periods_by_date = cls._periods()
    
    if period in periods_by_name:
      return periods_by_name[period]['start'], periods_by_name[period]['end']
    else:
      raise InvalidContextFilter('Unrecognized period: %s' % period)
    
  @property
  def shows(self):
    if not self._shows:
      range_filter = ShowDateRangeFilter(self.start_date, self.end_date)
      
      shows        = range_filter.apply(Show.objects)
      
      venues = []
      
      if self.venue:
        venues.append(self.venue)
      elif self.location:
        if self.location.get('neighborhood'):
          in_location = lambda v: self.location['city'].slug == v.city and self.location['neighborhood'].slug == v.neighborhood
        else:
          in_location = lambda v: self.location['city'].slug == v.city
        
        venues.extend(filter(in_location, Venue.objects()))

      if venues:
        shows = shows.filter(venue__url__in = [v.url for v in venues])
        
      shows.order_by('-rank')
        
      self._shows = list(shows)
      
    return list(self._shows)
  
  @classmethod
  def _date_key(cls, start, end):
    return '%s/%s' % (start.strftime('%F'), end.strftime('%F'))

  @property
  def multiday(self):
    return self.start_date != self.end_date
    
  @property
  def has_period(self):
    periods_by_name, periods_by_date = self._periods()
    
    date_key = self._date_key(self.start_date, self.end_date)
    
    return date_key in periods_by_date
    
  @property
  def period(self):
    periods_by_name, periods_by_date = self._periods()
    
    date_key = self._date_key(self.start_date, self.end_date)
    
    return periods_by_date[date_key]['slug']
    
  @property
  def period_name(self):
    FORMAT = '%a, %b %d'

    if self.start_date == self.end_date:
      today    = datetime.today().date()
      tomorrow = (datetime.today() + timedelta(days = 1)).date()

      if self.start_date == today:
        return 'Tonight'
      elif self.start_date == tomorrow:
        return 'Tomorrow'
      else:
        return self.start_date.strftime(FORMAT)
    else:
      periods_by_name, periods_by_date = self._periods()

      date_key = self._date_key(self.start_date, self.end_date)

      if date_key in periods_by_date:
        return periods_by_date[date_key]['name']
      else:
        return 'Upcoming Shows'
        #return ' to '.join((self.start_date.strftime(FORMAT), self.end_date.strftime(FORMAT)))
    
  @property
  def location_name(self):
    if self.venue:
      return self.venue.name
    elif self.location:
      if self.location.get('neighborhood'):
        return self.location.get('neighborhood').name
      elif self.location.get('city'):
        return self.location.get('city').name

    return settings.DEFAULT_LOCATION_NAME
    
  def _format_rel_date(self, day, comp_day):
    if day < comp_day and day > comp_day - timedelta(days = 6):
      return day.strftime('%a')
    elif day > comp_day and day < comp_day + timedelta(days = 6):
      return day.strftime('%a')
    elif day.year == comp_day.year:
      return day.strftime('%a, %b %d')
    else:
      return day.strftime('%b %d, %Y')
    
  def prev_name(self):
    prev_date = datetime(self.start_date.year, self.start_date.month, self.start_date.day) - timedelta(days = 1)

    return self._format_rel_date(prev_date, datetime.today())
    
  def next_name(self):
    next_date = datetime(self.end_date.year, self.end_date.month, self.end_date.day) + timedelta(days = 1)
    
    return self._format_rel_date(next_date, datetime.today())

  def prev_url(self):
    return self.url_for_date(datetime(self.start_date.year, self.start_date.month, self.start_date.day) - timedelta(days = 1))

  def next_url(self):
    return self.url_for_date(datetime(self.end_date.year, self.end_date.month, self.end_date.day) + timedelta(days = 1))
    
  def anywhere_url(self):
    date_args = {
      'year':  self.start_date.year,
      'month': self.start_date.month,
      'day':   self.start_date.day
    }
    return reverse('shows-on-date', kwargs = date_args)
    
  def today_url(self):
    today = datetime.today()

    date_args = {
      'year':  today.year,
      'month': today.month,
      'day':   today.day
    }
    return reverse('shows-on-date', kwargs = date_args)

  def url_for_date(self, day):
    location_type = ''
    date_args = {
      'year':  day.year,
      'month': day.month,
      'day':   day.day
    }
  
    if self.location:
      if self.location.get('neighborhood'):
        location_type = '-in-neighborhood'
        date_args.update({
          'city':         self.location.get('city').slug,
          'neighborhood': self.location.get('neighborhood').slug
        })
      else:
        location_type = '-in-city'
        date_args.update({
          'city': self.location.get('city').slug
        })
    else:
      location_type = ''

    return reverse('shows%s-on-date' % location_type, kwargs = date_args)