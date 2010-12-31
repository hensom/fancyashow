import re
import logging
from datetime                    import datetime
from optparse                    import make_option
from django.core.management.base import BaseCommand
from django.conf                 import settings

from fancyashow.extensions  import ExtensionLoader
from fancyashow.parsers     import ParserError
from fancyashow.processing  import ProcessorSetup
from fancyashow.extensions.common import ResourceExtractorManager
from fancyashow.util.loader import ShowLoader

from fancyashow.ui.fancy_main.util import init_logging
from fancyashow.db.models          import ParserStat, ParseRun

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
          make_option('--only',
              action='store',
              dest='only',
              default=None,
              help='Only consider parsers whose ids match this expression'),
          make_option('--list',
              action='store_true',
              dest='list',
              default=None,
              help='Show a list of all parsers'),
        make_option('--no-process',
            action='store_true',
            dest='no-processing',
            default=False,
            help='Skip show processing'),
          make_option('--debug',
              action='store_true',
              dest='debug',
              default=None,
              help='Show a list of all parsers'),
          )

    def handle(self, **options):
      logger = logging.getLogger()

      if options.get('debug'):
        logger.setLevel(level = logging.DEBUG)
      else:
        logger.setLevel(level = logging.WARNING)
      
      match_re = re.compile('.*')
      
      if options.get('only'):
        match_re = re.compile(options.get('only'))
        
      loader  = ExtensionLoader(settings.FANCY_EXTENSIONS)

      library = loader.library

      matching_parsers = (p for p in library.show_parsers() if match_re.search(p.id()))

      if options.get('list'):
        self.list_parsers(matching_parsers)
      else:
        self.load_from_parsers(library, matching_parsers, options.get('no-processing'))

    def list_parsers(self, parsers):
        list_parsers = [ p.id() for p in parsers ]

        list_parsers.sort()

        for name in list_parsers:
          print name

    def load_from_parsers(self, library, parsers, no_processing):
      parse_run_id = datetime.now()

      init_logging('parsing', parse_run_id)

      resource_extractor = ResourceExtractorManager(library.resource_extractors())

      for parser in parsers:
        start_time = datetime.now()

        logging.info(u'Starting parse for %s' % parser.id())

        loader = ShowLoader(parser, resource_extractor)
        
        num_new, num_invalid = 0, 0
        error = None
        shows = None
        
        try:
          num_new, num_invalid, shows = loader.load_shows()
        except Exception, e:
          logging.exception(u'Unable to parse %s: %s' % (parser.id(), e))

        end_time = datetime.now()
        
        stat, created = ParserStat.objects.get_or_create(parser_id = parser.id(), defaults = {'parser_id': parser.id()})
        
        run_info = {
          'group_start_time':  parse_run_id,
          'start_time':        start_time,
          'end_time':          end_time,
          'num_valid_shows':   num_new,
          'num_invalid_shows': num_invalid,
          'error_message':     error
        }
        
        if not stat.parse_history:
          # FIXME, shouldn't mongoengine handle this?
          stat.parse_history = []
        stat.parse_history.append(ParseRun(**run_info))
                
        stat.save()
        
        if shows and not no_processing:
          self.process_shows(library, shows)
          
    def process_shows(self, library, shows):
      logging.info(u'Beginning Processing for %d Shows' % len(shows))

      setup  = ProcessorSetup(library, library.show_processors(), settings.SHOW_PROCESSOR_SETTINGS)

      runner = setup.runner()

      for show in shows:
        # FIXME There's currently some of issue in mongoengine that needs this
        # if I don't reload here then any updates to this show actually update
        # the next show
        show.reload()
        runner.process(show)