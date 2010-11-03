import                           logging
from fancyashow.db.models import Audio, Video, MediaStatsHistory

logger = logging.getLogger(__name__)
    
class MediaStats(object):
  number_of_plays    = None
  number_of_comments = None
  number_of_likes    = None
  rating             = None
  num_raters         = None
  sample_date        = None

class MediaInfo(object):
  def __init__(self, system_id, media_id, source_id, title, upload_date = None, artist = None):
    self.system_id   = system_id
    self.media_id    = media_id
    self.source_id   = source_id
    self.artist      = artist
    self.title       = title
    self.stats       = MediaStats()
    self.upload_date = upload_date

  def __str__(self):
    return unicode(self).encode('utf-8')
    
  def __unicode__(self):
    return '%s - %s' % (self.system_id, self.media_id)

  def _get_media(self, media_class):
    media = media_class(artist = self.artist, title = self.title, system_id = self.system_id, media_id = self.media_id, source_id = self.source_id, upload_date = self.upload_date)
    
    media.stats.add_stats([self._trans_stats()])
    
    return media
    
  def _trans_stats(self):
    stats = {
      'number_of_plays':    self.stats.number_of_plays,
      'number_of_comments': self.stats.number_of_comments,
      'number_of_likes':    self.stats.number_of_likes,
      'rating':             self.stats.rating,
      'num_raters':         self.stats.num_raters,
      'sample_date':        self.stats.sample_date
    }

    return MediaStatsHistory(**stats)

class AudioInfo(MediaInfo):
  def get_audio(self):
    return self._get_media(Audio)

class VideoInfo(MediaInfo):
  def get_video(self):
    return self._get_media(Video)