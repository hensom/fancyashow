import logging
import re
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

from fancyashow.parsers.common.myspace import MyspaceParser

LOG = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class Zebulon(ShowParser):
  BASE_URL     = "http://www.zebuloncafeconcert.com/"
  MONTH_URL    = "http://www.zebuloncafeconcert.com/index.php?EC_action=switchMonthLarge&EC_month=%(month)s&EC_year=%(year)s"
  EVENT_URL    = re.compile("http://(?:www\.)?zebuloncafeconcert.com/?\?p=(?P<page_id>\d+)")
  MONTHS_AHEAD = 3
  
  def __init__(self, *args, **kwargs):
    super(Zebulon, self).__init__(*args, **kwargs)
    
    self._current_parser = None
    self._date_queue     = self._request_dates()
    
  def _next_parser(self):
    if self._date_queue:
      return self._month_parser(self._date_queue.pop(0))
      
    return None
  
  def next(self):
    if not self._current_parser:
      self._current_parser = self._next_parser()
      
    while(self._current_parser):
      try:
        return self._current_parser.next()
      except StopIteration:
        self._current_parser = self._next_parser()
    
    raise StopIteration

  def _request_dates(self):
    ret   = [ ]
    start = datetime.today().date().replace(day = 1)

    for i in xrange(self.MONTHS_AHEAD):
      month = start.month + i
      year  = start.year

      if month > 12:
        month = month - 12
        year  = year + 1

      ret.append(start.replace(month = month, year = year))
      
    return ret

  def _month_parser(self, request_date):
    month_url = self.MONTH_URL % {'year': request_date.year, 'month': request_date.month}
    
    LOG.debug('Parsing shows from: %s' % month_url)
    
    doc = html_util.fetch_and_parse(month_url)
    
    for script in doc.iter(tag = 'script'):
      for match in self.EVENT_URL.finditer(script.text_content()):
        yield self._parse_show(match.group(0))
          
  def _parse_show(self, link):
    LOG.debug("Fetching show: %s" % link)

    event_doc    = html_util.fetch_and_parse(link)

    event_detail = event_doc.get_element_by_id("mainColumn")

    show = Show()
    
    for performer in html_util.get_elements(event_detail, 'h1'):
      name = performer.text_content().strip(' \n\r\t')
      if name:
        show.performers.append(Performer(name))
      
    date_txt = html_util.get_first_element(event_detail, '.date').text_content()
    
    event_match = self.EVENT_URL.match(link)

    show.merge_key = event_match.group('page_id')
    show.venue     = self.venue()
    show.show_time = date_util.parse_date_time(date_txt).replace(hour = 21)
    
    LOG.debug('Date: %s' % show.date)
    
    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    for img_tag in event_detail.iter(tag = 'img'):
      if 'main' in img_tag.get('src'):
        show.resources.image_url = img_tag.get('src')
        
        break

    return show

  def venue(self):
    return Venue('Zebulon', 'http://www.myspace.com/zebuloncafeconcert')

  @classmethod
  def id(self):
    return 'us.ny.brooklyn.zebulon'

extensions.register_show_parser(Zebulon)