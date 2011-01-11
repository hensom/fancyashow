import re
import logging
from datetime import datetime

from fancyashow.extensions        import ExtensionLibrary, ArtistMediaExtractor, ResourceExtractor
from fancyashow.extensions        import ShowResourceHandler, ArtistResourceHandler
from fancyashow.extensions.models import VideoInfo
from fancyashow.db.models         import ArtistProfile
from fancyashow.util.resources    import URLMatch, HrefMatcher, ParamMatcher, TextMatcher
from fancyashow.util              import artist_matcher

from bandcamp                     import BandCampService
from fancyashow.systems.bandcamp.settings import API_KEY

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

PROFILE_ID = "(?P<profile_id>[\d\w_.-]+)"

HREF_URL  = URLMatch('%s.bandcamp.com' % PROFILE_ID)
SYSTEM_ID = 'bandcamp'

class BandCampResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def url(m):
      return 'bandcamp-profile:%s' % m.group('profile_id')

    ret = []

    ret.extend([url(m) for m in HrefMatcher( node, HREF_URL)])
    ret.extend([url(m) for m in TextMatcher( node, HREF_URL)])

    return ret

class BandCampShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'bandcamp-profile'

  def handle(self, show, uri):
    protocol, user_id = uri.split(':')

    logger.debug('Fetching profile information for: %s' % user_id)

    service = BandCampService(API_KEY)

    if user_id.isdigit():
      band = service.get_band_by_id(user_id)
    else:
      band = service.get_band_by_url(user_id)

    artist_profile = ArtistProfile(system_id = SYSTEM_ID, profile_id = str(band.id), source_id = 'show-resource-handler:bandcamp', url = band.url)

    return artist_matcher.associate_profile_with_matching_artist(show, band.name, artist_profile)

  @classmethod
  def id(self):
    return SYSTEM_ID

extensions.register_resource_extractor   (BandCampResourceExtractor)
extensions.register_show_resource_handler(BandCampShowResourceHandler)
