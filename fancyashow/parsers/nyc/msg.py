from fancyashow.extensions                 import ExtensionLibrary
from fancyashow.parsers.common.live_nation import LiveNationParser
from fancyashow.extensions.models          import Venue

extensions = ExtensionLibrary()

class MadisonSquareGarden(LiveNationParser):
  def venue_id(self):
    return 237569

  def venue(self):
    return Venue('Madison Square Garden', 'http://www.thegarden.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.madison-square-garden'
                                               
extensions.register_show_parser(MadisonSquareGarden)