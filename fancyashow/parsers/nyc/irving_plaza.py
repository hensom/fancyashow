from fancyashow.extensions                 import ExtensionLibrary
from fancyashow.parsers.common.live_nation import LiveNationParser
from fancyashow.extensions.models          import Venue

extensions = ExtensionLibrary()

class IrvingPlaza(LiveNationParser):
  def venue_id(self):
    return 47

  def venue(self):
    return Venue('Irving Plaza', 'http://www.irvingplaza.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.irving-plaza'

extensions.register_show_parser(IrvingPlaza)