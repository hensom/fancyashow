import logging
from datetime import datetime

from fancyashow.extensions        import ExtensionLibrary, ArtistMediaExtractor, ResourceExtractor
from fancyashow.extensions        import ShowResourceHandler, ArtistResourceHandler
from fancyashow.extensions.models import VideoInfo
from fancyashow.util.resources    import URLMatch, HrefMatcher, ParamMatcher, TagAttrMatcher
from fancyashow.util              import artist_matcher

from fancyashow.systems.youtube  import api

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

HREF_URL      = URLMatch('(www\.)?youtube.com/watch?(.+&)?v=(?P<video_id>[^&])+')
EMBED_URL     = URLMatch('(www\.)?youtube.com/v/(?P<video_id>[^&]+)')
NEW_EMBED_URL = URLMatch('(www\.)?youtube.com/embed/(?P<video_id>[^&]+)')

class YouTubeResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def url(m):
      return 'youtube-video:%s' % m.group('video_id')

    ret = []

    ret.extend([url(m) for m in HrefMatcher( node,          HREF_URL)])
    ret.extend([url(m) for m in ParamMatcher(node, 'movie', EMBED_URL)])
    ret.extend([url(m) for m in TagAttrMatcher(node, ['iframe'], ['src'], NEW_EMBED_URL)])

    return ret

def _trans_video(video, source_id):
  media = VideoInfo('youtube', video['id'], source_id, video['title'], upload_date = video['upload_date'])

  media.stats.number_of_plays    = video['plays']
  media.stats.number_of_likes    = video['likes']
  media.stats.number_of_comments = video['comments']
  media.stats.rating             = video['rating']
  media.stats.num_raters         = video['num_raters']
  media.stats.sample_date        = datetime.now()
  
  return media
  
class YouTubeShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'youtube-video'

  def handle(self, show, uri):
    protocol, video_id = uri.split(':')

    video = api.video_info(video_id)
    
    return artist_matcher.associate_video_with_matching_artist(show, _trans_video(video, 'show-resource-handler:youtube').get_video())

  @classmethod
  def id(self):
    return 'youtube'
    
class YouTubeArtistResourceHandler(ArtistResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'youtube-video'

  def handle(self, artist, uri):
    protocol, video_id = uri.split(':')

    video = api.video_info(video_id)

    return artist_matcher.associate_video_with_artist(artist, _trans_video(video, 'artist-resource-handler:youtube').get_video())

  @classmethod
  def id(self):
    return 'youtube'

class YouTubeMediaExtractor(ArtistMediaExtractor):
  def extract_media(self, artist):
    videos = []
    
    for video in artist.get_videos('youtube'):
      logger.debug('Fetching video information for: %s' % video.media_id)
        
      video = api.video_info(video.media_id)

      videos.append(_trans_video(video, 'media-extractor:youtube-videos'))

    return videos

  @classmethod
  def id(self):
    return 'youtube'

extensions.register_resource_extractor     (YouTubeResourceExtractor)
extensions.register_show_resource_handler  (YouTubeShowResourceHandler)
extensions.register_artist_resource_handler(YouTubeArtistResourceHandler)
extensions.register_media_extractor        (YouTubeMediaExtractor)
