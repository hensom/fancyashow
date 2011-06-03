import csv
import re
import logging
import os.path
from optparse                    import make_option
from django.core.management.base import BaseCommand
from django.conf                 import settings

from fancyashow.util.loader                import ShowLoader
from fancyashow.parsers.common.spreadsheet import SpreadsheetShowParser
from fancyashow.extensions                 import ExtensionLoader
from fancyashow.extensions.common          import ResourceExtractorManager
from fancyashow.processing                 import ProcessorSetup

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
          make_option('--file',
              action='store',
              dest='file',
              default=None,
              help='The file to parse'),
          make_option('--no-process',
              action='store_true',
              dest='no-processing',
              default=False,
              help='Skip show processing'),
          make_option('--debug',
              action='store_true',
              dest='debug',
              default=None,
              help='Enable debug information'),
          )
          
    def handle(self, **options):
      loader  = ExtensionLoader(settings.FANCY_EXTENSIONS)
      library = loader.library

      resource_extractor = ResourceExtractorManager(library.resource_extractors())

      logger = logging.getLogger()

      if options.get('debug'):
        logger.setLevel(level = logging.DEBUG)
      else:
        logger.setLevel(level = logging.WARNING)
        
      file_path = options.get('file')

      parser = SpreadsheetShowParser({}, resource_extractor, sheet = csv.reader(open(file_path)))
      
      loader = ShowLoader()
      
      try:
          num_new, num_invalid, shows = loader.load_shows(parser)
          
          if parser.season:
            parser.season.show_set.add_shows(shows)
            parser.season.show_set.save()
      except Exception, e:
        LOG.exception(u'Unable to parse %s: %s' % (file_path, e))
        
      if not options.get('no-processing'):
        setup  = ProcessorSetup(library, library.show_processors(), settings.SHOW_PROCESSOR_SETTINGS)

        runner = setup.runner()

        for show in shows:
          # FIXME There's currently some of issue in mongoengine that needs this
          # if I don't reload here then any updates to this show actually update
          # the next show
          show.reload()
          runner.process(show)