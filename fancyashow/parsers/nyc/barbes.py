# encoding=UTF-8
import logging
import re
from datetime                     import datetime, timedelta
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

logger = logging.getLogger(__name__)

class Barbes(ShowParser):
  BASE_URL     = "http://www.barbesbrooklyn.com/"
  CALENDAR_URL = "http://www.barbesbrooklyn.com/calendar.html"
  DATE_RE      = re.compile("\w+ (?P<month>\d+)/(?P<day>\d+)")
  
  def __init__(self, *args, **kwargs):
    super(Barbes, self).__init__(*args, **kwargs)
    
    self._parser = None
  
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    today = datetime.today().date()

    doc     = html_util.fetch_and_parse(self.CALENDAR_URL)
    
    by_date = { }
    
    for tr in doc.iter(tag = 'tr'):
      tds = list(tr.iter(tag = 'td'))
      
      date_txt = tds[0].text_content().strip()
      
      logger.debug('Checking if td el is a show: %s' % date_txt)
      
      if self.DATE_RE.match(date_txt):
        show = self._parse_show(tds)
        
        show_date = show[0].date()
        
        if show_date not in by_date:
          by_date[show_date] = []

        by_date[show_date].append(show)
          
    for date, performers in by_date.iteritems():
      performers.sort(lambda x,y: cmp(y[0], x[0]))
      
      show = Show()

      show.venue      = self.venue()
      show.performers = []
      
      all_resources   = []
      
      for time, name, resources in performers:
        all_resources.extend(resources)
        
        if not show.show_time:
          show.show_time = time
        else:
          show.show_time = min(show.show_time, time)

        show.performers.append(Performer(name, start_time = time.strftime('%I:%M')))

      show.resources.resource_uris = list(set(all_resources))
      
      yield show

  def _parse_show(self, tds):
    date, info, time = tds[0], tds[1], tds[2]
    
    date_txt = date.text_content()
    
    time_match = date_util.STRICT_TIME_RE.search(time.text_content())
    
    if time_match:
      time_txt = time_match.group('time')
    else:
      raise Exception('Unable to determine time for show: %s - %s - %s' % (date_txt, time.text_content(), info.text_content()))
      
    performers = []

    for el in info.iter(tag = 'a'):
      performers.append(el.text_content())

    show_time     = date_util.parse_date_and_time(date_txt, time_txt)
    resource_uris = self.resource_extractor.extract_resources(*tds)
      
    return (show_time, ' '.join(performers), resource_uris)

  def venue(self):
    return Venue('Barbes', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.barbes'

extensions.register_show_parser(Barbes)