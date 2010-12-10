from datetime                   import datetime, timedelta
from django.core.paginator      import Paginator
from django.http                import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.shortcuts           import render_to_response
from django.utils               import simplejson
from django.core.urlresolvers   import reverse
from django.conf                import settings
from datetime                   import datetime, timedelta
from fancyashow.processing.common import RESOURCE_HANDLED, RESOURCE_HANDLING_FAILED, RESOURCE_NOT_HANDLED
from fancyashow.db.models       import Show, VenueInfo, ArtistInfo, Artist, ParserStat, SystemStat, SystemStatInfo, Venue

from fancyashow.ui.fancy_admin         import query
from fancyashow.ui.fancy_admin.query   import transform_exec_js, show_has_resource_state, artist_is_suspect, show_lacks_headliner, show_has_resource
from fancyashow.ui.fancy_main.filters  import SearchFilter, DateFilter
from fancyashow.ui.fancy_admin.forms   import AdminShowFilterForm, AdminArtistFilterForm
from fancyashow.ui.fancy_admin.forms   import ShowVenueForm, ShowForm, ArtistForm, ArtistInfoForm, ProfileForm, ArtistAssociationForm
from fancyashow.ui.fancy_admin.forms   import initial_for_instance
from password_required.decorators      import password_required

@password_required
def summary(request):
  collections = {
    'shows':   Show.objects.count(),
    'artists': Artist.objects.count()
  }
  
  associations  = { }
  profiles      = [ ]
  media_summary = [ ]
  
  for doc in Show.objects.map_reduce(query.association_map, query.association_reduce):
    associations[doc.key] = doc.value

  for doc in Artist.objects.map_reduce(query.profile_map, query.profile_reduce):
    profiles.append({'system_id': doc.key, 'number': doc.value})

  profiles.sort(key = lambda x: x['number'], reverse = True)
  
  system_stats = { }
  
  stats_scope = {
    'start_date': datetime.now().replace(hour = 0, minute = 0, second = 0) - timedelta(days = 30),
    'end_date':   datetime.now().replace(hour = 0, minute = 0, second = 0)
  }
  
  for stat in SystemStat.objects():
    system_stats[ stat.system_id ] = {
      'mean':   stat.plays_per_day,
      'stddev': stat.stddev
    }

  for doc in Artist.objects.map_reduce(query.media_map, query.media_reduce):
    summary = {'media_type': doc.key, 'stats': doc.value}
    
    summary['stats'].update(system_stats.get(doc.key, {}))

    media_summary.append(summary)
  
  media_summary.sort(key = lambda x: x['stats']['number_of_plays'], reverse = True)

  context = {
    'collections':        collections,
    'artist_association': associations,
    'profiles':           profiles,
    'media_summary':      media_summary
  }

  return render_to_response('fancy_admin/summary.html', context)

@password_required
def shows(request):
  page_number = request.GET.get('page', 1)
  
  today   = datetime.now().date()
  
  initial = {
    'show_range': 'on',
    'show_date':  today 
  }
  
  data = None
  
  if request.GET.get('search'):
    data = request.GET

  show_form = AdminShowFilterForm(data = data, initial = initial)
  
  if data and not show_form.is_valid():
    raise Exception('Invalid admin filters')
    
  if data:
    filters = show_form.cleaned_data
  else:
    filters = initial
  
  shows = Show.objects()
  
  if filters.get('query'):
    f = SearchFilter(filters.get('query'), 'title', 'venue__name', 'parse_meta__parser_id')
    
    shows = f.apply(shows)

  if filters.get('show_date'):
    range_map = {
      'on':      None,
      'before': 'lt',
      'after':  'gt'
    }
    range_method = range_map[filters.get('show_range')]

    f = DateFilter(filters.get('show_date'), 'date', range_method)
    
    shows = f.apply(shows)

  if filters.get('is_hidden'):
    shows = shows.filter(visible = False)
    
  if filters.get('no_image'):
    shows = shows.filter(image_url = None)

  if filters.get('restrict') == 'handling_failed':
    shows = transform_exec_js(Show, shows, show_has_resource_state(RESOURCE_HANDLING_FAILED))
  elif filters.get('restrict') == 'not_handled':
    shows = transform_exec_js(Show, shows, show_has_resource_state(RESOURCE_NOT_HANDLED))
  elif filters.get('restrict') == 'no_headliner':
    shows = transform_exec_js(Show, shows, show_lacks_headliner)
    
  if filters.get('resource') not in ('', None):
    shows = transform_exec_js(Show, shows, show_has_resource(filters.get('resource')))
    
  shows = shows.order_by('date', '-rank')
  
  paginator = Paginator(shows, 100)
  
  page  = paginator.page(page_number)

  shows = list(page.object_list)

  today          = datetime.today().replace(hour = 0, minute = 0, second = 0)
  three_days_ago = today - timedelta(days = 3)

  for show in shows:
    artist_map = show.related_artists()

    for a in show.artists:
      a.full = artist_map.get(a.artist_id)

  context = {
    'show_form': show_form,
    'shows':     shows,
    'page':      page,
    'paginator': paginator
  }

  return render_to_response('fancy_admin/shows.html', context)
  
@password_required
def artists(request):
  page_number = request.GET.get('page', 1)

  artist_form = AdminArtistFilterForm(data = request.GET)

  if not artist_form.is_valid():
    raise Exception('Invalid admin filters')

  filters = artist_form.cleaned_data

  artists = Artist.objects()
  artists = artists.order_by('name')

  if filters.get('query'):
    f = SearchFilter(filters.get('query'), 'name')
    
    artists = f.apply(artists)
    
  if filters.get('suspect'):
    artists = transform_exec_js(Artist, artists, artist_is_suspect())
    
  paginator = Paginator(artists, 10000)

  page    = paginator.page(page_number)

  artists = []
  
  today            = datetime.now().replace(hour = 0, minute = 0, second = 0)
  yesterday        = today - timedelta(days = 1)
  three_days_ago   = today - timedelta(days = 3)
  thirty_days_ago  = today - timedelta(days = 30)
  
  periods = (
    ('last_30_days',    thirty_days_ago,  yesterday),
#    ('last_three_days', three_days_ago,   yesterday),
#    ('yesterday',       yesterday,        today)
  )
  
  for artist in list(page.object_list):
    stats    = { }
    profiles = { }
    
    artists.append({'artist': artist, 'stats': stats, 'profiles': profiles})
    
    last_sum = None
    
    for profile in artist.profiles:
      profiles[profile.system_id] = True

    for period, start, end in periods:
      media_info = [a.stats.stats_over(start, end).number_of_plays or 0 for a in artist.audio]
  
      media_info.sort(reverse = True)
  
      if len(media_info[0:3]) > 0:
        stats[period] = sum(media_info[0:3])/len(media_info[0:3])
      else:
        stats[period] = ''
        
      if last_sum and info[period]:
        stats['%s_perc' % period] = int((1.0 * stats[period] - last_sum) / last_sum * 100)
        
      last_sum = stats[period]

  context = {
    'artist_form': artist_form,
    'artists':     artists,
    'page':        page,
    'paginator':   paginator
  }

  return render_to_response('fancy_admin/artists.html', context)

@password_required
def media(request):
  items = []
  
  today            = datetime.now().replace(hour = 0, minute = 0, second = 0)
  thirty_days_ago  = today - timedelta(days = 30)

  for artist in Artist.objects():
    for m in artist.media:
      stats = m.stats.stats_over(thirty_days_ago, today)

      items.append({'artist': artist, 'media': m, 'plays_per_day': stats.number_of_plays or '' })
      
  context = {
    'media': items
  }
      
  return render_to_response('fancy_admin/media.html', context)

@password_required
def system_stats(request):
  systems = { }

  for item in SystemStatInfo.objects():
    if item.system_id not in systems:
      systems[item.system_id] = { }

    # Plays are normalized to increments of 20
    adj_plays = int(item.plays_per_day) / 5 * 5

    if adj_plays > settings.SAMPLE_MIN_PER_DAY and adj_plays < settings.SAMPLE_MAX_PER_DAY:    
      if adj_plays not in systems[item.system_id]:
        systems[item.system_id][adj_plays] = 0

      systems[item.system_id][adj_plays] += item.number

  series = []
  
  for system_id, stats in systems.iteritems():
    series.append({'name': system_id, 'data': [(k, v) for k, v in stats.iteritems()]})
    
  return HttpResponse(simplejson.dumps(series))    

@password_required
def resource_domains(request):
  show_domain_map_f = """
  function() {
    var domainRe = /(.*?):/;

    for(var i = 0; i < this.parsed_resources.length; i++) {
      var m = domainRe.exec(this.parsed_resources[i]);
      
      if(m) {      
        emit(m[1], 1);
      }
    }
  }
  """

  artist_domain_map_f = """
  function() {
    var domainRe = /(.*?):/;
    
    var state = this.processor_state['profile-parser'] || { };
    
    for(var handler in state) {
      var resources = state[handler]['resources'];
      
      for(var i = 0 ; i < resources.length; i++) {
        var m = domainRe.exec(resources[i]);
      
        if(m) {      
          emit(m[1], 1);
        }
      }
    }
  }
  """
  
  sum_by_key_f = """
  function(k, vals) {
    var sum = 0;
    
    for(var i = 0; i < vals.length; i++) {
      sum += vals[i];
    }

    return sum;
  }
  """

  show_domains   = []
  artist_domains = []
  
  for doc in Show.objects.map_reduce(show_domain_map_f, sum_by_key_f):
    show_domains.append({'domain': doc.key, 'number': doc.value})
    
  for doc in Artist.objects.map_reduce(artist_domain_map_f, sum_by_key_f):
    artist_domains.append({'domain': doc.key, 'number': doc.value})

  show_domains.sort(lambda x, y: cmp(y['number'], x['number']))
  artist_domains.sort(lambda x, y: cmp(y['number'], x['number']))

  return render_to_response('fancy_admin/admin_resource_domains.html', {'show_domains': show_domains, 'artist_domains': artist_domains})
  
def best_artists(request):
  act_info       = []
  unknown        = 0
  no_info        = 0
  total          = 0
  with_media     = 0
  with_resources = 0
  
  for show in Show.objects():
    artist_map = show.related_artists()
    
    total += 1
    
    if any( a.media for a in artist_map.values() ):
      with_media += 1

    if show.parsed_resources:
      with_resources += 1
    
    had_headliner     = False
    chosen            = -1
    chosen_play_count = 0
        
    for i, a in enumerate(show.artists):
      to_add = i + 1 - len(act_info)
      
      for x in range(to_add):
        act_info.append({
          'num_total':      0,
          'num_with_media': 0,
          'should_see':     0
        })
        
      play_count = 0
      
      act_info[i]['num_total'] += 1
      
      artist = None
      
      if a.artist_id:
        artist = artist_map.get(a.artist_id)
      
      if artist:
        play_count = reduce(lambda x, y: max(x, y), [m.stats.number_of_plays for m in artist.media], 0)
      
        if artist.media:
          act_info[i]['num_with_media'] += 1
      
      if i == 0 and play_count > 0:
        had_headliner = True
      
      if play_count > chosen_play_count:
        chosen = i
        chosen_play_count = play_count
        
    if chosen == -1:
      no_info += 1
    else:
      if not had_headliner:
        unknown += 1
      else:
        act_info[chosen]['should_see'] += 1
        
  for info in act_info:
    info['percent_with_media'] = int(100.0 * info['num_with_media'] / info['num_total'])

  context = {
    'act_info':       act_info,
    'total':          total,
    'with_media':     with_media,
    'with_resources': with_resources,
    'unknown':        unknown,
    'no_info':        no_info
  }

  return render_to_response('fancy_admin/best_artists.html', context)

@password_required
def parser_stats(request):
  show_map_f = """
  function() {
    var stats = {
      total:          1,
      with_resources: this.parsed_resources.length > 0 ? 1 : 0,
      with_artists:   this.artists.length > 0 ? 1 : 0,
      with_title:     this.title != null ? 1 : 0
    };
  
    emit(this.parse_meta.parser_id, stats)
  }
  """

  reduce_f = """
  function(k, vals) {
    var summarized = {
      total:          0,
      with_resources: 0,
      with_artists:   0,
      with_title:     0
    };
  
    for(var i = 0 ; i < vals.length; i++) {
      var stats = vals[i];
  
      for(var key in stats) {
        summarized[key] += stats[key];
      }
    }
  
    return summarized
  }
  """
  
  show_summary = { }

  for stat in Show.objects.map_reduce(show_map_f, reduce_f):
    show_summary[ stat.key ] = stat.value
  
  stats = []

  for stat in ParserStat.objects().order_by('parser_id'):
    stats.append({
      'parser_id': stat.parser_id,
      'stats':     stat,
      'shows':     show_summary.get(stat.parser_id, {})
    });
  

  return render_to_response('fancy_admin/stats.html', {'parser_stats': stats})

@password_required
def show_edit(request, show_id):
  show  = Show.objects.with_id(show_id)

  if request.method == 'POST':
    data = request.POST
  else:
    data = None
  
  forms   = []
  context = {
    'show': show
  }

  show_form    = ShowForm(         prefix = 'show',      data = data, initial = initial_for_instance(ShowForm, show))
  venue_form   = ShowVenueForm(    prefix = 'venue',     data = data, initial = initial_for_instance(ShowVenueForm, show.venue))
  artist_forms = []
  
  for i, artist in enumerate(show.artists):
    artist_forms.append(ArtistInfoForm(prefix = 'artist-%d' % i, data = data, instance = artist))

  forms.extend([show_form, venue_form])
  forms.extend(artist_forms)

  if all(f.is_valid() for f in forms):
    raise Exception("Save is currently unimplemented")
    context['saved'] = True
  elif data:
    context['error'] = True

  artist_map = show.related_artists()
  
  stats = { }

  for stat in SystemStat.objects():
    stats[ stat.system_id ] = stat
  
  for a in artist_map.values():
    for m in a.media:
      plays_per_day = m.stats.stats_last_30_days().number_of_plays
      system_stat   = stats.get(m.system_id)
  
      if plays_per_day != None and system_stat:
        m.stats.score = ( plays_per_day - system_stat.plays_per_day)  / system_stat.stddev
  
  for artist_info in show.artists:
    if artist_info.artist_id:
      artist_info.full = artist_map[artist_info.artist_id]

  context.update({
    'show_form':    show_form,
    'venue_form':   venue_form,
    'artist_forms': artist_forms
  })

  return render_to_response('fancy_admin/show_edit.html', context)
  
@password_required
def artist_stats(request):
  shows = shows_for_day(datetime.today())
  
  artists = []
  
  today          = datetime.today().replace(hour = 0, minute = 0, second = 0)
  three_days_ago = today - timedelta(days = 3)
  
  for show in shows:
    show.performers = associate_media_with_performers(show)
    
    for performer in show.performers:
      artists.append(performer)

      performer.media_stats = { }
      
      for media in performer.media:
        source, other = media.uri.split(':', 1)
        
        source = source.replace('-', '_')
        
        if source not in performer.media_stats:
          performer.media_stats[source] = {
            'plays_total':     0,
            'plays_avg_3days': 0
          }
          
        performer.media_stats[source]['plays_total']     += media.play_count
        performer.media_stats[source]['plays_avg_3days'] += media.average_plays_over(three_days_ago, today)

  context = {
    'artists': artists
  }

  return render_to_response('fancy_admin/artist_stats.html', context)

@password_required
def show_link_artist(request, show_id, artist_position):
  show        = Show.objects.with_id(show_id)
  artist_info = show.artists[int(artist_position)]
  
  query  = request.REQUEST.get('query', '')
  
  if request.REQUEST.get('link') and request.REQUEST.get('artist'):
    artist = Artist.objects.with_id(request.REQUEST.get('artist'))
    
    show.artists[int(artist_position)].artist_id = artist.id

    show.save()
    
    return HttpResponseRedirect(reverse('admin-show-edit', kwargs = {'show_id': show.id_str}))
  else:
    context = {
      'query':           query,
      'show':            show,
      'artist_position': artist_position,
      'artist_info':     artist_info,
      'matching':        []
    }
  
    if query:
      context['matching'] = Artist.objects(name__icontains = query).order_by('name').limit(10)
  
    return render_to_response('fancy_admin/show_link_artist.html', context)

@password_required
def artist_new(request):
  association_form = ArtistAssociationForm(prefix = 'associate', data = request.REQUEST)
  
  if not association_form.is_valid():
    raise Exception(association_form.errors)
    
  show_id         = association_form.cleaned_data['show_id']
  artist_position = association_form.cleaned_data['artist_position']
  show            = None
  artist_name     = None
  
  if show_id:
    show = Show.objects.with_id(show_id)
    artist_name = show.artists[artist_position].name

  saved, artist, context = artist_add_or_edit(request, name = artist_name)

  if not saved:
    return render_to_response('fancy_admin/artist_new.html', context)
  else:
    if show:
      show.artists[artist_position].artist_id = artist.id
      show.save()
      
      return HttpResponseRedirect(reverse('admin-show-edit', kwargs = {'show_id': show.id_str}))
    else:
      return HttpResponseRedirect(reverse('admin-artist-edit', kwargs = {'artist_id': artist.id_str}))
  
@password_required
def artist_edit(request, artist_id):
  saved, artist, context = artist_add_or_edit(request, artist_id)
  
  return render_to_response('fancy_admin/artist_edit.html', context)

@password_required
def artist_add_or_edit(request, artist_id = None, name = None):
  if artist_id:
    artist = Artist.objects.with_id(artist_id)
  else:
    artist = None

  if request.method == 'POST':
    data = request.POST
  else:
    data = None
  
  forms   = []
  context = {
    'artist': artist
  }
  
  artist_initial = { }
  
  if name:
    artist_initial['name'] = name

  artist_form   = ArtistForm(prefix = 'artist', data = data, instance = artist, initial = artist_initial)
  profile_forms = []
  
  if artist:
    i = 0

    for i, profile in enumerate(artist.profiles):
      profile_forms.append(ProfileForm(source_id = 'ui:admin', prefix = 'profile-%d' % i, data = data, instance = profile))
    
    j = i
    
    while j < i + 2:
      j += 1

      profile_forms.append(ProfileForm(source_id = 'ui:admin', prefix = 'profile-%d' % j, data = data))
  else:
    for i in range(0, 2):
      profile_forms.append(ProfileForm(source_id = 'ui:admin', prefix = 'profile-%d' % i, data = data))

  forms.append(artist_form)
  forms.extend(profile_forms)
  
  saved = False

  if all(f.is_valid() for f in forms):
    artist   = artist_form.save()
    
    profiles = []

    for p in profile_forms:
      if p.defined():
        profiles.append(p.save())

    artist.profiles = profiles

    artist.save()

    saved = True
  elif data:
    context['error'] = True

  context.update({
    'saved':         saved,
    'artist_form':   artist_form,
    'profile_forms': profile_forms
  })
  
  return saved, artist, context
  
@password_required
def missing_venues(request):
  venue_map_f = """
  function() {
    emit(this.venue.url, this.venue)
  }
  """

  reduce_f = """
  function(k, vals) {
    return vals[0];
  }
  """

  venue_map = { }

  for venue_doc in Show.objects.map_reduce(venue_map_f, reduce_f):
    venue_map[venue_doc.key] = venue_doc.value

  for venue in Venue.objects():
    if venue.url in venue_map:
      del venue_map[venue.url]

  venues = venue_map.values()

  venues.sort(lambda x,y: cmp(x['name'], y['name']))

  return render_to_response('fancy_admin/missing_venues.html', {'venues': venues})