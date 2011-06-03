# encoding=UTF-8
import logging
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.parsers.common.lastfm import LastFMParser
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util
import re

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()


class WebsterHall(LastFMParser):
  def venue_id(self):
    return 8778811

  def venue(self):
    return Venue('Webster Hall', "http://www.websterhall.com/")

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.webster-hall'

class WebsterHallStudio(LastFMParser):
  def venue_id(self):
    return 9004895

  def venue(self):
    return Venue('The Studio at Webster Hall', "http://www.websterhall.com/thestudio/")

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.webster-hall-studio'

extensions.register_show_parser(WebsterHall)                                               
extensions.register_show_parser(WebsterHallStudio)