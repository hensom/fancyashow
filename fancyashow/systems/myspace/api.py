import logging
import urllib2
import re
import lxml.html
from lxml import etree

logger = logging.getLogger(__name__)

ARTIST_ID_RE        = re.compile('artid=(\d+)&')
FRIEND_ID_RE        = re.compile('"DisplayFriendId":(\d+),')
PLAYLIST_ID_RE      = re.compile('plid=(\d+)&')
NAME_RE             = re.compile('\s*(.+)(?:\s+on myspace.*)', re.I | re.M)

PLAYLIST_URL_FORMAT = "http://musicservices.myspace.com/Modules/MusicServices/Services/MusicPlayerService.ashx?artistId=%(artist_id)s&action=getArtistPlaylist&artistUserId=%(friend_id)s&playlistId=%(playlist_id)d"
SONG_URL_FORMAT     = "http://musicservices.myspace.com/Modules/MusicServices/Services/MusicPlayerService.ashx?songId=%(song_id)s&action=getSong&ptype=4"

PLAYLIST_NS_MAP     = {'x': 'http://xspf.org/ns/0/'}

TRACKS_XPATH        = etree.XPath('/x:playlist/x:trackList/x:track',               namespaces = PLAYLIST_NS_MAP)
SONG_ID_XPATH       = etree.XPath('./x:song/@songId',                              namespaces = PLAYLIST_NS_MAP)
RELEASE_ID_XPATH    = etree.XPath('./x:song/@releaseId',                           namespaces = PLAYLIST_NS_MAP)
ARTIST_NAMES_XPATH  = etree.XPath('./x:song/x:artists/x:artist/@name',             namespaces = PLAYLIST_NS_MAP)
TITLE_XPATH         = etree.XPath('./x:title/text()',                              namespaces = PLAYLIST_NS_MAP)
PLAY_COUNT_XPATH    = etree.XPath('./x:song/x:stats/@plays',                       namespaces = PLAYLIST_NS_MAP)
RTMP_XPATH          = etree.XPath('/x:playlist/x:trackList/x:track/x:rtmp/text()', namespaces = PLAYLIST_NS_MAP)

class MySpacePlaylist:
  def __init__(self, profile, playlistId):
    self._profile = profile
    self._id      = playlistId

  def get_tracks(self):
    playlist_url = PLAYLIST_URL_FORMAT % {'artist_id': self._profile.artist_id, 'friend_id': self._profile.friend_id, 'playlist_id': self._profile.playlist_id}
    
    logger.debug('Fetching playlist data: %s' % playlist_url)
    
    doc          = etree.parse(playlist_url)

    tracks       = []

    for track in TRACKS_XPATH(doc):
      song_id    = SONG_ID_XPATH(track)[0]
      
      release_id = RELEASE_ID_XPATH(track)[0]
      
      # Sometimes songs returned in the playlist are complete garbage
      # There can be identified by the lack of a release id
      if release_id != "0":
        tracks.append({
          'id':         song_id,
          'artist':     self._form_artist_name(ARTIST_NAMES_XPATH(track)),
          'title':      TITLE_XPATH(track)[0],
          'play_count': int(PLAY_COUNT_XPATH(track)[0])
        })
      else:
        logger.warn('Skipping song without release id: %s (song is likely to be malformed)' % song_id)
  
    return tracks

  def _form_artist_name(self, names):
    if len(names) == 1:
      return names[0]
    else:
      return '%s and %s' % (', '.join(names[:-1]), names[-1])

# from fancyashow.ext.myspace import api
# profile = api.MySpaceProfile('thetwinshadow')
# profile.get_name()

class MySpaceProfile:  
  def __init__(self, profile_id):
    profile_link = 'http://www.myspace.com/' + profile_id
    
    self.name = None
    
    logger.debug('Fetching profile page: %s' % profile_link)
    
    html = urllib2.urlopen(profile_link).read()
    
    doc  = lxml.html.document_fromstring(html)
    
    for title in doc.iter(tag = 'title'):
      logger.debug('Fetching profile name from: %s' % title.text_content())
      match = NAME_RE.match(title.text_content())
      
      if match:
        self.name = match.group(1).strip()

        logger.debug("Profile name is: %s" % self.name)

        break
        
    if not self.name:
      raise Exception('Unable to determine profile name for myspace user: %s' % profile_id)

    self.friend_id = FRIEND_ID_RE.search(html)
    self.playlist_id = None

    if None != self.friend_id:
      self.friend_id = self.friend_id.group(1)

    self.artist_id = ARTIST_ID_RE.search(html)
    
    if None != self.artist_id:
      self.artist_id = self.artist_id.group(1)
      
    self.playlist_id = None

    if self.artist_id:
      playlist_match = PLAYLIST_ID_RE.search(html)
      
      if playlist_match:
        self.playlist_id = int(playlist_match.group(1))
        
  def get_name(self):
    return self.name

  def is_music_artist( self ):
    if None != self.artist_id:
        return True
    return False
    
  def has_playlist(self):
    return self.playlist_id is not None

  def get_tracks( self ):
    playlist = self.get_playlist()

    return playlist.get_tracks()

  def get_playlist( self ):
    return MySpacePlaylist(self, self.playlist_id)