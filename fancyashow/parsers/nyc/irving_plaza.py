from fancyashow.extensions            import ExtensionLibrary
from fancyashow.parsers.common.lastfm import LastFMParser
from fancyashow.extensions.models     import Venue

extensions = ExtensionLibrary()

class IrvingPlaza(LastFMParser):
  def venue_id(self):
    return 8778815

  def venue(self):
    return Venue('Irving Plaza', 'http://www.irvingplaza.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.irving-plaza'

extensions.register_show_parser(IrvingPlaza)