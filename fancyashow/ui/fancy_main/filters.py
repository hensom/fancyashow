from datetime    import datetime, date
from mongoengine import Q

class DocumentFilter(object):
  def apply(self, qs):
    raise NotImplemented()
    
class SearchFilter(object):
  def __init__(self, query, *fields):
    super(SearchFilter, self).__init__()

    self.query  = query
    self.fields = fields
    
  def apply(self, qs):
    for part in self.query.split(' '):
      field_filter = []

      for field in self.fields:
        field_filter.append(Q(**{'%s__icontains' % field: part}))

      qs = qs.filter(reduce(lambda x,y: x | y, field_filter))
    
    return qs

class DateFilter(object):
  def __init__(self, query_date, field, method = None):
    if isinstance(query_date, date):
      query_date = datetime(query_date.year, query_date.month, query_date.day)

    self.query_date = query_date
    self.field      = field
    self.method     = method
    
  def apply(self, qs):
    if self.method:
      return qs.filter(**{'%s__%s' % (self.field, self.method): self.query_date})
    else:
      return qs.filter(**{self.field: self.query_date})
      
class ShowDateFilter(DateFilter):
  def __init__(self, query_date, method = None):
    super(ShowDateFilter, self).__init__(query_date, 'date', method = method)
    
class VenueFilter(object):
  def __init__(self, venue):
    self.venue = venue

  def apply(self, qs):
    return qs.filter(venue__url = self.venue.url)
    
class ShowDateRangeFilter(object):
  def __init__(self, start_date, end_date):
    if isinstance(start_date, date):
      start_date = datetime(start_date.year, start_date.month, start_date.day)

    if isinstance(end_date, date):
      end_date = datetime(end_date.year, end_date.month, end_date.day)

    self.start_date = start_date
    self.end_date   = end_date

  def apply(self, qs):
    query = Q(date__gte = self.start_date) & Q(date__lte = self.end_date)

    return qs.filter(query)
    
class InvalidContextFilter(Exception):
  pass
    
class ShowContext(object):
  def __init__(self, start_date, end_date, location = None, venue = None):
    self.start_date = start_date
    self.end_date   = end_date
    self.location   = location
    self.venue      = venue
    self._shows     = None

  @classmethod    
  def from_request(self, year, month, day, period, city, neighborhood, venue):
    if period:
      self.start_date, self.end_date = self._parse_period(period)
    else:
      try:
        self.start_date = datetime(int(year), int(month), int(day)).date()
        self.end_date   = self.start_date
      except ValueError, e:
        raise InvalidContextFilter(e)

  def _parse_period(self, period):
    if period == 'weekend':
      start = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)

      # 4, 5, 6 - Fri, Sat, Sun
      if start.weekday() not in (4, 5, 6):
        start += timedelta(4 - start.weekday())

      end = start + timedelta(days = 6 - start.weekday())
      
      return start, end
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
        in_location = lambda v: self.location['city'] == v.city or self.location['neighborhood'] == v.neighborhood
        
        venues.extend(filter(in_location, Venue.objects()))
        
      if venues:
        shows = shows.filter(venue__url__in = [v.url for v in venues])
        
      shows.order_by('-rank')
        
      self._shows = list(shows)
      
    return list(self._shows)
    
  @property
  def period_name(self):
    FORMAT = '%M, %d'

    if self.start_date == self.end_date:
      return self.start_date.strftime(FORMAT)
    else:
      return ' to '.join((self.start_date.strftime(FORMAT), self.end_date.strftime(FORMAT)))
    
  @property
  def location_name(self):
    if self.venue:
      return self.venue.name
    elif self.location.get('neighborhood'):
      return self.location.get('neighborhood')
    elif self.location.get('city'):
      return self.location.get('city')
    else:
      return 'NYC'