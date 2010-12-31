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

extensions = ExtensionLibrary()

class Europa(ShowParser):
  BASE_URL     = "http://www.europalive.net/"
  CALENDAR_URL = "http://www.europalive.net/calendar.html"
  IMAGE_RE     = re.compile('/images/band_images/')

  def __init__(self, *args, **kwargs):
    super(Europa, self).__init__(*args, **kwargs)
    
    self._parser    = None
    
  def next(self):
    if not self._parser:
      self._parse_started = datetime.now()
      self._parser        = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    calendar_file = urllib2.urlopen(self.CALENDAR_URL)
    
    calendar = ''
    
    for data in calendar_file:
      calendar += data
    
    # Europa has an errant closing html tag at the top of the document that messes up lxml
    calendar = calendar.replace('</html>', '')
    
    doc = lxml.html.document_fromstring(calendar)

    doc.make_links_absolute(self.CALENDAR_URL)
    
    main_section = None
    
    for el in doc.iter(tag = 'table'):
      if el.get('width') == '756':
        main_section = el
        
        break
        
    if main_section is None:
      raise Exception('Unable to find main section')
    
    for el in html_util.get_elements(main_section, 'table'):
      if el.get('width') == '700' and el.get('height') == '80':
        show =  self._parse_show(el)
      
        if show:
          yield show

  def _parse_show(self, el):
    date_el = html_util.get_first_element(el, '.calendardates')
    
    for span in date_el.iter(tag = 'span'):
      if span.get('class') == 'small':
        span.getparent().remove(span)
    
    date_txt = date_el.text_content().lower()
    
    # Skip recurring events
    if 'every' in date_txt:
      return None
      
    date_txt, time_txt = date_txt.split(',')
    
    performers = [] 
    
    title_el = html_util.get_first_element(el, '.calendar')

    for name in title_el.text_content().split('/'):
      performers.append(Performer(name))

    show = Show()

    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_date_and_time(date_txt, time_txt)

    show.resources.resource_uris = self.resource_extractor.extract_resources(el)
    
    for img in el.iter(tag = 'img'):
      logging.debug('image: %s - %s' % (img.get('src'), self.IMAGE_RE.search(img.get('src', ''))))
      if self.IMAGE_RE.search(img.get('src', '')):
        show.resources.image_url = img.get('src')
        
    date_util.adjust_fuzzy_years(show, self._parse_started)

    return show

  def _parse_performer(self, h):
    return Performer(h.text_content(), headliner = h.tag in ('h1', 'h2'))

  def venue(self):
    return Venue('Europa', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.europa'

extensions.register_show_parser(Europa)