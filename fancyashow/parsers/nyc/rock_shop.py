# encoding=UTF-8
import logging
import lxml.html
import re
from lxml.html.clean              import Cleaner
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class RockShop(ShowParser):
  BASE_URL      = "http://www.therockshopny.com/"
  SHOW_PART_SEP = u'•'
  SHOW_START_RE = re.compile(u'\s*\w+\s*,\s*\w+\s+\d+\s*•')
  
  def __init__(self, *args, **kwargs):
    super(RockShop, self).__init__(*args, **kwargs)
    
    self._parser    = None

  def next(self):
    if not self._parser:
      self._parse_started = datetime.now()
      self._parser        = self._get_parser()
      
    while(True):
      return self._parser.next()
      
    raise StopIteration

  def _get_parser(self):    
    doc     = html_util.fetch_and_parse(self.BASE_URL)

    events  = html_util.get_first_element(doc, '.defaultText')
    content = html_util.get_displayed_text_content(events).strip()

    for line in content.split('\n'):
      if self.SHOW_START_RE.match(line):
        show = self._parse_show(line)
        
        if show:
          yield show
          
  def _parse_show(self, show_txt):
    parts = show_txt.split(self.SHOW_PART_SEP)
    
    date_txt, time_txt = parts[0], parts[1]
    performers         = parts[-1]

    show = Show()

    show.show_time = date_util.parse_date_and_time(date_txt, time_txt)
    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers(performers)]

    date_util.adjust_fuzzy_years(show, self._parse_started)

    return show

  def venue(self):
    return Venue('Rock Shop', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.rock-shop'

extensions.register_show_parser(RockShop)