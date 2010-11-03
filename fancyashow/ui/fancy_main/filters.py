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