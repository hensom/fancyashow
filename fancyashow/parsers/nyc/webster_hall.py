# encoding=UTF-8
import logging
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util
import re

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

N = 0

class WebsterHall(ShowParser):
  BASE_URL     = "http://www.websterhall.com/"
  CALENDAR_URL = "http://www.websterhall.com/events/"
  EVENT_URL    = 'http://websterhall.com/events/show_event_sub.php?id=%(event_id)s&size=large&cdate=%(cdate)s'
  IS_EVENT     = re.compile('javascript:\s*list_post\s*\(\s*"(?P<event_id>.*?)"\s*,\s*"(?:.*)"\s*,\s*"(?P<cdate>.*)"\s*\)', re.I)
  INFO_LINE    = re.compile('^\s*(Date|Age|Ticket)', re.I)

  def __init__(self, *args, **kwargs):
    super(WebsterHall, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    show_urls = html_util.get_show_urls(self.CALENDAR_URL, 'form[name="event_list"]', 'td.day', self.IS_EVENT)
    
    for url in show_urls:
      show = self._parse_show(url)
      
      if show:
        yield show

  def _parse_show(self, js_link):
    global N
    match = self.IS_EVENT.match(js_link)
    
    event_id = match.group('event_id')
    
    link     = self.EVENT_URL % {'event_id': event_id, 'cdate': match.group('cdate')}
    
    logger.debug('Fetching show: %s' % link)

    event_doc = html_util.fetch_and_parse(link)
    
    content   = html_util.get_displayed_text_content(event_doc).strip()

    # General format of the displayed content is:
    """
    Sunday, October 10, 2010 - 7:00 PM 

    Chris Webby, Hoodie Allen, Matt Clark 

    DATE : October 10, 2010 
    DOOR : 7:00 PM 
    AGE : 16+ 
    TICKETS :  $13 in advance, $15 at the door 
    """
    
    date_txt, time_txt = None, None
    collect_performers = True
    performers         = []

    for line in content.split('\n'):
      if line:
        if not date_txt:
          date_txt, time_txt = line.split('-')
        elif self.INFO_LINE.match(line):
          collect_performers = False
        elif collect_performers:
          performers.extend([Performer(name) for name in lang_util.parse_performers(line)])

    show = Show()

    show.venue               = self.venue()
    show.performers          = performers
    show.door_time           = date_util.parse_date_and_time(date_txt, time_txt)
    show.merge_key           = event_id
    show.resources.show_link = link
    
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_doc)

    found = False

    for div in event_doc.iter(tag = 'div'):
      if found:
        break

      if div.get('align') == 'left':
        for img in div.iter(tag = 'img'):
          show.resources.image_url = img.get('src')
          
          found = True

          break

    return show
    
  def _parse_performer(self, h):
    return Performer(h.text_content(), headliner = h.tag == 'h2')

  def venue(self):
    return Venue('Webster Hall', self.BASE_URL)

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.webster-hall'

extensions.register_show_parser(WebsterHall)