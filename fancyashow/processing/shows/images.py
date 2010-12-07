import logging
import mimetypes
import urllib2

import pytz

from PIL                   import Image as pil
from PIL                   import Image, ImageOps, ImageEnhance, ImageColor, ImageChops
from cStringIO             import StringIO

import subprocess
from tempfile import TemporaryFile, NamedTemporaryFile

from fancyashow.extensions       import ExtensionLibrary
from fancyashow.extensions.shows import ShowProcessor
from fancyashow.util.storage     import ChunkedFile

from dateutil              import parser as date_parser

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class HeadRequest(urllib2.Request):
  def get_method(self):
    return 'HEAD'

class DownloadImageProcessor(ShowProcessor):
  def __init__(self, library, settings):
    self.storage = self.get_required_setting(settings, 'storage')
    
  def default_state(self):
    return {
      'version': 0
    }

  def process(self, show, state, dependent_states):
    new_state   = state.copy()
    
    current_url = show.image_url

    old_url     = state.get('image_url')

    old_name    = state.get('stored_name')
    old_version = state.get('version', 0)
    old_mtime   = state.get('mtime')

    current_mtime, current_name, current_version = old_mtime, old_name, old_version

    if not current_url:
      logger.debug('[show:%s] No image url was found' % show.id)

      show.images.pop('full', None)
        
      new_state = { }
    elif self.do_download(show, current_url, old_url, old_mtime):
      logging.debug('[show:%s] Downloading image: %s' % (show.id, current_url))

      image_file      = urllib2.urlopen(current_url)
      
      content_type    = image_file.info().get('Content-Type')
      current_mtime   = self.last_modified(image_file)
      current_version = current_version + 1
      current_name    = '%s/images/full.%d%s' % (show.id, current_version, mimetypes.guess_extension(content_type))

      self.storage.save(current_name, ChunkedFile(image_file))
      
      local_path = self.safe_path(self.storage, current_name)

      new_state.update({
        'image_url':   current_url,
        'path':        local_path,
        'stored_name': current_name,
        'version':     current_version,
        'mtime':       current_mtime
      })
      
      show.images.update({
        'full': {
          'url':  self.storage.url(current_name),
          'path': local_path
        }
      })
      
    return new_state
    
  def cleanup(self, show, state):
    old_name = state.get('stored_name')
    
    if old_name:
      self.storage.delete(old_name)
    
  def safe_path(self, storage, name):
    try:
      return storage.path(name)
    except NotImplementedError:
      return None
      
  def last_modified(self, res):
    mtime = res.info().get('Last-Modified')
    
    if mtime:
      mtime = date_parser.parse(mtime)
      
      return mtime.astimezone(pytz.utc).replace(tzinfo = None)
    else:
      return None
    
  def do_download(self, show, current_url, old_url, old_mtime):
    if not old_mtime:
      logger.debug('[show:%s] Previous modification time for image was unknown' % show.id)
      
      return True
    elif current_url != old_url:
      logger.debug('[show:%s] Image url has changed from %s to %s' % (show.id, old_url, current_url))

      return True

    # Check last modification time
    current_mtime = None

    res = urllib2.urlopen(HeadRequest(current_url))
    
    current_mtime = self.last_modified(res)

    if not current_mtime:
      logger.debug('[show:%s] Image resource did not provide last modified time' % show.id)
  
      return True
      
    if current_mtime > old_mtime:
      logger.debug('[show:%s] Image resource has been updated (old-mtime: %s, new-mtime: %s)' % (show.id, old_mtime, current_mtime))

      return True
    else:
      logger.debug('[show:%s] Image resource is up to date' % (show.id))

      return False
    
  @classmethod    
  def id(self):
    return 'download-image'
    
  @classmethod
  def depends_on(self):
    return ()

class TransformImageBase(ShowProcessor):
  def __init__(self, library, settings):
    self.storage = self.get_required_setting(settings, 'storage')
    self.width   = self.get_required_setting(settings, 'width'  )
    self.height  = self.get_required_setting(settings, 'height' )
    
  def default_state(self):
    return {'version': 0}

  def process(self, show, state, dependent_states):
    new_state   = state.copy()

    image_info = dependent_states['download-image']

    version = image_info.get('version')
    path    = image_info.get('path')
    
    if not version:
      logging.debug('[show:%s] Image resource was not acquired. Removing any images of type: %s' % (show.id, self.image_type()))

      show.images.pop(self.image_type(), None)
      
      return { }
    
    if not path:
      raise Exception('%s requires the storage mechanism for the show image to provide a local file path' % self.id())
      
    old_version = state.get('version')
    
    if version != old_version:
      logging.debug('[show:%s] Image resource has been updated. Refreshing images of type: %s (path:%s, version:%s)' % (show.id, self.image_type(), path, version))

      stored_name, image_file = self.transform_image(show, state, dependent_states, path, version)
      
      final_name = self.storage.save(stored_name, ChunkedFile(image_file))

      new_state.update({
        'stored_name': stored_name,
        'version':     version
      })

      show.images.update({
        self.image_type(): {
          'url':  self.storage.url(final_name),
          'path': self.safe_path(self.storage, final_name)
        }
      })
      
      return new_state
    else:
      logging.debug('[show:%s] Image resource is the same. Image of type %s does not need to be refreshed' % (show.id, self.image_type()))

      return new_state

  def cleanup(self, show, state):
    old_name = state.get('stored_name')
    
    logging.debug('Removing thumbnail image: %s' % old_name)

    if old_name:
      self.storage.delete(old_name)
      
  def image_type(self):
    raise NotImplementedError()

  def safe_path(self, storage, name):
    try:
      return storage.path(name)
    except NotImplementedError:
      return None

  @classmethod
  def depends_on(self):
    return ('download-image',)
    
class ImageMagickImageProcessor(TransformImageBase):
  def transform_image(self, show, state, dependent_states, image_path, image_version):
    img = pil.open(image_path).convert('RGB')

    img = ImageOps.fit(img, (self.width, self.height), Image.ANTIALIAS, 0, (0.5,0.5))

    inp_file = TemporaryFile()
    out_file = TemporaryFile()

    img.save(inp_file, 'PNG')

    inp_file.seek(0)
    
    size = '%dx%d' % (self.width, self.height)
    
    command = ['convert', '-']
    command.extend(self.image_magick_command())
    command.append('-')
    
    retcode = subprocess.call(command, stdin = inp_file, stdout = out_file)

    out_file.seek(0)
    
    final_image = pil.open(out_file)
    final_file  = StringIO()
    
    final_image.save(final_file, 'JPEG')
    final_file.seek(0)

    file_name = '%s/images/%s.%d.jpg' % (show.id, self.image_type(), image_version)
    
    return file_name, final_file

class FeaturedImageProcessor(ImageMagickImageProcessor):
  def image_magick_command(self):
    #'-channel', 'R', '-fx', '0.854*u^2+0.537*u',
    #'-channel', 'G', '-fx', '-0.799*u^3+1.066*u^2+0.734*u',
    #'-channel', 'B', '-fx', '0.833*u+0.083',
    return ('-normalize', '-contrast', '-modulate', '100,120,100')
    
  def image_type(self):
    return 'featured'

  @classmethod    
  def id(self):
    return 'featured-image'
    
extensions.register_show_processor(DownloadImageProcessor)
extensions.register_show_processor(FeaturedImageProcessor)
