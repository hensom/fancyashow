import logging
import re
import urllib2
import lxml.html
from lxml                       import etree
from fancyashow.extensions      import ExtensionLibrary, ResourceExtractor, ShowResourceHandler, ArtistResourceHandler
from fancyashow.util.resources  import URLMatch, HrefMatcher, TextMatcher
from fancyashow.db.models       import ArtistProfile
from fancyashow.util            import artist_matcher, parsing

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

PROFILE_ID = "(?P<profile_id>[\d\w_.-]+)"

PROFILE_URL = URLMatch('%s\.muxtape\.com/' % PROFILE_ID)
NAME_RE     = re.compile('\s*(.+)(?:\s+on muxtape.*)', re.I | re.M)

class MuxtapeResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def uri(match):
      return 'muxtape-profile:%s' % m.group('profile_id')
      
    ret = []

    ret.extend( [ uri(m) for m in HrefMatcher(node, PROFILE_URL) ] ) 
    ret.extend( [ uri(m) for m in TextMatcher(node, PROFILE_URL) ] ) 

    return ret

class MuxtapeShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'muxtape-profile'
    
  def handle(self, show, uri):
    protocol, user_id = uri.split(':')
    
    profile_link = 'http://%s.muxtape.com/' % user_id

    name = parsing.get_name_from_title(profile_link, NAME_RE)

    artist_profile = ArtistProfile(system_id = 'muxtape', profile_id = user_id, source_id = 'show-resource-handler:muxtape', url = profile_link)
    
    return artist_matcher.associate_profile_with_matching_artist(show, name, artist_profile)

  @classmethod
  def id(self):
    return 'muxtape'
    
class MuxtapeArtistResourceHandler(ArtistResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'muxtape-profile'

  def handle(self, artist, uri):
    protocol, user_id = uri.split(':')

    profile_link = 'http://%s.muxtape.com/' % user_id

    name = parsing.get_name_from_title(profile_link, NAME_RE)

    artist_profile = ArtistProfile(system_id = 'muxtape', profile_id = user_id, source_id = 'artist-resource-handler:muxtape', url = profile_link)

    return artist_matcher.associate_profile_with_artist(artist, name, artist_profile)

  @classmethod
  def id(self):
    return 'muxtape'

extensions.register_resource_extractor     (MuxtapeResourceExtractor)
extensions.register_show_resource_handler  (MuxtapeShowResourceHandler)
extensions.register_artist_resource_handler(MuxtapeArtistResourceHandler)
