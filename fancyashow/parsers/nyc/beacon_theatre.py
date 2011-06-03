from fancyashow.extensions            import ExtensionLibrary
from fancyashow.parsers.common.lastfm import LastFMParser
from fancyashow.extensions.models     import Venue

extensions = ExtensionLibrary()

class BeaconTheatre(LastFMParser):
  def venue_id(self):
    return 8825722

  def venue(self):
    return Venue('Beacon Theatre', 'http://www.beacontheatre.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.beacon-theatre'
                                               
extensions.register_show_parser(BeaconTheatre)