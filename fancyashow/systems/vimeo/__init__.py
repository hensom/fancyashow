import logging
from datetime import datetime

from fancyashow.extensions        import ExtensionLibrary, ResourceExtractor, ShowResourceHandler
from fancyashow.extensions        import ArtistResourceHandler, ArtistMediaExtractor
from fancyashow.extensions.models import VideoInfo
from fancyashow.util.resources    import URLMatch, HrefMatcher, ParamMatcher
from fancyashow.util              import lang, artist_matcher

from fancyashow.systems.vimeo  import api

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

HREF_URL  = URLMatch('(www\.)?vimeo.com/(?P<video_id>\d+)\/?')
EMBED_URL = URLMatch('(www\.)?vimeo.com/.*?clip_id=(?P<video_id>\d+)')

class VimeoResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def url(m):
      return 'vimeo-video:%s' % m.group('video_id')

    ret = []

    ret.extend([url(m) for m in HrefMatcher( node,          HREF_URL)])
    ret.extend([url(m) for m in ParamMatcher(node, 'movie', EMBED_URL)])

    return ret
    
def _trans_video(video, source_id):
  media = VideoInfo('vimeo', video['id'], source_id, video['title'], upload_date = video['upload_date'])

  media.stats.number_of_plays    = video['plays']
  media.stats.number_of_likes    = video['likes']
  media.stats.number_of_comments = video['comments']
  media.stats.sample_date        = datetime.now()
  
  return media
    
class VimeoShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'vimeo-video'
    
  def handle(self, show, uri):
    protocol, video_id = uri.split(':')

    video = api.video_info(video_id)
    
    return artist_matcher.associate_video_with_matching_artist(show, _trans_video(video, 'show-resource-handler:vimeo').get_video())

  @classmethod
  def id(self):
    return 'vimeo'
    
class VimeoArtistResourceHandler(ArtistResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'vimeo-video'

  def handle(self, artist, uri):
    protocol, video_id = uri.split(':')

    video = api.video_info(video_id)

    return artist_matcher.associate_video_with_artist(artist, _trans_video(video, 'artist-resource-handler:vimeo').get_video())

  @classmethod
  def id(self):
    return 'vimeo'

class VimeoMediaExtractor(ArtistMediaExtractor):
  def extract_media(self, artist):
    videos = []
    
    for video in artist.get_videos('vimeo'):
      logger.debug('Fetching video information for: %s' % video.media_id)
        
      video = api.video_info(video.media_id)

      videos.append(_trans_video(video, 'media-extractor:vimeo-videos'))

    return videos

  @classmethod
  def id(self):
    return'vimeo'

extensions.register_resource_extractor     (VimeoResourceExtractor)
extensions.register_show_resource_handler  (VimeoShowResourceHandler)
extensions.register_artist_resource_handler(VimeoArtistResourceHandler)
extensions.register_media_extractor        (VimeoMediaExtractor)