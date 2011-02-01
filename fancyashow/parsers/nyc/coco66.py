import logging
from datetime                     import datetime
import urlparse
import re
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions  = ExtensionLibrary()

class Coco66(ShowParser):
  BASE_URL     = "http://www.coco66.com/"
  MONTH_FORMAT = 'http://coco66.com/?page=calendar&month=%(month)s&year=%(year)s'
  IS_EVENT     = re.compile("http://(?:www.)?coco66.com/\?page=event&id=\d+")
  EVENT_ID     = re.compile('id=(\d+)')
  # Allows for 2009-09-01, Monday, October 11th, 2010, or Tonight
  HEADER_PARSE = re.compile('(?P<date>(?:\d+-\d+-\d+)|(?:\w+\s+\d+/\d+)|(\w+,\s+\w+\s+\d+\w+,\s+\d+)|(?:tonight))\s*-\s*(?P<title>.*)', re.I)
  MONTHS_AHEAD = 3
  
  def __init__(self, *args, **kwargs):
    super(Coco66, self).__init__(*args, **kwargs)
    
    self._current_parser = None
    self._date_queue     = self._request_dates()
    self._parsed_dates   = { }
    
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
        year  += 1

      ret.append(start.replace(month = month, year = year))
      
    return ret
    
  def raw_url(self, url):
    url = urlparse.urlparse(url)
    
    if url.fragment:
      url = urlparse.ParseResult(scheme = url.scheme, netloc = url.netloc, path = url.fragment, params = '', query = '', fragment = '')
      
    url = url.geturl()
    
    if not url.endswith('/'):
      url = url + '/'

    if not url.endswith('Raw'):
      url = url + 'Raw'
      
    return url

  def _month_parser(self, request_date):
    month_url = self.MONTH_FORMAT % {'year': request_date.year, 'month': request_date.month}
    
    logging.debug('Parsing shows from: %s' % month_url)

    for show_url in html_util.get_show_urls(month_url, 'body', None, self.IS_EVENT):
      yield self._parse_show(show_url)
          
  def _parse_show(self, link):
    raw_url   = self.raw_url(link)
    
    match     = self.EVENT_ID.search(link)
    
    if not match:
      raise Exception("Unable to locate event id in: %s" % link)
      
    event_id = match.group(0)
    
    logging.debug('Fetching show info: %s' % link)

    event_doc = html_util.fetch_and_parse(link)
    
    show_el   = html_util.get_first_element(event_doc, '#content')

    header_el = html_util.get_first_element(show_el, 'h1')
    
    header_match = self.HEADER_PARSE.search(header_el.text_content())
    
    if not header_match:
      raise Exception("Unable to parse header: %s" % header_el.text_content())
      
    date_txt = header_match.group('date').strip()
    title    = header_match.group('title').strip()
    
    if date_txt.lower().startswith('tonight'):
      date_txt = datetime.today().date().strftime('%F')

    img   = html_util.get_first_element(show_el, 'img', optional = True)

    show = Show()
    
    show.performers = [Performer(p) for p in lang_util.parse_performers(title)]
    show.show_time  = date_util.parse_date_and_time(date_txt, None)

    show.merge_key = event_id
    show.venue     = self.venue()
  
    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(show_el)
    
    if img is not None:
      show.resources.image_url = img.get('src')
      
    return show
    
  def venue(self):
    return Venue('Coco 66', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.coco-66'

extensions.register_show_parser(Coco66)
