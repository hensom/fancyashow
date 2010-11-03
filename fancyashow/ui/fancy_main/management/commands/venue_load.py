import re
import logging
from optparse                    import make_option
from decimal                     import Decimal
from django.core.management.base import BaseCommand
from django.conf                 import settings

from fancyashow.db.models import Venue
from fancyashow.util.csv  import CSVParser
from fancyashow.util.lang import normalize

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
          make_option('--file',
              action='store',
              dest='file',
              default=None,
              help='Load venues from this file'),
          make_option('--debug',
              action='store_true',
              dest='debug',
              default=None,
              help='Enable debugging output'),
          )
          
    def handle(self, **options):
      logger = logging.getLogger()

      if options.get('debug'):
        logger.setLevel(level = logging.DEBUG)
      else:
        logger.setLevel(level = logging.WARNING)
        
      venue_file = options.get('file')
      
      parser = CSVParser(venue_file)
      
      Venue.objects().delete()

      for record in parser:
        copy_over = ('name', 'url', 'address', 'city')
        
        #if record.get('lat') and record.get('long'):
        #  v_map['geo'] = GeoPoint(lat = float(record.get('lat')), long = float(record.get('long')))
        
        v_map = { }
        
        for field in copy_over:
          v_map[field] = record[field]
          
        v_map['normalized_name'] = normalize(v_map['name'])
        
        v = Venue(**v_map)
        
        v.save()