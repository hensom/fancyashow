import                           logging
from datetime             import datetime, timedelta
from mongoengine          import Document, EmbeddedDocument
from mongoengine          import IntField, FloatField, DateTimeField, ListField
from mongoengine          import DictField, BooleanField, URLField
from mongoengine          import EmbeddedDocumentField, ObjectIdField, GeoPointField
from mongoengine.base     import ValidationError
from fancyashow.db.fields import StringField
from django.template.defaultfilters import slugify

logger = logging.getLogger(__name__)

class SystemStat(Document):
  system_id     = StringField(required = True)
  plays_per_day = FloatField()
  stddev        = FloatField()
  
class SystemStatInfo(Document):
  system_id     = StringField(required = True)
  plays_per_day = FloatField()
  number        = IntField()

class ParseRun(EmbeddedDocument):
  group_start_time  = DateTimeField(required = True)
  start_time        = DateTimeField(required = True)
  end_time          = DateTimeField(required = True)
  num_valid_shows   = IntField(required = True, default = 0)
  num_invalid_shows = IntField(required = True, default = 0)
  error_message     = StringField()

class ParserStat(Document):
  parser_id     = StringField(required = True, unique = True)
  parse_history = ListField(EmbeddedDocumentField(ParseRun))
  
  def last_parse(self):
    return self.parse_history[-1]
  
class MediaStatsHistory(EmbeddedDocument):
  number_of_plays    = IntField()
  number_of_comments = IntField()
  number_of_likes    = IntField()
  rating             = FloatField()
  num_raters         = IntField()
  sample_date        = DateTimeField(required = True)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return '(plays: %s, comments: %s, likes: %s, rating: %s - %s)' % (self.number_of_plays, self.number_of_comments, self.number_of_likes, self.rating, self.sample_date)
  
class MediaReport(object):
  start_date         = None
  end_date           = None
  number_of_plays    = None
  number_of_comments = None
  number_of_likes    = None
  
  def __init__(self, start_date, end_date):
    self.start_date = start_date
    self.end_date   = end_date

  def __str__(self):
    return unicode(self).encode('utf-8')
      
  def __unicode__(self):
    return '(plays: %s, comments: %s, likes: %s - per day from %s to %s)' % (self.number_of_plays, self.number_of_comments, self.number_of_likes, self.start_date, self.end_date)
  
class MediaStats(EmbeddedDocument):
  number_of_plays    = IntField()
  number_of_comments = IntField()
  number_of_likes    = IntField()
  rating             = IntField()
  history            = ListField(EmbeddedDocumentField(MediaStatsHistory), default = lambda: [])

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):  
    return '(plays: %s, comments: %s, likes:%s, rating: %s)' % (self.number_of_plays, self.number_of_comments, self.number_of_likes, self.rating)

  def add_stats(self, stats):
    self.history.extend(stats)
    self.history.sort(key = lambda h: h.sample_date)
    
    if self.history:
      last_stat = self.history[-1]

      self.number_of_plays    = last_stat.number_of_plays
      self.number_of_comments = last_stat.number_of_comments
      self.number_of_likes    = last_stat.number_of_likes
      self.rating             = last_stat.rating
      
  def last_sample(self):
    return self.history[-1]

  def sample_range(self, start_date, end_date):
    start = None
    end   = None

    # Stats are sorted by increasing time
    for stat in self.history:
      if stat.sample_date < start_date:
        start = stat

      if stat.sample_date >= start_date and stat.sample_date <= end_date:
        if not start:
          start = stat
        else:
          end = stat

      # Find the latest sample
      if stat.sample_date > end_date:
        end = stat

        break
         
    return start, end
    
  def stats_last_30_days(self):
    today          = datetime.now()
    three_days_ago = (today - timedelta(days = 30)).replace(hour = 0, minute = 0, second = 0)
    
    return self.stats_over(three_days_ago, today)

  def stats_over(self, start_date, end_date):
    start, end = self.sample_range(start_date, end_date)

    if not (start and end):
      return MediaReport(start_date, end_date)
      
    def avg(start, end, prop, sample_period):
      start_val = getattr(start, prop)
      end_val   = getattr(end,   prop)
      
      if sample_period == 0:
        return None
      
      if start_val != None and end_val != None:
        return int(1.0 * (end_val - start_val) / sample_period)
      else:
        return None

    time_range = end.sample_date - start.sample_date

    num_days   = time_range.days + (time_range.seconds / 60.0 / 60 / 24)
    
    report     = MediaReport(start_date, end_date) 

    report.number_of_plays    = avg(start, end, 'number_of_plays',    num_days)
    report.number_of_comments = avg(start, end, 'number_of_comments', num_days)
    report.number_of_likes    = avg(start, end, 'number_of_likes',    num_days)
    
    return report

class Media(EmbeddedDocument):
  system_id     = StringField(required = True)
  media_id      = StringField(required = True)
  source_id     = StringField(required = True)
  artist        = StringField()
  title         = StringField(required = True)
  upload_date   = DateTimeField()
  creation_date = DateTimeField(required = True, default = lambda: datetime.now())
  stats         = EmbeddedDocumentField(MediaStats, required = True, default = lambda: MediaStats())
  
  def merge(self, media):
    if not self.equivalent_to(media):
      raise Exception('%s and %s are not the same piece of media, unable to merge' % (self.uri, media.uri))
      
    self.artist = media.artist
    self.title  = media.title

    self.stats.add_stats(media.stats.history)
  
  def equivalent_to(self, media):
    return media.system_id == self.system_id and media.media_id == self.media_id

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return '%s - %s' % (self.system_id, self.media_id)

class Audio(Media):
  pass

class Video(Media):
  pass
  
class ArtistProfile(EmbeddedDocument):
  system_id     = StringField(required = True)
  profile_id    = StringField(required = True)
  source_id     = StringField(required = True)
  creation_date = DateTimeField(required = True, default = lambda: datetime.now())
  url           = URLField(required = True)

  def equivalent_to(self, profile):
    return profile.system_id == self.system_id and profile.profile_id == self.profile_id

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return '%s - %s' % (self.system_id, self.profile_id)

class Artist(Document):
  name              = StringField(required = True)
  normalized_name   = StringField(required = True, unique = True)
  profiles          = ListField(EmbeddedDocumentField(ArtistProfile), default = lambda: [])
  audio             = ListField(EmbeddedDocumentField(Audio),         default = lambda: [])
  videos            = ListField(EmbeddedDocumentField(Video),         default = lambda: [])

  processor_state   = DictField(default = lambda: {}, required = True)
  
  creation_date     = DateTimeField(required = True, default = lambda: datetime.now())
  
  rank              = FloatField()
  
  def slug(self):
    return slugify(self.name)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return self.name

  @property
  def id_str(self):
    return str(self.id)

  @property
  def media(self):
    media = []
    
    media.extend(self.audio)
    media.extend(self.videos)

    return media
    
  def get_profiles(self, system_id):
    return [p for p in self.profiles if p.system_id == system_id]
    
  def add_profile(self, profile):    
    found = False

    for i in self.profiles:
      if profile.equivalent_to(i):
        found = True
      
    if found:
      logger.debug('[artist:%s] Already has profile: %s' % (self.id, profile))

      return False
    else:
      logger.debug('[artist:%s] Adding new profile: %s' % (self.id, profile))

      self.profiles.append(profile)

      return True
      
  def add_or_update_audio(self, audio, update = True):
    found = False
    
    for a in self.audio:
      if audio.equivalent_to(a):
        if update:
          a.merge(audio)

        found = True

    if found:
      return False
    else:
      self.audio.append(audio)

      return True
      
  def add_audio(self, audio):
    return self.add_or_update_audio(audio, update = False)

  def get_videos(self, system_id):
    return [v for v in self.videos if v.system_id == system_id]

  def add_or_update_video(self, video, update = True):
    found = False
    
    logger.debug('Searching for video: %s' % video)

    for v in self.videos:
      if video.equivalent_to(v):
        if update:
          v.merge(video)

        found = True

    if found:
      return False
    else:
      self.videos.append(video)

      return True

  def add_video(self, video):
    return self.add_or_update_video(video, update = False)

class Neighborhood(EmbeddedDocument):
  name = StringField(required = True)
  slug = StringField(required = True, unique = True)

class City(Document):
  name          = StringField(required = True)
  slug          = StringField(required = True, unique = True)
  neighborhoods = ListField(EmbeddedDocumentField(Neighborhood), default = lambda: [])

class Venue(Document):
  name            = StringField(required = True)
  slug            = StringField(required = True, unique = True)
  url             = URLField()
  address         = StringField()
  city            = StringField()
  neighborhood    = StringField()
  location        = GeoPointField()

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return self.name
    
  def save(self):
    self.slug = slugify(self.name)
    
    return super(Venue, self).save()

class VenueInfo(EmbeddedDocument):
  name = StringField(required = True)
  url  = URLField()
  
  def slug(self):
    return slugify(self.name)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return self.name

class ArtistInfo(EmbeddedDocument):
  name       = StringField(required = True)
  headliner  = BooleanField(required = True, default = False)
  start_time = StringField()
  artist_id  = ObjectIdField()

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return self.name
    
class ParseMeta(EmbeddedDocument):
  parser_id = StringField(required = True)
  merge_key = StringField()

class Show(Document):
  title            = StringField()
  artists          = ListField(EmbeddedDocumentField(ArtistInfo))
  artist_ids       = ListField(ObjectIdField(), default = lambda: [])

  date             = DateTimeField(required = True)
  show_time        = DateTimeField()
  door_time        = DateTimeField()
  
  url              = URLField()
  image_url        = URLField()
  
  parsed_resources = ListField(StringField(), default = lambda: [])

  rank             = FloatField()

  venue            = EmbeddedDocumentField(VenueInfo, required = True)
  soldout          = BooleanField(default = False, required = True)

  visible          = BooleanField(default = True, required = True)
  
  parse_meta       = EmbeddedDocumentField(ParseMeta, required = True)
  processor_state  = DictField(default = lambda: {}, required = True)
  images           = DictField(default = lambda: {}, required = True)

  creation_date    = DateTimeField(required = True, default = lambda: datetime.now())

  def __unicode__(self):
    return '%s on %s' % (self.title or self.artists[0].name, self.date.strftime('%F'))
  
  def slug(self):
    if self.title:
      return slugify(self.title)
    else:
      return slugify(self.artists[0].name)

  @property
  def id_str(self):
    return str(self.id)

  def validate(self):
    super(Show, self).validate()
    
    if not self.title and not self.artists:
      raise ValidationError('A show must have a title or list of artists')
      
  def related_artists(self):
    artist_ids = []
    
    for a in self.artists:
      if a.artist_id != None:
        artist_ids.append(a.artist_id)
        
    if artist_ids:
      return Artist.objects.in_bulk(artist_ids)
    else:
      return {}
