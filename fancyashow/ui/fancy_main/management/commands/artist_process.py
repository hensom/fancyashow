import re
from optparse                    import make_option
from datetime                    import datetime
from django.conf                 import settings

from fancyashow.ui.fancy_main.management.commands import ArtistCommand

from fancyashow.extensions           import ExtensionLoader
from fancyashow.processing           import ProcessorSetup

from fancyashow.ui.fancy_main.util   import init_logging

from pymongo.objectid import ObjectId

class Command(ArtistCommand):
  option_list = ArtistCommand.option_list + (        
        make_option('--only',
            action='store',
            dest='only',
            default=None,
            help='Only run matching processors'),
        make_option('--list',
            action='store_true',
            dest='list',
            default=None,
            help='List all processors'),
        make_option('--cleanup',
            action='store_true',
            dest='cleanup',
            default=None,
            help='Cleanup all state associated with the target processors'),
        )
        
  def handle_artists(self, artists, **options):      
    match_re = re.compile('.*')

    if options.get('only'):
      match_re = re.compile(options.get('only'))
      
    loader  = ExtensionLoader(settings.FANCY_EXTENSIONS)

    library = loader.library

    all_processors      = library.artist_processors()
    matching_processors = [p for p in all_processors if match_re.search(p.id())]
    
    if options.get('list'):
      self.list_processors(matching_processors)
    elif options.get('cleanup'):
      self.run_cleanup(library, all_processors, matching_processors, artists)
    else:
      self.run_processors(library, all_processors, matching_processors, artists)
      
  def list_processors(self, processors):
    list_processors = [ p.id() for p in processors ]

    list_processors.sort()

    for name in list_processors:
      print name
    
  def run_processors(self, loader, all_processors, matching_processors, artists):
    setup  = ProcessorSetup(loader, all_processors, settings.ARTIST_PROCESSOR_SETTINGS, restrict_to = matching_processors)

    runner = setup.runner()
    
    init_logging('processing', datetime.now())

    for artist in artists:      
      runner.process(artist)

  def run_cleanup(self, library, all_processors, matching_processors, artists):
    setup  = ProcessorSetup(library, all_processors, settings.ARTIST_PROCESSOR_SETTINGS, restrict_to = matching_processors)

    runner = setup.runner()

    for artist in artists:
      runner.cleanup(artist)
