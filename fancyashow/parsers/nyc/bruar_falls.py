import logging
import lxml.html
import re
from lxml.html.clean              import Cleaner
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class BruarFalls(ShowParser):
  BASE_URL = "http://www.bruarfalls.com/"
  NUM_RE   = re.compile('^\s*\d+\s*(?:st|nd|rd|th):\s*', re.IGNORECASE | re.MULTILINE)
  
  def __init__(self, *args, **kwargs):
    super(BruarFalls, self).__init__(*args, **kwargs)
    
    self._parser = None
  
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()
      
    while(True):
      return self._parser.next()
      
    raise StopIteration

  def _get_parser(self):    
    doc   = html_util.fetch_and_parse(self.BASE_URL)
    
    for event_detail in doc.cssselect(".shows .dates"):
      yield self._parse_show(event_detail)
        
  def _parse_show(self, event_detail):
    show = Show()
    
    performers = []
    
    content  = html_util.get_displayed_text_content(event_detail).strip()
    date_txt = None

    # This flag is set up and down to allow either of the following to be processed:
    # 1st: Ava Luna
    # or
    # 1st:
    # Ava Luna
    had_num  = True
    
    logger.debug("Parsing show content: %s" % content)
    
    for line in content.split('\n'):
      if line:
        time_match = date_util.STRICT_TIME_RE.search(line)

        if not date_txt:
          date_txt = line
        elif time_match:
          show.show_time = date_util.parse_date_and_time(date_txt, time_match.group('time'))
          
          line = date_util.STRICT_TIME_RE.sub('', line).strip(': ')
          
          if line:
            performers.append(Performer(line))

            had_num = False
          else:
            had_num = True
        elif self.NUM_RE.match(line):
          line = self.NUM_RE.sub('', line).strip()
          
          if line:
            performers.append(Performer(line))

            had_num = False
          else:
            had_num = True
        elif had_num:
          performers.append(Performer(line))
          had_num = False
        else:
          logger.error('Unknown line format: %s' % line)
            
    show.venue      = self.venue()
    show.performers = performers
    show.date       = date_util.parse_date_and_time(date_txt, None)
    
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    for img_tag in event_detail.iter(tag = 'img'):
      show.resources.image_url = img_tag.get('src')
      
      break

    return show

  def venue(self):
    return Venue('Bruar Falls', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.bruar-falls'

extensions.register_show_parser(BruarFalls)