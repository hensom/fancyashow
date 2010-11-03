from fancyashow.extensions             import ExtensionLibrary
from fancyashow.parsers.common.myspace import MyspaceParser
from fancyashow.extensions.models      import Venue

extensions = ExtensionLibrary()

class SheaStadium(MyspaceParser):
  def venue(self):
    return Venue('Shea Stadium', 'http://www.myspace.com/sheastadiumbk')

  @classmethod
  def profile_id(self):
    return 463786807    

  @classmethod
  def id(self):
    return 'us.ny.brooklyn.shea-stadium'

extensions.register_show_parser(SheaStadium)