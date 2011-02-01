import logging
import re
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class KnittingFactory(ShowParser):
  BASE_URL     = "http://bk.knittingfactory.com/"
  CALENDAR_URL = "http://bk.knittingfactory.com/calendar/"
  IS_EVENT     = re.compile("http://bk.knittingfactory.com/event-details/\?tfly_event_id=\d+")

  def __init__(self, *args, **kwargs):
    super(KnittingFactory, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    show_urls = html_util.get_show_urls(self.CALENDAR_URL, ".tfly-calendar", 'td', self.IS_EVENT)
    
    for url in show_urls:
      yield self._parse_show(url)

  def _parse_show(self, link):
    event_doc = html_util.fetch_and_parse(link)

    event        = html_util.get_first_element(event_doc, '#tfly-center-column-wide')
    event_detail = html_util.get_first_element(event,     '#details')
    """
    <div class="info"> 
      Sat, May 22, 2010<br /> 
      Doors: 6:00 PM / Show: 7:00 PM&nbsp;<br /> 
      $5.00<br /> 
    </div> 
    """
    event_info   = html_util.get_first_element(event_detail, ".info")

    date_txt     = event_info.text
    time_txt     = event_info.getchildren()[0].tail

    img          = html_util.get_first_element(event_detail, "img")
    
    performers = [] 

    for tag in ('h1', 'h2', 'h3', 'h4'):
      for h in event_detail.iter(tag = tag):
        performers.extend(self._parse_performers(h))

    show = Show()

    show.merge_key  = link
    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_show_time(date_txt, time_txt)
    show.door_time  = date_util.parse_door_time(date_txt, time_txt)

    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event)
    
    if img is not None:
      show.resources.image_url  = img.get('src')

    return show

  def _parse_performers(self, h):
    ret = []

    for name in lang_util.parse_performers(h.text_content()):
      ret.append(Performer(name, headliner = h.tag in ('h1', 'h2')))
      
    return ret

  def venue(self):
    return Venue('Knitting Factory', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.knitting-factory'

extensions.register_show_parser(KnittingFactory)
