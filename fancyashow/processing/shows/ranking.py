from copy     import deepcopy
import logging
from fancyashow.extensions       import ExtensionLibrary
from fancyashow.extensions.shows import ShowProcessor
from fancyashow.processing       import ProcessorSetup

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class ShowRanking(ShowProcessor):
  def process(self, show, state, dependent_states):
    artists = show.related_artists().values()
    
    if artists:
      show.rank = max(a.rank for a in artists)
    
    return deepcopy(state)

  def cleanup(self, show, state):
    pass
    
  @classmethod
  def id(self):
    return 'ranking'
    
  @classmethod
  def depends_on(self):
    return ( )#'artist-processor', )
  
extensions.register_show_processor(ShowRanking)