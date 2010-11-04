import logging
import re
import urllib2
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ResourceExtractor
from fancyashow.extensions        import ArtistResourceHandler, ShowResourceHandler
from fancyashow.extensions        import ArtistMediaExtractor, ArtistProfileParser, ArtistProfileParserResult
from fancyashow.extensions.models import AudioInfo
from fancyashow.db.models         import ArtistProfile
from fancyashow.util.resources    import HrefMatcher
from fancyashow.util              import parsing
from fancyashow.util              import artist_matcher

from fancyashow.systems.myspace import api

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

SYSTEM_ID   = 'myspace'

MYSPACE_URL = re.compile('(?:http://)?(?:www\.)?myspace\.com/(?P<profile_id>[^/&]+)', re.I)
PROFILE_URL = re.compile('(?:http://)?profile\.myspace\.com/index.cfm\?(?:[^&]*&)*friendid=(?P<profile_id>[^&]+)', re.I)
OFFSITE_URL = re.compile('http[s]?://www.msplinks.com/', re.I)

class MySpaceResourceExtractor(ResourceExtractor):
  def resources(self, node):
    def uri(match):
      return 'myspace-profile:%s' % m.group('profile_id')
      
    ret = []
    
    ret.extend( [ uri(m) for m in HrefMatcher(node, MYSPACE_URL) ] ) 
    ret.extend( [ uri(m) for m in HrefMatcher(node, PROFILE_URL) ] ) 

    return ret

class MySpaceShowResourceHandler(ShowResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'myspace-profile'
    
  def handle(self, show, uri):
    protocol, user_id = uri.split(':')
    
    logger.debug('Fetching profile information for: %s' % user_id)
    
    profile        = api.MySpaceProfile(user_id)

    artist_profile = ArtistProfile(system_id = 'myspace', profile_id = user_id, source_id = 'show-resource-handler:myspace', url = 'http://www.myspace.com/%s' % user_id)
    
    return artist_matcher.associate_profile_with_matching_artist(show, profile.get_name(), artist_profile)

  @classmethod
  def id(self):
    return 'myspace'
    
class MySpaceArtistResourceHandler(ArtistResourceHandler):
  def supports(self, uri):
    protocol, user_id = uri.split(':')

    return protocol == 'myspace-profile'

  def handle(self, show, uri):
    protocol, user_id = uri.split(':')

    logger.debug('Fetching profile information for: %s' % user_id)

    profile        = api.MySpaceProfile(user_id)

    artist_profile = ArtistProfile(system_id = 'myspace', profile_id = user_id, source_id = 'artist-resource-handler:myspace', url = 'http://www.myspace.com/%s' % user_id)

    return artist_matcher.associate_profile_with_artist(artist, artist_profile)

  @classmethod
  def id(self):
    return 'myspace'

class MySpaceSongExtractor(ArtistMediaExtractor):
  def extract_media(self, artist):
    audio = []

    for artist_profile in artist.get_profiles('myspace'):
      user_id = artist_profile.profile_id

      logger.debug('Fetching playlist information for: %s' % user_id)

      profile = api.MySpaceProfile(user_id)

      media = []

      logger.debug('Profile info: is_music_artist: %s, has_playlist: %s' % (profile.is_music_artist(), profile.has_playlist()))

      if profile.is_music_artist() and profile.has_playlist():
        now = datetime.now()

        def trans(track):
          info =  AudioInfo('myspace', track['id'], 'media-extractor:myspace-songs', track['title'], artist = track['artist'])

          info.stats.number_of_plays = track['play_count']
          info.stats.sample_date     = now

          return info

        audio.extend([trans(track) for track in profile.get_tracks()])

    return audio
    
  @classmethod
  def id(cls):
    return 'myspace-songs'
    
class GetRedirectHandler(urllib2.HTTPRedirectHandler):
  def http_error_302(self, req, fp, code, msg, headers):
    return urllib2.addinfourl(fp, headers, req.get_full_url(), code)

  http_error_301 = http_error_303 = http_error_307 = http_error_302

class MyspaceProfileParser(ArtistProfileParser):
  def supports(self, profile):
    return profile.system_id == SYSTEM_ID

  def parse(self, artist, profile):
    doc  = parsing.fetch_and_parse('http://www.myspace.com/%s' % profile.profile_id)
    body = parsing.get_first_element(doc, 'body')
    
    self._resolve_offsite_links(doc)

    if parsing.has_class(body, 'profileV1'):
      logger.debug('%s is v1 profile' % profile.profile_id)

      return self._parse_v1(doc)
    elif 'layout_0_2' in body.get('class'):
      logger.debug('%s is v2 profile' % profile.profile_id)

      return self._parse_v2(doc)
    else:
      raise Exception('Unable to determine myspace profile version')

  def _resolve_offsite_links(self, doc):
    logger.debug('Resolving msplinks.com links')

    for a in doc.iter(tag = 'a'):
      if OFFSITE_URL.match(a.get('href', '')):
        logger.debug('Found offsite link: %s' % a.get('href'))
        
        opener = urllib2.build_opener(GetRedirectHandler())

        req = urllib2.Request(url = a.get('href'))
        
        fp = None
        
        try:
          fp = opener.open(req)
          
          if fp.info()['Location']:
            logger.debug('Url resolved to: %s' % fp.info()['Location'])
        
            a.set('href', fp.info()['Location'])
          else:
            logger.debug('Url was not redirected, leaving as is')
        except:
          logger.exception('Unable to resolve url')
        finally:
          if fp:
            fp.close()
            
            
    for a in doc.iter(tag = 'a'):
      logger.error('Found link: %s' % a.get('href'))

  def _parse_v1(self, doc):
    to_drop = ('table.friendsComments', 'table.friendSpace', '#footerWarpper', '#header', '#musicJVNav')
    
    for selector in to_drop:
      for drop in doc.cssselect(selector):
        drop.drop_tree()

    info_rows = dict((css_id, True) for css_id in('Member SinceRow', 'Band WebsiteRow', 'Sounds LikeRow', 'RecordLabelRow', 'Type of LabelRow'))

    tr        = None
    
    for test_row in doc.iter('tr'):
      if test_row.get('id') in info_rows:
        tr = test_row
        
        break
        
    if tr == None:
      raise Exception('Unable to locate info table')
    else:
      table = None
      
      for item in tr.iterancestors(tag = 'table'):
        table = item
        
        break
        
      resources = self.resource_extractor.extract_resources(doc)
      
      return ArtistProfileParserResult(resources)
      
  def _parse_v2(self, doc):
    content    = parsing.get_first_element(doc, '.content.contentMid')

    html_boxes = list(parsing.get_elements(content, '.htmlBoxModule'))

    resources = self.resource_extractor.extract_resources(*html_boxes)
    
    return ArtistProfileParserResult(resources)

  @classmethod
  def id(self):
    return SYSTEM_ID

extensions.register_resource_extractor     (MySpaceResourceExtractor)
extensions.register_show_resource_handler  (MySpaceShowResourceHandler)
extensions.register_artist_resource_handler(MySpaceArtistResourceHandler)
extensions.register_media_extractor        (MySpaceSongExtractor)
extensions.register_artist_profile_parser  (MyspaceProfileParser)