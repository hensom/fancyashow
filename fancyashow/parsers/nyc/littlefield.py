import re
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class Littlefield(ShowParser):
  BASE_URL     = "http://www.littlefieldnyc.com/"
  CALENDAR_URL = "http://www.littlefieldnyc.com/upcoming-events/"
  IS_EVENT     = re.compile("http://www.littlefieldnyc.com/event-detail/\?id=\d+")

  def __init__(self, *args, **kwargs):
    super(Littlefield, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    show_urls = html_util.get_show_urls(self.CALENDAR_URL, "ul#events-list", {'tag': 'li'}, self.IS_EVENT, parse_500 = True)
    
    for url in show_urls:
      try:
        yield self._parse_show(url)
      except Exception, e:
        raise ParserError(url, None, e)

  def _parse_show(self, link):
    event_doc = html_util.fetch_and_parse(link, parse_500 = True)

    event_detail = html_util.get_first_element(event_doc,    ".event-details")
    event_vitals = html_util.get_first_element(event_detail, ".event-vitals")
    artist_info  = html_util.get_first_element(event_doc,    ".artist-section")
    
    date_txt     = html_util.get_first_element(event_vitals, ".date").text_content()
    
    performers = [] 
    
    for tag in ('h2', 'h3'):
      performers.extend([self._parse_performer(h) for h in event_vitals.iter(tag = tag)])

    show = Show()

    show.merge_key  = link
    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_show_time(date_txt, html_util.get_first_element(event_vitals,  ".time").text_content())
    show.door_time  = date_util.parse_door_time(date_txt, html_util.get_first_element(event_vitals,  ".time").text_content())

    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_vitals, event_detail, artist_info)

    img = html_util.get_first_element(event_detail, ".event-image img", optional = True)
    
    if img is not None:
      show.resources.image_url = img.get('src')

    return show
    
  def _parse_performer(self, h):
    return Performer(h.text_content(), headliner = h.tag == 'h2')

  def venue(self):
    return Venue('Littlefield', self.BASE_URL)

  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.littlefield'

extensions.register_show_parser(Littlefield)