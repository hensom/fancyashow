from fancyashow.parsers.common.facebook import FacebookParser
from fancyashow.extensions              import ExtensionLibrary
from fancyashow.extensions.models       import Venue

extensions = ExtensionLibrary()

class SilentBarn(FacebookParser):
  @classmethod
  def profile_id(cls):
    return 'silentbarn'

  @classmethod
  def venue(cls):
    return Venue('Silent Barn', 'http://www.facebook.com/silentbarn')

  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.silent-barn'

extensions.register_show_parser(SilentBarn)