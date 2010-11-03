import               re
import               logging
from lxml     import etree
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

VIDEO_URL = 'http://vimeo.com/api/v2/video/%(video_id)s.%(format)s'

def video_info(video_id):
  logging.debug('Fetching video information for: %s' % video_id)

  url     = VIDEO_URL % {'video_id': video_id, 'format': 'xml'}

  doc     = etree.parse(url)

  title       = doc.xpath('/videos/video/title/text()')[0]
  upload_date = date_parser.parse(doc.xpath('/videos/video/upload_date/text()')[0])
  plays       = int(doc.xpath('/videos/video/stats_number_of_plays/text()')[0])
  likes       = int(doc.xpath('/videos/video/stats_number_of_likes/text()')[0])
  comments    = int(doc.xpath('/videos/video/stats_number_of_comments/text()')[0])
  
  return {'id': video_id, 'title': title, 'upload_date': upload_date, 'plays': plays, 'likes': likes, 'comments': comments}