import logging
import math
import os.path
from datetime                    import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf                 import settings
import sys
import traceback

from fancyashow.ui.fancy_admin import query
from fancyashow.db.models      import Artist, SystemStat, SystemStatInfo

class Command(BaseCommand):
    def handle(self, **options):
      stats_scope = {
        'start_date': datetime.now().replace(hour = 0, minute = 0, second = 0) - timedelta(days = 30),
        'end_date':   datetime.now().replace(hour = 0, minute = 0, second = 0)
      }
      
      new_stats = Artist.objects.map_reduce(query.system_stats_map, query.system_stats_reduce, scope = stats_scope, keep_temp = False)

      SystemStat.objects.delete()
      SystemStatInfo.objects.delete()
      
      systems = { }

      for doc in new_stats:
        if doc.value['system_id'] not in systems:
          systems[doc.value['system_id']] = []

        SystemStatInfo(system_id = doc.value['system_id'], plays_per_day = doc.value['plays'], number = doc.value['num']).save()
        
        systems[doc.value['system_id']].append(doc.value['plays'])

      for system_id, plays in systems.iteritems():
        plays.sort()
        
        num_plays = len(plays)
        
        if num_plays % 2 == 1:
          median =  plays[ (num_plays + 1) / 2 - 1 ]
        else:
          lower  = plays[num_plays / 2 -1]
          upper  = plays[num_plays / 2]
          median = (float(lower + upper)) / 2

        sq_sum = 0
        
        for p in plays:
          sq_sum += (median - p) ** 2
          
        stddev = math.sqrt(sq_sum / len(plays))
        
        SystemStat(system_id = system_id, plays_per_day = median, stddev = stddev).save()