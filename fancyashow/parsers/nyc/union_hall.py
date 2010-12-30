import re
import logging
from datetime                     import datetime, timedelta
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

logger = logging.getLogger(__name__)

class UnionHall(ShowParser):
  BASE_URL     = "http://www.unionhallny.com/"
  CALENDAR_URL = "http://www.unionhallny.com/calendar.php"
  DATE_RE      = re.compile("\w+ (?P<month>\d+)/(?P<day>\d+):")
  TIME_RE      = re.compile(':\s+(?P<time>\d+(?:\s*:\s*\d+)?\s*[ap]\.?m\.?)\s*', re.IGNORECASE)
  
  def __init__(self, *args, **kwargs):
    super(UnionHall, self).__init__(*args, **kwargs)
    
    self._parser    = None
    self.prev_month = None
    self.year       = datetime.now().year
  
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()
      
    while(True):
      return self._parser.next()
      
    raise StopIteration

  def _get_parser(self):
    today = datetime.today().date()
    
    doc   = html_util.fetch_and_parse(self.CALENDAR_URL)
    
    main_section = doc.get_element_by_id("col-main")
    
    for event_detail in main_section.cssselect("#unionhall"):
      yield self._parse_show(self.CALENDAR_URL, event_detail, today)
        
  def _parse_show(self, show_url, event_detail, today):
    show = Show()

    # Union hall will have duplicate instances of #unionhall_performer
    # some may or may not have links, but those that do have links are tagged
    # with the same id again ie: <div id="unionhall_performer"><a href="#" id="#unionhall_performer"> ...
    performers = [Performer(p.text_content()) for p in event_detail.cssselect("#unionhall_performer") if p.tag != 'a']

    performers[0].headliner = True
    
    ticket_link = html_util.get_first_element(event_detail, '#ticket_link a', optional = True)

    show.venue      = self.venue()
    show.performers = performers

    if ticket_link is not None:
      show.merge_key = ticket_link.get('href')

    # Format: THU 3/25: 6pm / $15      
    date_tag   = event_detail.get_element_by_id("unionhall_date")
    
    date_match = self.DATE_RE.match(date_tag.text_content())
    time_match = self.TIME_RE.search(date_tag.text_content())
    
    if date_match and time_match:
      month, day = (int(d) for d in (date_match.group('month'), date_match.group('day')))
      
      # Handle cases where we pass from one year to the next
      logger.debug('Testing for year boundary: last month: %s, current month: %s' % (self.prev_month, month))

      if self.prev_month > month:
        logger.debug('Increasing date by one year to account for passing the boundary')
        self.year += 1
        
      self.prev_month = month
      
      show_date = datetime(month = month, day = day, year = self.year)
      
      show.show_time = date_util.parse_date_and_time(show_date.strftime('%F'), time_match.group('time'))

    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    for img_tag in event_detail.iter(tag = 'img'):
      show.resources.image_url = img_tag.get('src')
      
      break
      
    return show

  def venue(self):
    return Venue('Union Hall', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.union-hall'

extensions.register_show_parser(UnionHall)