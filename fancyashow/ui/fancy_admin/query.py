def transform_exec_js(document, query, *exec_js_args):
  query = query.exec_js(*exec_js_args)

  return [document._from_son(i) for i in query]
  
  
def show_has_resource(resource):
  return """
  function() {
    var shows [];
  
    function has_resource(show) {
      for(var i = 0; i < show.parsed_resources.length; i++) {
        if(show.parsed_resources[i].indexOf('%s') != -1) {
          return true;
        }
      }
    
      return false;
    }

    db[collection].find(query).forEach(function(show) {
      if(has_resource(show)) {
        shows.push(show);
      }
    });
  
    return shows;
  }
  """ % resource

def show_has_resource_state(state):
  return """
  function() {
    var shows = [];
  
    function has_unhandled(show) {
      var proc_state = show[~processor_state]['resource-handler'];
  
      for(var resource in proc_state) {
        var resource_state = proc_state[resource];

        for(var handler_id in resource_state) {
          if(resource_state[handler_id].state == %(UNHANDLED_STATE)s) {
             return true;
          }
        }
      }
    
      return false;
    }
  
    db[collection].find(query).forEach(function(show) {
      if(has_unhandled(show)) {
        shows.push(show);
      }
    });
  
    return shows;
  }
  """ % {'UNHANDLED_STATE': state}
  
def artist_is_suspect():
  return """
  function() {
  
    var artists = [];
    
    db[collection].find(query).forEach(function(artist) {
      if(artist[~resources].length == 0) {
        artists.push(artist);
      }
    });
  
    return artists;
  }
  """

sum_by_key = """
function(k, vals) {
  var sum = 0;

  for(var i = 0; i < vals.length; i++) {
    sum += vals[i];
  }

  return sum;
}
"""

association_map = """
function() {
  var num_artists    = this.artists.length;
  var num_associated = 0;

  for(var i = 0; i < num_artists; i++) {
    var artist = this.artists[i];

    if(artist.artist_id) {
      num_associated++;
    } else if(i == 0) {
      emit('no_headliner', 1);
    }
  }

  if(num_artists > 0) {
    if(num_associated == num_artists) {
      emit('all', 1);
    } else if(num_associated == 0) {
      emit('none', 1);
    } else {
      emit('some', 1);    
    }
  }
}
"""

association_reduce = sum_by_key

profile_map = """
function() {
  var num_profiles = this.profiles.length;

  for(var i = 0; i < num_profiles; i++) {
    emit(this.profiles[i].system_id, 1);
  }
}
"""

profile_reduce = sum_by_key

system_stats_map = """
function() {
  function sample_range(history) {
    var start = null;
    var end   = null;

    // Stats are sorted by increasing time
    for(var i = 0; i < history.length; i++) {
      var stat = history[i];

      if(stat.sample_date < start_date) {
        start = stat;
      }

      if(stat.sample_date >= start_date && stat.sample_date <= end_date) {
        if(!start) {
          start = stat;
        } else {
          end = stat;
        }
      }

      // Find the latest sample
      if(stat.sample_date > end_date) {
        end = stat;

        break;
      }
    }
       
    return {"start": start, "end": end};
  }
  
  function plays_per_day(history) {
    var range = sample_range(history);
    
    if(!(range.start && range.end)) {
      return null;
    } else if(range.end.number_of_plays == null || range.start.number_of_plays == null) {
      return null;
    }

    var range_seconds = (range.end.sample_date.getTime() - range.start.sample_date.getTime()) / 1000;
    
    if(range_seconds <= 0) {
      return null;
    }

    var num_days = range_seconds / 60.0 / 60 / 24;

    return 1.0 * (range.end.number_of_plays - range.start.number_of_plays) / num_days;
  }

  for(var i = 0; i < this.audio.length; i++) {
    var audio = this.audio[i];
    var plays = plays_per_day(audio.stats.history);

    if(plays != null && (plays > min_sample && plays < max_sample)) {
      emit(audio.system_id + '/' + plays, {'system_id': audio.system_id, 'plays': plays, 'num': 1});
    }
  }

  for(var i = 0; i < this.videos.length; i++) {
    var video = this.videos[i];
    var plays = plays_per_day(video.stats.history);
    
    if(plays != null && (plays > min_sample && plays < max_sample)) {
      emit(video.system_id + '/' + plays, {'system_id': video.system_id, 'plays': plays, 'num': 1});
    }
  }
}
"""

system_stats_reduce = """
function(k, vals) {
  var ret = vals[0];
  
  for(var i = 1; i < vals.length; i++) {    
    ret.num += vals[i].num;
  }
  
  return ret;
}
"""

system_stats_finalize = """
function(k, val) {
  if(val.num > 0) {
    var mean = val.sum / val.num;
    
    var sq_sum = 0;
    
    for(var i in val.plays) {
      sq_sum += Math.pow(mean - val.plays[i], 2);
    }
    
    return {'mean': mean, 'stddev': Math.sqrt(sq_sum / val.num), 'plays': val.plays};
  } else {
    return {'mean': start_date, 'stddev': null};
  }
}
"""

media_map = """
function() {
  var artistCounted = { };

  function emit_stats(m) {
    var stats  = {
      'number_of_artists':  artistCounted[m.system_id] ? 0 : 1,
      'number_of_plays':    m.stats.number_of_plays,
      'number_of_comments': m.stats.number_of_comments,
      'number_of_likes':    m.stats.number_of_likes
    };
    
    artistCounted[m.system_id] = true;
    
    emit(m.system_id, stats);
  }
  
  for(var i = 0; i < this.audio.length; i++) {
    emit_stats(this.audio[i]);
  }

  for(var i = 0; i < this.videos.length; i++) {
    emit_stats(this.videos[i]);
  }
}
"""

media_reduce = """
function(k, vals) {
  var keys    = ['number_of_artists', 'number_of_plays', 'number_of_comments', 'number_of_likes'];
  var summary = { };
  
  for(var i = 0; i < keys.length; i++) {
    summary[keys[i]] = 0;
  }
  
  for(var i = 0; i < vals.length; i++) {
    for(var j = 0; j < keys.length; j++) {
      summary[keys[j]] += vals[i][keys[j]];
    }
  }
  
  return summary;
}
"""

show_lacks_headliner = """
function() {
  var shows = [];

  db[collection].find(query).forEach(function(show) {
    if(show[~artists].length > 0 && !show[~artists][0].artist_id) {
      shows.push(show);
    }
  });

  return shows;
}
"""