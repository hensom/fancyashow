from fancyashow.extensions                 import ExtensionLibrary
from fancyashow.parsers.common.live_nation import LiveNationParser
from fancyashow.extensions.models          import Venue

extensions = ExtensionLibrary()

class RadioCityMusicHall(LiveNationParser):
  def venue_id(self):
    return 237571

  def venue(self):
    return Venue('Radio City Music Hall', 'http://www.radiocity.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.radio-city-music-hall'
                                               
extensions.register_show_parser(RadioCityMusicHall)