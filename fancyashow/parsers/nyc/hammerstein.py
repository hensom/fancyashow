from fancyashow.extensions            import ExtensionLibrary
from fancyashow.parsers.common.lastfm import LastFMParser
from fancyashow.extensions.models     import Venue

extensions = ExtensionLibrary()

class HammersteinBallroom(LastFMParser):
  def venue_id(self):
    return 8778684

  def venue(self):
    return Venue('Hammerstein Ballroom', 'http://www.mcstudios.com/mc-studio-events/the-hammerstein.php')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.hammerstein-ballroom'

extensions.register_show_parser(HammersteinBallroom)