import logging
from datetime import datetime

from fancyashow.extensions        import ExtensionLibrary, ArtistMediaExtractor, ResourceExtractor
from fancyashow.extensions        import ShowResourceHandler, ArtistResourceHandler
from fancyashow.extensions.models import VideoInfo
from fancyashow.util.resources    import URLMatch, HrefMatcher, ParamMatcher
from fancyashow.util              import artist_matcher

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

HREF_URL  = URLMatch('(www\.)?soundcloud.com/(?P<profile_id>[^/])+')
EMBED_URL = URLMatch('player.soundcloud.com/player.swf?url=http[s]?%3A%2F%2Fsoundcloud.com%2F(?P<profile_id>[^%]+)')

class SoundCloudResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def url(m):
      return 'soundcloud-profile:%s' % m.group('profile_id')

    ret = []

    ret.extend([url(m) for m in HrefMatcher( node,          HREF_URL)])
    ret.extend([url(m) for m in ParamMatcher(node, 'movie', EMBED_URL)])

    return ret

extensions.register_resource_extractor     (SoundCloudResourceExtractor)
