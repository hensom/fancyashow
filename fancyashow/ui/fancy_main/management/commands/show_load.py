import re
import logging
import os.path
from optparse                    import make_option
from django.core.management.base import BaseCommand
from django.conf                 import settings
import sys
import traceback

from fancyashow.parsers         import ParserLoader, ParserError
from fancyashow.parsers.generic import FileShowParserClass
from fancyashow.resources       import ResourceExtractorLoader, ResourceExtractorManager

from fancyashow.ui.fancy_main.loader import ShowLoader

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
          make_option('--file',
              action='store',
              dest='file',
              default=None,
              help='Parse this file'),
          make_option('--debug',
              action='store_true',
              dest='debug',
              default=None,
              help='Show a list of all parsers'),
          )
          
    def handle(self, **options):
      resource_loader    = ResourceExtractorLoader(settings.RESOURCE_EXTRACTOR_PACKAGES)

      resource_extractor = ResourceExtractorManager(resource_loader.extractors())

      logger = logging.getLogger()

      if options.get('debug'):
        logger.setLevel(level = logging.DEBUG)
      else:
        logger.setLevel(level = logging.WARNING)
        
      file_path = options.get('file')
      
      directory, file_name = os.path.split(file_path)
      
      parser_id, ext       = os.path.splitext(file_name)
      
      parser = FileShowParserClass(parser_id, file_path)
      
      loader = ShowLoader(parser, resource_extractor)
      
      loader.load_shows()