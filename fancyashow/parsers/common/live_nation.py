import logging
import urllib2
import re
import simplejson
from pytz                         import timezone
from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

logger = logging.getLogger(__name__)

class LiveNationParser(ShowParser):
  EVENTS_URL_BASE = 'http://www.livenation.com/json/search/event?vid=%d'
  IMAGE_URL_BASE  = 'http://media.ticketmaster.com/ln/%(lang_code)s%(image_path)s'

  BASE_URL = "http://www.bruarfalls.com/"
  NUM_RE   = re.compile('^\s*\d+\s*(?:st|nd|rd|th):\s*', re.IGNORECASE | re.MULTILINE)
  
  def __init__(self, *args, **kwargs):
    super(LiveNationParser, self).__init__(*args, **kwargs)
    
    self._parser = None
  
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()
      
    while(True):
      return self._parser.next()
      
    raise StopIteration

  def _get_parser(self):  
    events_url = self.EVENTS_URL_BASE % self.venue_id()
    
    logger.debug("Fetching events from: %s" % events_url)

    res = urllib2.urlopen(events_url)
    
    data = simplejson.load(res)
    
    shows = data['response']['docs']
    
    for show_data in shows:
      show = self._trans_show(show_data)
      
      if show:
        yield show
        
  def _image_url(self, show_data, url_fragment):
    return self.IMAGE_URL_BASE % {'lang_code': show_data['LangCode'], 'image_path': url_fragment}

  def _trans_show(self, show_data):
    if "Music" not in show_data['MajorGenre']:
      return None
    elif show_data.get('Canceled'):
      return None
    elif 'VIP Packages' in show_data['EventName']:
      return None
  
    show = Show()
    
    performers = []
    
    for i, name in enumerate(lang_util.parse_performers(show_data['EventName'])):
      performers.append(Performer(name, headliner = i == 0))
            
    show.merge_key  = show_data['EventId']
    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_date_time(show_data['EventDate'])
    
    #if show.show_time:
    #  show.show_time = timezone(show_data['Timezone']).localize(show.show_time)
    
    if show_data['AttractionImage']:
      show.resources.image_url = self._image_url(show_data, show_data['AttractionImage'][0])

    return show

  def venue(self):
    return Venue('Bruar Falls', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.bruar-falls'