import logging
import urllib2
import re
import simplejson
import pylast
from pytz                         import timezone
from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

LOG = logging.getLogger(__name__)

class LastFMParser(ShowParser):  
  def __init__(self, *args, **kwargs):
    super(LastFMParser, self).__init__(*args, **kwargs)
    
    self._parser = None
  
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()
      
    while(True):
      return self._parser.next()
      
    raise StopIteration

  def _get_parser(self):
    LOG.debug("Fetching events for venue: %s" % self.venue_id())
    
    network = pylast.LastFMNetwork(self.settings['lastfm_api_key'])

    venue = pylast.Venue(self.venue_id(), network)
    
    for event in venue.get_upcoming_events():
      yield self._trans_show(event)

  def _trans_show(self, event):
    LOG.debug("Transforming show: %s" % event.get_title())

    show = Show()
    
    performers = []
    
    artists = event.get_artists()
    
    for i, artist in enumerate(artists):
      performers.append(Performer(artist.get_name(), headliner = i == 0))
      
      if artist.get_cover_image(size = pylast.COVER_MEGA):
        show.resources.image_url = artist.get_cover_image(size = pylast.COVER_MEGA)
            
    show.merge_key  = event.get_id()
    show.venue      = self.venue()
    show.performers = performers
    show.show_time  = date_util.parse_date_time(event.get_start_date())

    show.resources.show_url = event.get_url()

    return show

  def venue(self):
    raise NotImplemented()
    
  @classmethod
  def id(cls):
    raise NotImplemented()