from __future__ import absolute_import
import csv

class CSVParser(object):
  def __init__(self, file_path):
    self.file_path   = file_path
    self.reader      = None
    self.heading_map = None
  
  def __iter__(self):
    return self
    
  def _init_heading_map(self, line):
    self.heading_map = {}

    for i, header in enumerate(line):
      header = header.lower()
      
      if header in self.heading_map:
        raise Exception("Field '%s' defined multiple times in '%s'" % (header, self.file_path))

      self.heading_map[header] = i

  def next(self):
    if not self.reader:
      self.reader = csv.reader(open(self.file_path))
      
    for line in self.reader:
      line = [l.strip() for l in line]

      if self.heading_map == None:
        self._init_heading_map(line)
      else:
        last_offset = len(line) - 1
        record      = { }

        for header, offset in self.heading_map.iteritems():
          if offset <= last_offset:
            record[header] = line[offset]

        return record

    raise StopIteration