import urllib2
import subprocess
import logging

from tempfile import TemporaryFile

from fancyashow.extensions.artists import ArtistProcessor

from fancyashow.util.storage      import ChunkedFile
from fancyashow.extensions        import ExtensionLibrary
from datetime                     import datetime
from fancyashow.db.models         import Audio, Video, MediaStatsHistory
from fancyashow.extensions.models import AudioInfo, VideoInfo

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class MediaExtractionProcessor(ArtistProcessor):
  def __init__(self, library, settings):
    super(MediaExtractionProcessor, self).__init__(library, settings)

    self.update_interval = self.get_required_setting(settings, 'update_interval')

  @classmethod
  def default_state(self):
    return {'extractor_state': { }}

  def process(self, artist, state, dependent_states):
    new_state = self.clone_state(state)
    media     = []
    
    extractors = [e() for e in self.library.media_extractors()]
    
    for extractor in extractors:
      if not self.should_extract(artist, extractor, state):
        logger.debug('[artist:%s] Media extractor does not need to be run %s' % (artist.id, extractor.id()))

        continue

      logger.debug('[artist:%s] Running media extractor %s' % (artist.id, extractor.id()))

      try:
        last_updated = datetime.now()

        media.extend(extractor.extract_media(artist))
        
        if extractor.id() not in new_state['extractor_state']:
          new_state['extractor_state'][extractor.id()] = { }

        new_state['extractor_state'][extractor.id()]['last_updated'] = last_updated
      except:
        logging.exception('[artist:%s] Media extractor failed: %s' % (artist.id, extractor.id()))

    self.merge_media(artist, media)
      
    return new_state

  def should_extract(self, artist, extractor, state):
    if extractor.id() in state['extractor_state']:
      last_run = state['extractor_state'][extractor.id()]['last_updated']
      now      = datetime.now()
      
      logger.debug('[artist:%s] Media extractor %s was last run on %s, update interval is %s' % (artist.id, extractor.id(), last_run, self.update_interval))
      
      return last_run + self.update_interval < now
    else:
      logger.debug('[artist:%s] Media extractor %s has never been run.' % (artist.id, extractor.id()))

      return True

  def merge_media(self, show, media):
    for m in media:
      if isinstance(m, AudioInfo):
        show.add_or_update_audio(m.get_audio())
      elif isinstance(m, VideoInfo):
        show.add_or_update_video(m.get_video())
      else:
        raise Exception('Unsupported media type: %s' % m.__class__)

  def cleanup(self, show, state):
    pass
      
  @classmethod    
  def id(self):
    return 'media-extraction'
    
  @classmethod
  def depends_on(self):
    return ( 'resource-handler', )

class PreviewExtractorProcessor(ArtistProcessor):
  def __init__(self, settings):
    self.storage   = self.get_required_setting(settings, 'storage')
    self.rtmp_path = self.get_required_setting(settings, 'rtmp_path')

  def process(self, show, state, dependent_states):
    new_state   = state.copy()
    
    preview = self.preview_media(show)
    
    if not preview:
      logger.debug('[show:%s] No media could be previewed' % show.id)
      
      new_state = { }
    else:
      logger.debug('[show:%s] Chosen media: %s - %s' % (show.id, preview.uri, preview.title))
      
      old_preview_uri = state.get('preview_uri')
      old_name        = state.get('stored_name')
      old_version     = state.get('version', 0)
      
      if old_preview_uri == preview.uri:
        logger.debug('[show:%s] Media has already been download, skipping' % show.id)
      else:
        logger.debug('[show:%s] Media has changed, downloading: %s' % (show.id, preview.fetch_url))
        
        proto, rest = preview.fetch_url.split(':', 2)
        
        current_version = old_version + 1
        current_name    = None
        
        if proto == 'rtmp':
          media_file = TemporaryFile()

          command = (self.rtmp_path, '-r', 'rtmpe:%s' % rest, '-o', '-')

          retcode = subprocess.call(command, stdout = media_file)

          media_file.seek(0)
          
          current_name = '%s/preview/%d.flv' % (show.id, current_version)
        else:
          raise Exception('Only rtmp:// urls are supported at this time')
          
        stored_name = self.storage.save(current_name, ChunkedFile(media_file))

        local_path = self.safe_path(self.storage, current_name)
    
        new_state.update({
          'preview_uri': preview.uri,
          'version':     current_version,
          'stored_name': stored_name
        })
        
        show.preview = Preview(artist = preview.artist, title = preview.title, url = self.storage.url(current_name))

    return new_state
    
  def cleanup(self, show, state):
    old_name = state.get('stored_name')
    
    if old_name:
      self.storage.delete(old_name)
      
  def preview_media(self, show):
    preview = None

    if not show.media:
      return None
      
    for media in show.media:
      if media.fetch_url and (not preview or preview.play_count < media.play_count):
        preview = media

    return preview
    
  def safe_path(self, storage, name):
    try:
      return storage.path(name)
    except NotImplementedError:
      return None
    
  @classmethod    
  def id(self):
    return 'preview-extraction'
    
  @classmethod
  def depends_on(self):
    return ('media-extraction',)
    
#register.processor(PreviewExtractorProcessor)

extensions.register_artist_processor(MediaExtractionProcessor)