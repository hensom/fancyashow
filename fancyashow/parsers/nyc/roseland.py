from fancyashow.extensions                 import ExtensionLibrary
from fancyashow.parsers.common.live_nation import LiveNationParser
from fancyashow.extensions.models          import Venue

extensions = ExtensionLibrary()

class RoselandBallroom(LiveNationParser):
  def venue_id(self):
    return 95

  def venue(self):
    return Venue('Roseland Ballroom', 'http://www.roselandballroom.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.roseland-ballroom'

extensions.register_show_parser(RoselandBallroom)