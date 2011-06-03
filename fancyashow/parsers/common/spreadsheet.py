import logging

from lxml.etree                   import Element

from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import dates   as date_util
from fancyashow.util              import parsing as html_util
from fancyashow.db.models         import Festival, FestivalSeason, ShowSet
from fancyashow.db.models         import Venue as VenueModel
from fancyashow.util.lang         import normalize
from mongoengine                  import Q

SECTION = 0
NAME    = 1
VALUE   = 2

LOG = logging.getLogger(__name__)

def DictForNameValue(rows):
  ret = { }
  
  for r in rows:
    ret[ r[NAME].lower().replace(' ', '-')] = r[VALUE]

  return ret

class SheetToDictByCol(object):
  def __init__(self, sheet):
    self.sheet       = sheet
    self.heading_map = None
  
  def __iter__(self):
    return self
    
  def _init_heading_map(self):
    self.heading_map = {}
    
    line = self.sheet.pop(0)

    for i, header in enumerate(line):
      header = header.lower().replace(' ', '-')
      
      if header in self.heading_map:
        raise Exception("Field '%s' defined multiple times in '%s'" % (header, self.file_path))

      self.heading_map[header] = i
      
  def _line_dict(self, line):
    line        = [l.strip() for l in line]
    last_offset = len(line) - 1
    record      = { }

    for header, offset in self.heading_map.iteritems():
      if offset <= last_offset:
        record[header] = line[offset]

    return record

  def next(self):
    try:
      if not self.heading_map:
        self._init_heading_map()

      return self._line_dict(self.sheet.pop(0))
    except IndexError, e:
      raise StopIteration

class SpreadsheetShowParser(ShowParser):        
  def __init__(self, *args, **kwargs):
    self.sheet        = kwargs.pop('sheet')
    self.parser_id    = None
    self.festival     = None
    self.season       = None
    self.show_set     = None
    self.venue        = None
    self._initialized = False

    super(SpreadsheetShowParser, self).__init__(*args, **kwargs)

  def __iter__(self):
    return self

  def next(self):
    self._init()

    for record in self.shows:
      return self._trans_record(self._clean_record(record))

    raise StopIteration
    
  def _init(self):
    if self._initialized:
      return
      
    self._initialized = True

    sections = {
      'parser':   [],
      'festival': [],
      'venue':    [],
      'shows':    []
    }
    
    current_section = None

    for row in self.sheet:
      # Skip empty rows
      if not any(len(d) > 0 for d in row):
        continue
        
      row = [unicode(r, 'utf-8', 'ignore') for r in row]

      if row[SECTION]:
        current_section = row[SECTION].lower()
        
        if not current_section in sections:
          raise Exception("Unsupported section: %s" % row[SECTION])
      else:
        if current_section:
          sections[current_section].append(row)
        else:
          raise Exception("Data row seen before any valid section")

    festival, season = self._festival(sections.get('festival'))
    
    self.festival  = festival
    self.season    = season
    self.parser_id = self._parser_id(sections.get('parser'))
    self.venue     = self._venue(sections.get('venue'))
    self.shows     = SheetToDictByCol(sections.get('shows'))
    
  def _parser_id(self, rows):
    for r in rows:
      if r[NAME].lower() == 'id' and r[VALUE]:
        return r[VALUE]

    raise Exception("Unable to locate field ID in section Parser")
    
  def _festival(self, rows):
    if len(rows) == 0:
      return None
      
    info = DictForNameValue(rows)
    
    for r in ('name', 'merge-key', 'season-merge-key', 'season-start-date', 'season-end-date'):
      if info.get(r) == None:
        raise Exception("Festival lacks required field: %s" % r)

    festival_query  = Q(merge_key = info['merge-key'])
    festival_kwargs = {'name': info['name'], 'merge_key': info['merge-key']}
    
    festival, created = Festival.objects.get_or_create(festival_query, defaults = festival_kwargs)
    
    season_query  = Q(festival_id = festival.id, merge_key = info['season-merge-key'])
    season_kwargs = {'festival_id': festival.id,
                     'merge_key':   info['season-merge-key'],
                     'start_date':  date_util.parse_date_time(info['season-start-date']),
                     'end_date':    date_util.parse_date_time(info['season-end-date'])
                    }

    season, created = FestivalSeason.objects.get_or_create(season_query, defaults = season_kwargs)
      
    return festival, season

  def _venue(self, rows):
    if len(rows) == 0:
      return None

    info = DictForNameValue(rows)

    for r in ('name', 'url'):
      if not info.get(r):
        raise Exception("Venue lacks required field: %s" % r)

    v_kwargs = { }

    for field in ('name', 'url', 'address', 'city', 'neighborhood'):
      v_kwargs[field] = info[field]

    if info.get('lat') and info.get('long'):
      v_kwargs['location'] = [float(info.get('lat')), float(info.get('long'))]

    v_kwargs['normalized_name'] = normalize(v_kwargs['name'])
    
    venue, created = VenueModel.objects.get_or_create(Q(url = v_kwargs['url']), defaults = v_kwargs)
    
    return venue

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
    
    show.venue     = Venue(record.get('venue-name'), record.get('venue-url'))
    show.title     = record.get('title')
    show.merge_key = record.get('merge-key')
    
    performers = []
    
    if record.get('performers'):
      for performer in record['performers'].split(','):
        performers.append(Performer(performer.strip()))
        
    if record.get('tags'):
      show.tags = [t.strip() for t in record['tags'].split(',')]
      
    date_txt = record.get('show-date')
    
    if not date_txt:
      raise Exception('Show Date is required')
    else:
      show.date = date_util.parse_date_time(date_txt)
      
    if performers:
      show.performers = performers
      
    if record.get('show-time'):
      show.show_time = date_util.parse_date_and_time(date_txt, record.get('show-time'))

    if record.get('door-time'):
      show.show_time = date_util.parse_date_and_time(date_txt, record.get('door-time'))

    show.resources.show_url      = record.get('show-url')
    show.resources.image_url     = record.get('image-url')
    show.resources.resource_uris = self.resource_extractor.extract_resources(self._create_resource_doc(record))
      
    return show
    
  def _create_resource_doc(self, record):
    root = Element('div')

    for link in record.get('links', '').split(','):
      root.append(Element('a', href = link))
      
    return root
  
  def id(self):
    self._init()

    return self.parser_id