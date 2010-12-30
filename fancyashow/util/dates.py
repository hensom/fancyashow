from dateutil import parser as date_parser
from datetime import datetime, date
import re
import logging

logger = logging.getLogger(__name__)

TIME_MATCH        = '(?P<time>\d+(?::\d+)?\s*(?:am|pm)?)'
STRICT_TIME_MATCH = '\s*(?P<time>\d+(?::\d+)?\s*(?:am|pm))\s*'

MATCH_FLAGS = re.IGNORECASE | re.MULTILINE

TIME_RE        = re.compile(TIME_MATCH,        MATCH_FLAGS)
STRICT_TIME_RE = re.compile(STRICT_TIME_MATCH, MATCH_FLAGS)

SHOW_TIME_RE_LIST = [
  re.compile("Show.?\s*[@]?\s*%s" % TIME_MATCH, MATCH_FLAGS),
  re.compile("%s START"           % TIME_MATCH, MATCH_FLAGS) # Southpaw
]

DOOR_TIME_RE_LIST = [
  re.compile("Door[s]?.?\s*[@]?\s*%s" % TIME_MATCH, MATCH_FLAGS),
  re.compile("Door\s+time:\s*%s"      % TIME_MATCH, MATCH_FLAGS), # Southpaw
  re.compile("%s\s*Door[s]"           % TIME_MATCH, MATCH_FLAGS), # Cake Shop
]

REPLACE_RE = re.compile('[\s\n\r]+')

def sanitize_str(inp):
  return REPLACE_RE.sub(' ', inp)

def parse_date_and_time(date_str, time_str):
  if isinstance(date_str, datetime) or isinstance(date_str, date):
    date_str = date_str.strftime('%F')
  else:
    date_str = sanitize_str(date_str)

  if time_str:
    time_str = sanitize_time(sanitize_str(time_str))

  logger.debug("Parsing date(%s) and time(%s)" % (date_str, time_str))

  if time_str:
    return date_parser.parse('%s at %s' % (date_str, time_str), fuzzy = True)
  else:
    return date_parser.parse(date_str, fuzzy = True).date()

def parse_date_time(date_time_str):
  return date_parser.parse(date_time_str)
  
def sanitize_time(time_txt):
  logger.debug('Extracting time: %s' % time_txt)
  
  # Handles 730
  if ':' not in time_txt:
    suffix = ''

    # We must remove all spaces for the algorithm to work
    # Since we will basically just extract the suffix and then
    # Determine if we have hours or not by the fact that the
    # remaining time is 3 or 4 characters (ie: 7, versus 730)
    time_txt = time_txt.replace(' ', '')

    for s in ('am', 'pm'):
      if time_txt.lower().endswith(s):
        suffix   = s
        time_txt = time_txt[:-2]

        break
    
    if len(time_txt) in(3, 4):
      min_start = len(time_txt) - 2

      hours, minutes = time_txt[0:min_start], time_txt[min_start:]
    
      return '%s:%s %s' % (hours, minutes, suffix)
    else:
      return '%s %s' % (time_txt, suffix)
  else:
    return time_txt
  
def extract_time(match):
  return sanitize_time(match.group('time'))

def parse_door_time(date_str, time_str):
  for test_re in DOOR_TIME_RE_LIST:
    logger.debug('searching for door time in: %s' % time_str)
    time_match = test_re.search(time_str)
  
    if time_match:
      return parse_date_and_time(date_str, extract_time(time_match))

  return None
  
def parse_show_time(date_str, time_str):
  for test_re in SHOW_TIME_RE_LIST:
    time_match = test_re.search(time_str)
  
    if time_match:
      return parse_date_and_time(date_str, extract_time(time_match))

  return None