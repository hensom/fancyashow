import logging
from optparse                    import make_option
from dateutil                    import parser as date_parser
from django.core.management.base import BaseCommand

from fancyashow.db.models        import Artist, Show

from pymongo.objectid import ObjectId

class ShowCommand(BaseCommand):
  option_list = BaseCommand.option_list + (
        make_option('--show',
            action='store',
            dest='show',
            default=None,
            help='Only process the show with this id'),
        make_option('--date',
            action='store',
            dest='date',
            default=None,
            help='Only process shows that occurred on this date'),
        make_option('--parser',
            action='store',
            dest='parser',
            default=None,
            help='Only process shows from matching parsers'),
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=None,
            help='Enable debug output')
        )
        
  def handle(self, **options):
    logger = logging.getLogger()

    if options.get('debug'):
      logger.setLevel(level = logging.DEBUG)
    else:
      logger.setLevel(level = logging.WARNING)
    
    show_filter = { }
    
    if options.get('show'):
      show_filter['id'] = ObjectId(options.get('show'))
    
    if options.get('date'):
      show_filter['date'] = date_parser.parse(options.get('date'))
      
    if options.get('parser'):
      show_filter['parse_meta__parser_id__icontains'] = options.get('parser')
      
    shows = Show.objects.filter(**show_filter)
      
    self.handle_shows(shows, **options)
    
  def handle_shows(self, shows, **options):
    raise NotImplementedError()
    
class ArtistCommand(BaseCommand):
  option_list = BaseCommand.option_list + (
        make_option('--id',
            action='store',
            dest='id',
            default=None,
            help='Only process the artist with this id'),
        make_option('--name',
            action='store',
            dest='name',
            default=None,
            help='Only process artist with this name'),
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=None,
            help='Enable debug output')
        )

  def handle(self, **options):
    logger = logging.getLogger()

    if options.get('debug'):
      logger.setLevel(level = logging.DEBUG)
    else:
      logger.setLevel(level = logging.WARNING)

    artist_filter = { }

    if options.get('id'):
      artist_filter['id'] = ObjectId(options.get('id'))

    if options.get('name'):
      artist_filter['name__icontains'] = options.get('name')

    artists = Artist.objects.filter(**artist_filter)

    self.handle_artists(artists, **options)

  def handle_artists(self, artists, **options):
    raise NotImplementedError()
