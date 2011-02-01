# coding=UTF-8
import logging
import re
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class Pianos(ShowParser):
  BASE_URL      = "http://www.pianosnyc.com/"
  CALENDAR_URLS = ['http://www.pianosnyc.com/showroom', 'http://www.pianosnyc.com/upstairs']
  IS_EVENT      = re.compile("http://www.pianosnyc.com/(upstairs|showroom)/[^/]+-\d+")
  DATE_RE       = re.compile('(\w+,\s+\w+\s+\d+,\s+\d+)')

  def __init__(self, *args, **kwargs):
    super(Pianos, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    for cal_url in self.CALENDAR_URLS:
      show_urls = html_util.get_show_urls(cal_url, "#longlist", '.details', self.IS_EVENT)
    
      for url in show_urls:
        yield self._parse_show(url)

  def _parse_show(self, link):
    logging.debug('Parsing show from: %s' % link)

    event_doc = html_util.fetch_and_parse(link)

    event        = html_util.get_first_element(event_doc, '.biglisting')
    img          = html_util.get_first_element(event, '.tonightinfo img', optional = True)

    date_el     = html_util.get_first_element(event, '.date')
    
    date_match  = self.DATE_RE.search(date_el.text_content())
    
    if date_match:
      date_txt = date_match.group(0)
    else:
      raise Exception('Unable to determine show date from: %s' % date_el.text_content())
    
    performers = [] 
    first_time = None

    for det in event.cssselect('.showpage-details'):
      header = None
      
      for child in det.getchildren():
        if child.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
          header = child
          
      if header is None:
        logger.error('Unable to determine performer')
      else:
        time_txt = html_util.get_first_element(det, '.time').text_content()
      
        time_match = date_util.TIME_RE.search(time_txt)
      
        if time_match:
          first_time = time_txt = time_match.group('time')
        else:
          time_txt = None

        performers.append(Performer(header.text_content(), start_time = time_txt, headliner = header.tag in ('h1')))

    show = Show()

    show.merge_key  = link
    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_date_and_time(date_txt, first_time)

    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event)
    
    if img is not None:
      show.resources.image_url  = img.get('src')

    return show

  def venue(self):
    return Venue('Pianos', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.manhattan.pianos'

extensions.register_show_parser(Pianos)
