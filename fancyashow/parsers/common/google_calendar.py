import re

from itertools              import groupby
from gdata.calendar.service import CalendarService, CalendarEventQuery
from datetime               import datetime, timedelta
from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

class GoogleCalendarParser(ShowParser):
  BASE_URL     = "http://myspace.com/%(profile_id)s"
  IS_EVENT     = re.compile("http://events.myspace.com/Event/\d+")
  
  def __init__(self, *args, **kwargs):
    super(GoogleCalendarParser, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    calendar_service = CalendarService()

    yesterday    = datetime.today() - timedelta(days = 1)
    three_months = yesterday + timedelta(days = 90)

    query = CalendarEventQuery(self.calendar_id(), 'public', 'full')

    query.start_min      = yesterday.strftime('%F')
    query.start_max      = three_months.strftime('%F')
    
    query['max-results'] = '500'

    feed = calendar_service.CalendarQuery(query)
    
    start_date = lambda e: date_util.parse_date_time(e.when[0].start_time).date()
    
    single    = []
    recurring = []
    
    for e in feed.entry:
      if len(e.when) > 1:
        recurring.append(e)
      else:
        single.append(e)
        
    for show in self._process_recurring_entries(recurring):
      if show:
        yield show

    if self.group_by_date():
      single.sort(key = start_date)

      for batch_date, date_entries in groupby(single, start_date):
        for show in self._process_entry_group(batch_date, list(date_entries)):
          if show:
            pass
          
          yield show 
    else:
      for entry in single:
        show = self._process_entry(entry)

        if show:
          yield show

          
  def _process_recurring_entries(self, entries):
    raise NotImplementedError()

  def _process_entry_group(self, start_date, feeds):
    raise NotImplementedError()
    
  def _process_entry(self, feed):
    raise NotImplementedError()

  @classmethod
  def calendar_id(cls):
    raise NotImplementedError()

  @classmethod
  def group_by_date(cls):
    return False