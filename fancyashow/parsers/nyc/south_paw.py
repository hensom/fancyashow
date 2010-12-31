import re
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class Southpaw(ShowParser):
  BASE_URL     = "http://spsounds.com/"
  CALENDAR_URL = "http://spsounds.com/calendar/"
  IS_EVENT     = re.compile("http://www.santospartyhouse.com/index/event/id/\d+")

  def __init__(self, *args, **kwargs):
    super(Southpaw, self).__init__(*args, **kwargs)
    
    self._parser    = None
    
  def next(self):
    if not self._parser:
      self._parse_started = datetime.now()
      self._parser        = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    doc = html_util.fetch_and_parse(self.CALENDAR_URL)
    
    for el in doc.cssselect('#event-posts .post'):
      yield self._parse_show(el)

  def _parse_show(self, el):    
    event_detail = html_util.get_first_element(el, '.event-details')

    date_txt     = html_util.get_first_element(event_detail, 'strong').text
    time_txt     = event_detail.text_content()

    show = Show()

    show.venue      = self.venue()
    
    title_txt       = html_util.get_first_element(event_detail, '.event-name').text_content()
    show.performers = [Performer(p) for p in lang_util.parse_performers(title_txt)]
    show.show_time  = date_util.parse_show_time(date_txt, time_txt)
    show.door_time  = date_util.parse_door_time(date_txt, time_txt)
    
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    img = html_util.get_first_element(el, ".event-image img", optional = True)
    
    if img is not None:
      show.resources.image_url = img.get('src')
      
    date_util.adjust_fuzzy_years(show, self._parse_started)

    return show

  def venue(self):
    return Venue('Southpaw', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.southpaw'
    
extensions.register_show_parser(Southpaw)