from fancyashow.extensions                 import ExtensionLibrary
from fancyashow.parsers.common.live_nation import LiveNationParser
from fancyashow.extensions.models          import Venue

extensions = ExtensionLibrary()

class BeaconTheatre(LiveNationParser):
  def venue_id(self):
    return 237665

  def venue(self):
    return Venue('Beacon Theatre', 'http://www.beacontheatre.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.beacon-theatre'
                                               
extensions.register_show_parser(BeaconTheatre)