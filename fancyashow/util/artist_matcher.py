import logging
from mongoengine.queryset import DoesNotExist
from fancyashow.db.models import Artist
from fancyashow.util.lang import artist_matches, artist_mentioned, normalize

logger = logging.getLogger(__name__)

def get_artist(name):
  try:
    return Artist.objects.get(normalized_name = normalize(name))
  except DoesNotExist, e:
    return None

def get_or_create_artist(name):
  query = {
    'normalized_name': normalize(name),
    'defaults': {
      'name': name
    }
  }
  
  return Artist.objects.get_or_create(**query)

def _artists(show):
  artist_map = { }
  artist_ids = [ ]
  
  for artist_info in show.artists:
    if artist_info.artist_id:
      artist_ids.append(artist_info.artist_id)

  if artist_ids:
    artist_map = Artist.objects.in_bulk(artist_ids)
    
  return [(a, artist_map.get(a.artist_id)) for a in show.artists]

def associate_profile_with_matching_artist(show, name, profile):
  for artist_info, artist in _artists(show):      
    logger.debug('Checking if %s matches %s' % (artist_info.name, name))

    if artist_matches(artist_info.name, name) or (artist and artist_matches(artist.name, name)):
      logger.debug('Resource matches artist: %s, associating' % (artist_info.name))
      
      if not artist:
        artist = get_or_create_artist(artist_info.name)

        artist_info.artist_id = artist.id

      artist.add_profile(profile)

      artist.save()
      
      return True
    
  return False
  
def associate_profile_with_artist(artist, profile):
  logger.debug('Checking if %s matches %s' % (artist.name, name))

  if artist_matches(artist.name, name):
    logger.debug('Resource matches artist: %s, associating' % (artist_info.name))

    artist.add_profile(profile)

    artist.save()

    return True
  else:
    return False
  
def associate_video_with_matching_artist(show, video):
  for artist_info, artist in _artists(show):    
    associate = False

    if video.artist:
      logger.debug('Checking if %s matches video artist %s' % (artist_info.name, video.artist))

      associate = artist_matches(artist_info.name, video.artist) or (artist and artist_matches(artist.name, video.artist))

    if not associate:
      logger.debug('Checking if %s matches video title %s' % (artist_info.name, video.title))

      associate = artist_mentioned(artist_info.name, video.title) or (artist and artist_mentioned(artist.name, video.title))
      
    if associate:
      logger.debug('Video matches artist: %s, associating' % (artist_info.name))

      if not artist:
        artist = get_or_create_artist(artist_info.name)

        artist_info.artist_id = artist.id

      artist.add_video(video)

      artist.save()

      return True

  return False
  
def associate_video_with_artist(artist, video):
  associate = False

  if video.artist:
    logger.debug('Checking if %s matches video artist %s' % (artist.name, video.artist))

    associate = artist_matches(artist.name, video.artist)

  if not associate:
    logger.debug('Checking if %s matches video title %s' % (artist.name, video.title))

    associate = artist_mentioned(artist.name, video.title)

  if associate:
    logger.debug('Video matches artist: %s, associating' % (artist.name))

    artist.add_video(video)

    artist.save()

  return associate