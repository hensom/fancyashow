import logging
import re
import urllib2
import lxml.html
from lxml import etree
from fancyashow.extensions     import ExtensionLibrary, ResourceExtractor, ShowResourceHandler, ArtistResourceHandler
from fancyashow.util.resources import HrefMatcher
from fancyashow.db.models      import ArtistProfile
from fancyashow.util           import artist_matcher, parsing

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

NAME_RE     = re.compile('\s*(.+)(?:\s+\(.+?\)\s+on twitter.*)', re.I | re.M)
TWITTER_URL = re.compile('(?:http[s]?://)?(?:www\.)?twitter\.com/(?P<profile_id>[^/&]+)', re.I)

class TwitterResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def uri(match):
      return 'twitter-profile:%s' % m.group('profile_id')
      
    ret = []

    ret.extend( [ uri(m) for m in HrefMatcher(node, TWITTER_URL) ] ) 

    return ret

class TwitterShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'twitter-profile'
    
  def handle(self, show, uri):
    protocol, user_id = uri.split(':')
    
    profile_link = 'http://www.twitter.com/%s' % user_id
    
    name = parsing.get_name_from_title(profile_link, NAME_RE)

    artist_profile = ArtistProfile(system_id = 'twitter', profile_id = user_id, source_id = 'show-resource-handler:twitter', url = profile_link)
    
    return artist_matcher.associate_profile_with_matching_artist(show, name, artist_profile)

  @classmethod
  def id(self):
    return 'twitter'

class TwitterArtistResourceHandler(ArtistResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'twitter-profile'

  def handle(self, show, uri):
    protocol, user_id = uri.split(':')

    profile_link = 'http://www.twitter.com/%s' % user_id

    name = parsing.get_name_from_title(profile_link, NAME_RE)

    artist_profile = ArtistProfile(system_id = 'twitter', profile_id = user_id, source_id = 'artist-resource-handler:twitter', url = profile_link)

    return artist_matcher.associate_profile_with_artist(show, name, artist_profile)

  @classmethod
  def id(self):
    return 'twitter'

extensions.register_resource_extractor     (TwitterResourceExtractor)
extensions.register_show_resource_handler  (TwitterShowResourceHandler)
extensions.register_artist_resource_handler(TwitterArtistResourceHandler)