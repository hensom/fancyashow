from lxml.etree                   import Element

from fancyashow.parsers           import ShowParser
from fancyashow.parsers.util      import CSVParser
from fancyashow.parsers.models.v1 import Venue, Performer, Show
from fancyashow.parsers           import date_util, html_util

def FileShowParserClass(parser_id, file_path):
  class FileShowParser(ShowParser):        
    def __init__(self, *args, **kwargs):
      super(FileShowParser, self).__init__(*args, **kwargs)

      self.parser = CSVParser(file_path)
    def __iter__(self):
      return self

    def next(self):
      for record in self.parser:
        show = self._trans_record(self._clean_record(record))
        
        print show.performers[0]
        
        return show
        
      raise StopIteration
      
    def _clean_record(self, record):
      remove_keys = []
      
      for key, value in record.iteritems():
        if value == '':
          remove_keys.append(key)
          
      for k in remove_keys:
        del record[k]
        
      return record

    def _trans_record(self, record):
      show = Show()
      
      show.venue     = Venue(record.get('venue name'), record.get('venue url'))
      show.title     = record.get('title')
      show.merge_key = record.get('merge key')
      
      performers = []
      
      for performer in record.get('performers', '').split(','):
        performers.append(Performer(performer.strip()))
        
      date_txt = record.get('show date')
      
      if not date_txt:
        raise Exception('Show Date is required')
        
      if performers:
        show.performers = performers
        
      if record.get('show time'):
        show.show_time = date_util.parse_date_and_time(date_txt, record.get('show time'))

      if record.get('door time'):
        show.show_time = date_util.parse_date_and_time(date_txt, record.get('door time'))

      free = record.get('free', 'no')

      if free.lower() == 'no':
        free = False
      elif free.lower() == 'yes':
        free = True
      else:
        raise Exception("Invalid value for free: %s in %s" % (free, record))
        
      show.free = free
      show.resources.show_url      = record.get('show url')
      show.resources.image_url     = record.get('image url')
      show.resources.resource_uris = self.resource_extractor.extract_resources(self._create_resource_doc(record))
        
      return show
      
    def _create_resource_doc(self, record):
      root = Element('div')

      for link in record.get('links', '').split(','):
        root.append(Element('a', href = link))
        
      return root

    @classmethod    
    def id(self):
      return parser_id

  return FileShowParser
