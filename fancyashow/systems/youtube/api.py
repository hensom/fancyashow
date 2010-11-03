import logging
import gdata.youtube
import gdata.youtube.service
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

def video_info(video_id):
  logger.debug('Fetching video information for: %s' % video_id)

  service = gdata.youtube.service.YouTubeService()
  
  service.ssl = False

  entry       = service.GetYouTubeVideoEntry(video_id = video_id)

  title       = entry.media.title.text
  upload_date = date_parser.parse(entry.published.text)
  plays       = int(entry.statistics.view_count)
  likes       = int(entry.statistics.favorite_count)
  comments    = int(entry.comments.feed_link[0].count_hint)
  rating      = float(entry.rating.average)
  num_raters  = int(entry.rating.num_raters)
  
  return {'id': video_id, 'title': title, 'upload_date': upload_date, 'plays': plays, 'likes': likes, 'comments': comments, 'rating': rating, 'num_raters': num_raters}