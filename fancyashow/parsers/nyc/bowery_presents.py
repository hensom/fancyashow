import logging
import urlparse
import re

from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class BoweryPresentsBase(ShowParser):
  BASE_URL     = "http://www.brooklynbowl.com/"
  CALENDAR_URL = "http://www.brooklynbowl.com/upcoming-events/"
  IMAGE_RE     = re.compile('background-image:\s*url\((?P<image_path>.+)\)')

  def __init__(self, *args, **kwargs):
    super(BoweryPresentsBase, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration
    
  def _get_parser(self):
    show_urls = html_util.get_show_urls_and_section(self.show_list_url(), '.list-view', '.list-view-item', self.event_url_re())

    for url, show_section in show_urls.iteritems():
      yield self._parse_show(url, show_section)

  def _parse_show(self, link, show_section):
    show_doc    = html_util.fetch_and_parse(link)

    show_detail = html_util.get_first_element(show_doc, "#content .event-detail")

    date_txt    = html_util.get_first_element(show_detail, ".dates").text_content()
    time_txt    = html_util.get_first_element(show_detail, ".times").text_content()
    sold_out    = html_util.get_first_element(show_detail,  '.sold-out', optional = True)
    image       = html_util.get_first_element(show_detail,  'img',       optional = True)
    
    # The image we want is generally the first one, but if the layout changes this may break
    if image is not None:
      image_url = image.get('src')
    else:
      image_url = None
    
    performers = [] 
    
    for tag in ('h1', 'h2', 'h3'):
      for p in show_detail.iter(tag = tag):
        if p.text_content():    
          performers.extend(self._parse_performers(p))

    show = Show()

    show.merge_key               = link
    show.venue                   = self.venue()
    show.performers              = performers
    show.door_time               = date_util.parse_door_time(date_txt, time_txt)
    show.show_time               = date_util.parse_show_time(date_txt, time_txt)
    show.soldout                 = sold_out is not None

    show.resources.show_url      = link
    show.resources.image_url     = image_url
    show.resources.resource_uris = self.resource_extractor.extract_resources(show_detail)

    return show

  def _parse_performers(self, el):    
    headliner = html_util.has_class(el, "headliners")
    support   = html_util.has_class(el, "supports")
    
    if not headliner and not support:
      return []
    elif headliner:
      return [Performer(el.text_content(), headliner = True)]
    elif support:
      return [Performer(name) for name in lang_util.parse_performers(el.text_content())]
    
  def show_list_url(self):
    return self.venue().url + 'listing'
    
  def event_url_re(self):
    return re.compile(self.venue().url + 'event/\d+')

class MercuryLounge(BoweryPresentsBase):
  def venue(self):
    return Venue('Mercury Lounge', 'http://www.mercuryloungenyc.com/')

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.mercury-lounge'

extensions.register_show_parser(MercuryLounge)
  
class BoweryBallroom(BoweryPresentsBase):
  def venue(self):
    return Venue('Bowery Ballroom', 'http://www.boweryballroom.com/')

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.bowery-ballroom'

extensions.register_show_parser(BoweryBallroom)

class MusicHallofWilliamsburg(BoweryPresentsBase):
  def venue(self):
    return Venue('Music Hall of Williamsburg', 'http://www.musichallofwilliamsburg.com/')
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.music-hall-of-williamsburg'

extensions.register_show_parser(MusicHallofWilliamsburg)

class TerminalFive(BoweryPresentsBase):
  def venue(self):
    return Venue('Terminal 5', 'http://www.terminal5nyc.com/')

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.terminal5'
    
extensions.register_show_parser(TerminalFive)

class WellmontTheatre(BoweryPresentsBase):
  def venue(self):
    return Venue('The Wellmont Theatre', 'http://www.wellmonttheatre.com/')
    
  @classmethod
  def id(cls):
    return 'us.nj.montclair.wellmont-theatre'
