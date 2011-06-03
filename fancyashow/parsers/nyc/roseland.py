from fancyashow.extensions            import ExtensionLibrary
from fancyashow.parsers.common.lastfm import LastFMParser
from fancyashow.extensions.models     import Venue

extensions = ExtensionLibrary()

class RoselandBallroom(LastFMParser):
  def venue_id(self):
    return 8780835

  def venue(self):
    return Venue('Roseland Ballroom', 'http://www.roselandballroom.com/')

  @classmethod
  def id(self):
    return 'us.ny.manhattan.roseland-ballroom'

extensions.register_show_parser(RoselandBallroom)