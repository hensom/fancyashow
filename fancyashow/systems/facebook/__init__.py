import logging
from datetime import datetime

from facebook                     import GraphAPI
from fancyashow.extensions        import ExtensionLibrary, ArtistMediaExtractor, ResourceExtractor
from fancyashow.extensions        import ShowResourceHandler, ArtistResourceHandler
from fancyashow.util.resources    import URLMatch, HrefMatcher, TextMatcher
from fancyashow.db.models         import ArtistProfile
from fancyashow.util              import artist_matcher

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

OBJECT_ID = "(?P<object_id>[\d\w_.-]+)"

STRICT_PROFILE_URL = URLMatch('(www\.)?facebook.com/%s/?$' % OBJECT_ID)
PROFILE_URL        = URLMatch('(www\.)?facebook.com/%s' % OBJECT_ID)
GROUP_URL          = URLMatch('(www\.)?facebook.com/group.php\?.*?gid=%s' % OBJECT_ID)
EVENT_URL          = URLMatch('(www\.)?facebook.com/event.php\?.*?eid=%s' % OBJECT_ID)
PAGE_URL           = URLMatch('(www\.)?facebook.com/pages/[^/]+/%s' % OBJECT_ID)
PAGE_AJAX_URL      = URLMatch('(www\.)?facebook.com/home.php#!/pages/[^/]+/%s' % OBJECT_ID)

class FacebookResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def url(m):
      return 'facebook:%s' % m.group('object_id')

    ret = []

    ret.extend([url(m) for m in HrefMatcher( node, STRICT_PROFILE_URL)])
    ret.extend([url(m) for m in HrefMatcher( node, GROUP_URL)])
    ret.extend([url(m) for m in HrefMatcher( node, EVENT_URL)])
    ret.extend([url(m) for m in HrefMatcher( node, PAGE_URL)])
    ret.extend([url(m) for m in HrefMatcher( node, PAGE_AJAX_URL)])

    ret.extend([url(m) for m in TextMatcher( node, PROFILE_URL)])
    ret.extend([url(m) for m in TextMatcher( node, GROUP_URL)])
    ret.extend([url(m) for m in TextMatcher( node, EVENT_URL)])
    ret.extend([url(m) for m in TextMatcher( node, PAGE_URL)])
    ret.extend([url(m) for m in TextMatcher( node, PAGE_AJAX_URL)])

    return ret
  
class FacebookShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'facebook'

  def handle(self, show, uri):
    protocol, object_id = uri.split(':')
    
    logger.debug('Fetching facebook object: %s' % object_id)
    
    profile        = GraphAPI().get_object(object_id)
    
    logging.debug('Item: %s' % profile)

    # Not all profiles have links
    if 'link' in profile:
      artist_profile = ArtistProfile(system_id = 'facebook', profile_id = profile['id'], source_id = 'show-resource-handler:facebook', url = profile['link'])
    
      return artist_matcher.associate_profile_with_matching_artist(show, profile['name'], artist_profile)
    else:
      return False

  @classmethod
  def id(self):
    return 'facebook'

extensions.register_resource_extractor   (FacebookResourceExtractor)
extensions.register_show_resource_handler(FacebookShowResourceHandler)