import re
import logging
from optparse                       import make_option
from decimal                        import Decimal
from django.core.management.base    import BaseCommand
from django.conf                    import settings
from django.template.defaultfilters import slugify

from fancyashow.db.models import Venue, City, Neighborhood
from fancyashow.util.csv  import CSVParser
from fancyashow.util.lang import normalize

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
         make_option('--cities',
              action='store',
              dest='cities',
              default=None,
              help='Load cities and neighborhoods from this file'),
          make_option('--venues',
              action='store',
              dest='venues',
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
      
      self.load_cities(options.get('cities'))

      self.load_venues(options.get('venues'))
      
    def load_cities(self, city_file):
      parser = CSVParser(city_file)

      City.objects().delete()
      
      city_map = { }

      for record in parser:
        LOG.debug(record)
        city, city_slug = record.get('city'), record.get('city slug')

        if city_slug not in city_map:
          city_map[city_slug] = {
            'city':          City(name = city, slug = city_slug),
            'neighborhoods': { }
          }
          
        city_map[city_slug]['neighborhoods'][record.get('neighborhood slug')] = record.get('neighborhood')
        
      for city_info in city_map.values():
        city = city_info['city']
        
        neighborhoods = [Neighborhood(name = name, slug = slug) for slug, name in city_info['neighborhoods'].iteritems()]

        neighborhoods.sort(key = lambda n: n.name)

        city.neighborhoods = neighborhoods
        
        LOG.debug("Saving neighborhoods for city: %s - %s: %s" % (city.name, city.slug, city_info['neighborhoods']))

        city.save()
      
    def load_venues(self, venue_file):      
      parser = CSVParser(venue_file)
      
      Venue.objects().delete()

      for record in parser:
        copy_over = ('name', 'url', 'address', 'city', 'neighborhood')
        
        v_map = { }
        
        if record.get('lat') and record.get('long'):
          v_map['location'] = [float(record.get('lat')), float(record.get('long'))]
        
        for field in copy_over:
          v_map[field] = record[field]
          
        v_map['normalized_name'] = normalize(v_map['name'])
        
        print v_map['name']
        
        v = Venue(**v_map)
        
        v.save()