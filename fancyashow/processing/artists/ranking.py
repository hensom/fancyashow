from copy     import deepcopy
import logging
from fancyashow.extensions         import ExtensionLibrary
from fancyashow.extensions.artists import ArtistProcessor
from fancyashow.processing  import ProcessorSetup
from fancyashow.db.models   import SystemStat

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class ArtistRanking(ArtistProcessor):
  def __init__(self, *args, **kwargs):
    super(ArtistRanking, self).__init__(*args, **kwargs)
    
    self._stats = None

  def stats(self):
    if not self._stats:
      stats = { }

      for stat in SystemStat.objects():
        stats[ stat.system_id ] = stat
        
      self._stats = stats

    return self._stats

  def process(self, artist, state, dependent_states):
    media_info = []
    
    for m in artist.media:
      plays_per_day = m.stats.stats_last_3_days().number_of_plays
      system_stat   = self.stats().get(m.system_id)
      
      if plays_per_day != None and system_stat:
        media_info.append( ( ( plays_per_day - system_stat.plays_per_day)  / system_stat.stddev ) )
        
    media_info.sort(reverse = True)

    if media_info:
      logger.debug('Media: %s' % media_info)
      artist.rank = sum(media_info[0:3]) / len(media_info[0:3])
    else:
      artist.rank = None
    
    return deepcopy(state)

  def cleanup(self, show, state):
    pass
    
  @classmethod
  def id(self):
    return 'ranking'
    
  @classmethod
  def depends_on(self):
    return ( )#'media-extraction', )

extensions.register_artist_processor(ArtistRanking)