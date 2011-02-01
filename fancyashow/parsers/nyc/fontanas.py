import logging
import urllib2
import lxml.html
import re
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class Fontanas(ShowParser):
  BASE_URL     = "http://fontanasnyc.com/"
  CALENDAR_URL = "http://fontanasnyc.com/shows.html"
  IMAGE_RE     = re.compile('/images/bands/')
  # We don't care about the day of the week (which is first, just nab the month and date)
  DATE_RE      = re.compile('\w+\s+(?P<date>\w+\s+\d+)')
  PERFORMER_RE = re.compile('%s (?P<performer>.*)' % date_util.STRICT_TIME_MATCH)

  def __init__(self, *args, **kwargs):
    super(Fontanas, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parse_started = datetime.now()
      self._parser        = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    doc = html_util.fetch_and_parse(self.CALENDAR_URL)
    
    main_section = None
    
    for tr in doc.iter(tag = 'tr'):
      tds = tr.getchildren()
      
      if len(tds) != 2:
        continue
        
      match = self.DATE_RE.search(tds[0].text_content())
      
      if match:
        show =  self._parse_show(match.group('date'), tds[1])

        if show:
          yield show

  def _parse_show(self, date_txt, info_el):
    logger.debug('Parsing show in %s' % date_txt)

    info_txt = html_util.get_displayed_text_content(info_el)
    
    performers    = []
    show_time_txt = None
    
    for line in info_txt.split('\n'):
      match = self.PERFORMER_RE.match(line)
      
      if match:
        time_txt, name = match.group('time'), match.group('performer')
        
        show_time_txt = time_txt
        
        performers.append(Performer(name, start_time = time_txt))
    
    if len(performers) == 0:
      return None

    show = Show()

    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_date_and_time(date_txt, show_time_txt)

    show.resources.resource_uris = self.resource_extractor.extract_resources(info_el)
    
    # Fontanas's stores the large image in an anchor tag
    for a in info_el.iter(tag = 'a'):
      if self.IMAGE_RE.search(a.get('href', '')):
        show.resources.image_url = a.get('href')

    date_util.adjust_fuzzy_years(show, self._parse_started)

    return show

  def venue(self):
    return Venue('Fontanas', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.manhattan.fontanas'

extensions.register_show_parser(Fontanas)
