from datetime import datetime
from copy     import deepcopy
import logging
from fancyashow.extensions       import ExtensionLibrary
from fancyashow.extensions.shows import ShowProcessor
from fancyashow.processing       import ProcessorSetup
from fancyashow.util             import artist_matcher

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class ArtistAssociation(ShowProcessor):
  def process(self, show, state, dependent_states):
    artist_ids = []

    for artist_info in show.artists:
      if not artist_info.artist_id:
        artist = artist_matcher.get_artist(artist_info.name)
        
        if artist:
          artist_info.artist_id = artist.id

      if artist_info.artist_id:
        artist_ids.append(artist_info.artist_id)

    show.artist_ids = artist_ids

  def cleanup(self, show, state):
    pass
    
  @classmethod
  def id(self):
    return 'artist-association'
    
  @classmethod
  def depends_on(self):
    return ( )
  
class ArtistProcessor(ShowProcessor):
  def __init__(self, library, settings):
    super(ArtistProcessor, self).__init__(library, settings)

    self.artist_processor_settings = self.get_required_setting(settings, 'artist_processor_settings')
    self.setup  = ProcessorSetup(self.library, self.library.artist_processors(), self.artist_processor_settings)
    
    self.runner = self.setup.runner()

  def process(self, show, state, dependent_states):
    logger.debug('[show:%s] Starting artist processing' % (show.id))

    for artist in show.related_artists().values():  
      logger.debug('[show:%s] Starting artist processing for artist: %s (%s)' % (show.id, artist.name, artist.id))

      self.runner.process(artist)

  def cleanup(self, show, state):
    for artist in show.related_artists().values():  
      self.runner.cleanup(artist)
    
  @classmethod
  def id(self):
    return 'artist-processor'
    
  @classmethod
  def depends_on(self):
    return ( 'resource-handler', 'artist-association' )
  
extensions.register_show_processor(ArtistAssociation)
extensions.register_show_processor(ArtistProcessor)
