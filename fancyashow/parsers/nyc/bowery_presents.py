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
    show_urls = html_util.get_show_urls_and_section(self.show_list_url(), '#list-view', {'tag': 'li'}, self.event_url_re())

    for url, show_section in show_urls.iteritems():
      yield self._parse_show(url, show_section)

  def _parse_show(self, link, show_section):
    show_doc    = html_util.fetch_and_parse(link)

    show_detail = show_doc.get_element_by_id("featured")

    # Not all pages have one of these
    artist_info = html_util.get_first_element(show_doc, "#artist-info", optional = True)

    summary     = html_util.get_first_element(show_detail, ".summary")
    description = html_util.get_first_element(show_detail, ".description")
    start_time  = html_util.get_first_element(show_section, 'abbr.dtstart').get('title')
    image_el    = html_util.get_first_element(show_detail,  '#featured')
    soldout     = html_util.has_class(show_detail, 'soldout')

    image_match = self.IMAGE_RE.search(image_el.get('style'))
    
    if image_match:
      image_url = urlparse.urljoin(link, image_match.group('image_path'))
    else:
      image_url = None
    
    performers = [] 
    
    for tag in ('h1', 'h2', 'h3'):
      for p in summary.iter(tag = tag):
        if p.text_content():        
          performers.extend(self._parse_performers(p))

    show = Show()

    show.merge_key               = link
    show.venue                   = self.venue()
    show.performers              = performers
    show.show_time               = date_util.parse_date_time(start_time)
    show.soldout                 = soldout

    show.resources.show_url      = link
    show.resources.image_url     = image_url
    show.resources.resource_uris = self.resource_extractor.extract_resources(show_detail, artist_info)

    return show

  def _parse_performers(self, el):
    """
    Sample Multi Performer Case

    <h1>
      The Watson Twins<br />
      <span class="t">10:30</span><br />
      Sean Bones<br />
      <span class="t">9:30</span>
    </h1>
    
    """
    performers = []
      
    f = el.getchildren()
    
    # Initialize our first performer's name
    name = el.text
    
    headliner = el.tag == 'h1' 
    
    for e in el.getchildren():
      # if we find a new element with a tail and had a prior artist, we need to pop it
      if e.tail:
        if name:
          performers.append(Performer(name, headliner = headliner))

        name = e.tail
      # if we have a start time process it
      elif e.tag == 'span':
        performers.append(Performer(name, start_time = e.text, headliner = headliner))

        name = None
        
    if name:
      for performer_name in name.split('/'):
        performers.append(Performer(performer_name.strip(), headliner = headliner))
      
    return performers
    
  def show_list_url(self):
    return self.venue().url + 'events'
    
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
