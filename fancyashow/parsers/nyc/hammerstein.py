from fancyashow.extensions                 import ExtensionLibrary
from fancyashow.parsers.common.live_nation import LiveNationParser
from fancyashow.extensions.models          import Venue

extensions = ExtensionLibrary()

class HammersteinBallroom(LiveNationParser):
  def venue_id(self):
    return 280

  def venue(self):
    return Venue('Hammerstein Ballroom', 'http://www.mcstudios.com/mc-studio-events/the-hammerstein.php')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.hammerstein-ballroom'

extensions.register_show_parser(HammersteinBallroom)