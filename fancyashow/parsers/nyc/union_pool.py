from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class UnionPool(ShowParser):
  BASE_URL     = "http://unionpool.blogspot.com/"
  
  def __init__(self, *args, **kwargs):
    super(UnionPool, self).__init__(*args, **kwargs)
    
    self._parser    = None
  
  def next(self):
    if not self._parser:
      self._parse_started = datetime.now()
      self._parser        = self._get_parser()
      
    while(True):
      return self._parser.next()
      
    raise StopIteration

  def _get_parser(self):    
    doc   = html_util.fetch_and_parse(self.BASE_URL)
    
    sidebar = doc.get_element_by_id("sidebar-right-1")
    
    for event_detail in sidebar.cssselect("div.widget.Image"):
      show = self._parse_show(event_detail)

      if show:
        yield show
        
  def _parse_show(self, event_detail):
    if html_util.get_first_element(event_detail, 'h2', optional = True) is None:
      return None

    show = Show()

    date_txt       = html_util.get_first_element(event_detail, 'h2').text_content()
    performers_txt = html_util.get_first_element(event_detail, '.caption').text_content()

    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers(performers_txt)]
    
    if not date_txt.lower().startswith('every'):
      show.date = date_util.parse_date_and_time(date_txt, None)

    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    for img_tag in event_detail.iter(tag = 'img'):
      show.resources.image_url = img_tag.get('src')
      
      break
      
    date_util.adjust_fuzzy_years(show, self._parse_started)
      
    return show

  def venue(self):
    return Venue('Union Pool', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.union-pool'

extensions.register_show_parser(UnionPool)
