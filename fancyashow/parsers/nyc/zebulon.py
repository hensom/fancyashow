from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

from fancyashow.parsers.common.myspace import MyspaceParser

extensions = ExtensionLibrary()

class Zebulon(MyspaceParser):
  def venue(self):
    return Venue('Zebulon', 'http://www.myspace.com/zebuloncafeconcert')

  @classmethod
  def profile_id(self):
    return 299508306    

  @classmethod
  def id(self):
    return 'us.ny.brooklyn.zebulon'

extensions.register_show_parser(Zebulon)