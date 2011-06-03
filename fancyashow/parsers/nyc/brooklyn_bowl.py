import re
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class BrooklynBowl(ShowParser):
  BASE_URL     = "http://www.brooklynbowl.com/"
  CALENDAR_URL = "http://www.brooklynbowl.com/calendar/"
  IS_EVENT     = re.compile("http://www.brooklynbowl.com/event/(?P<event_id>\d+)")

  def __init__(self, *args, **kwargs):
    super(BrooklynBowl, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    show_urls = html_util.get_show_urls(self.CALENDAR_URL, ".list-view", '.list-view-item', self.IS_EVENT)
    
    for url in show_urls:
      yield self._parse_show(url)

  def _parse_show(self, link):
    event_doc = html_util.fetch_and_parse(link)
    match     = self.IS_EVENT.match(link)

    event_id      = int(match.group('event_id'))
    event_detail  = html_util.get_first_element(event_doc, ".tfly-event-id-%d" % event_id)
    
    date_txt     = html_util.get_first_element(event_doc, ".dates").text_content()
    time_txt     = html_util.get_first_element(event_doc, ".times").text_content()

    img          = html_util.get_first_element(event_detail, "img")
    
    performers = [] 
    
    for p in html_util.get_elements(event_detail, '.headliners'):
      performers.append(Performer(p.text_content(), headliner = True))
      
    for p in html_util.get_elements(event_detail, '.supports'):
      for pi in lang_util.parse_performers(p.text_content()):
        performers.append(Performer(pi, headliner = False))

    show = Show()

    show.merge_key  = link
    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_show_time(date_txt, time_txt)
    show.door_time  = date_util.parse_door_time(date_txt, time_txt)

    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)
    
    if img is not None:
      show.resources.image_url  = img.get('src')

    return show

  def venue(self):
    return Venue('Brooklyn Bowl', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.brooklyn-bowl'

extensions.register_show_parser(BrooklynBowl)
