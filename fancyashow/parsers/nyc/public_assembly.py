import logging
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util
import re

extensions = ExtensionLibrary()

class PublicAssembly(ShowParser):
  BASE_URL     = "http://www.publicassemblynyc.com/"
  IS_EVENT     = re.compile("http://www.publicassemblynyc.com/events/view/(\d+)")
  TIME_RE      = re.compile("Room\s*,\s*(?P<time>\d.*?[ap]m)")
  MONTHS_AHEAD = 3
  
  def __init__(self, *args, **kwargs):
    super(PublicAssembly, self).__init__(*args, **kwargs)
    
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
    month_url = '%sevents/month/%d/%d' % (self.BASE_URL, request_date.year, request_date.month)
    
    logging.debug('Parsing shows from: %s' % month_url)

    for show_url in html_util.get_show_urls(month_url, "#content", None, self.IS_EVENT):
      try:
        yield self._parse_show(show_url)
      except UnicodeDecodeError, e:
        logging.exception('Unable to parse show: %s, skipping' % show_url)
        
        continue
      except Exception, e:
        raise ParserError(show_url, None, e)
          
  def _parse_show(self, link):
    event_doc    = html_util.fetch_and_parse(link)

    event_detail = event_doc.get_element_by_id("detail")

    show = Show()

    strong_iter = event_detail.iter(tag = 'strong')

    date_tag, title_tag, blank_tag, desc_tag = strong_iter.next(), strong_iter.next(), strong_iter.next(), strong_iter.next()
    
    date_txt = date_tag.text_content()
    
    if desc_tag.getnext().tail:
      time_match = self.TIME_RE.search(desc_tag.getnext().tail)
    else:
      time_match = None
    
    if time_match:
      time_txt = time_match.group('time')
    else:
      time_txt = None

    show.merge_key = link
    show.venue     = self.venue()
    show.title     = title_tag.text_content()
    show.show_time = date_util.parse_date_and_time(date_txt, time_txt)
    
    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    for img_tag in event_detail.iter(tag = 'img'):
      if 'main' in img_tag.get('src'):
        show.resources.image_url = img_tag.get('src')
        
        break

    return show
    
  def venue(self):
    return Venue('Public Assembly', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.public-assembly'

extensions.register_show_parser(PublicAssembly)