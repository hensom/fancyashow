from fancyashow.extensions             import ExtensionLibrary
from fancyashow.parsers.common.myspace import MyspaceParser
from fancyashow.extensions.models      import Venue

extensions = ExtensionLibrary()

class CameoGallery(MyspaceParser):
  def venue(self):
    return Venue('Cameo Gallery', 'http://www.myspace.com/cameogallery/')

  @classmethod
  def profile_id(self):
    return 459194474

  @classmethod
  def id(self):
    return 'us.ny.brooklyn.cameo-gallery'

extensions.register_show_parser(CameoGallery)