var FancyUI = null;

(function() {
YUI().use('event-custom', function(Y) {
  Fancy = { };
  
  function rand(around, thresh) {
    var neg    = (Math.random() > 0.5) ? 1 : -1;
    var offset = thresh * neg * Math.random();
    
    return parseInt(around + offset);
  }

  Fancy.PreviewManager = function() {
    this.init();
  };

  Fancy.PreviewManager.prototype = {
    PREVIEW_PLAY:   "preview-play",
    PREVIEW_PAUSE:  "preview-pause",
    PREVIEW_RESUME: "preview-resume",
    PREVIEW_STOP:   "preview-stop",
    PREVIEW_FINISH: "preview-finish",
    PREVIEW_STATE:  "preview-state",

    init: function() {
      this._showId = undefined;
      this._meta   = undefined;
    },

    getShowId: function() {
      return this._showId;
    },

    getMeta: function() {
      return this._meta;
    },

    startPreview: function(showId, streamUrl, meta) {
      this.stop();

      this._showId = showId;
      this._meta   = meta;
      this._sound  = this._getSound(showId, streamUrl);

      this.play();
    },

    isPaused: function() {
      if(this._sound) {
        return this._sound.paused;
      } else {
        return false;
      }
    },

    play: function() {
      if(this._sound) {
        this._sound.play();
      }
    },

    stop: function() {
      if(this._sound) {
        this._sound.stop();
      }
    },

    pause: function() {
      if(this._sound) {
        this._sound.pause();
      }
    },

    resume: function() {
      if(this._sound) {
        this._sound.resume();
      }
    },

    _getSound: function(showId, streamUrl) {
      var manager = this;
      var soundId = 'preview-' + showId;
      var sound   = soundManager.getSoundById(soundId);
      
      if(!sound) {
        sound = soundManager.createSound({
          'id':     soundId,
          'url':    streamUrl,
          'volume': 60,
          'stream': true,
          'whileplaying': function() {
            manager.fire(manager.PREVIEW_STATE, this.position, this.duration);
          },
          'onplay': function() {
            manager.fire(manager.PREVIEW_PLAY);
          },
          'onpause': function() {
            manager.fire(manager.PREVIEW_PAUSE);
          },
          'onresume': function() {
            manager.fire(manager.PREVIEW_RESUME);
          },
          'onstop': function() {
            manager.fire(manager.PREVIEW_STOP);
          },
          'onfinish': function() {
            manager.fire(manager.PREVIEW_FINISH);
          }
        });
      }

      return sound
    }
  };
  
  Y.augment(Fancy.PreviewManager, Y.EventTarget);

  Fancy.UI = function() {
  };

  Fancy.UI.prototype = {
    init: function() {
      this.currentShowId      = null;
      this.displayState       = 'top';
      this.venuePanelIsOpen   = false;
      this.page               = 0;
      this.showPanelWasClosed = false;
      this.requests        = {
        showList:    null,
        showDetails: null
      };
      this.filters         = {
        free:     false,
        outdoors: false,
        county:   null,
        geo:      null
      };
      
      this.shows   = $('#shows');
      this.artists = $('#artists');
 	    
 	    this._columnizeLists();
 	     
 	    this.closeVenuePanel(true);
      
      //this._initSettings();
      this._initDisplayCompat();
      this._initEvents();
      this._initPreviews();
    },
    
    _initDisplayCompat: function() {
      if(!Modernizr.textshadow) {
        $('#shows .show h2').each(this._createShadow);
        $('#shows .show .venue').each(this._createShadow);
      }
    },
    
    _createShadow: function() {
      if($.browser.msie) {
       $(this).textShadow();
      } else {
        var item   = $(this);
        var shadow = item.clone();
      
        var pos    = item.position();
      
        shadow.css('top',   pos.top + 1);
        shadow.css('left',  pos.left + 1);
        shadow.css('color', 'black');
        shadow.css('z-index', 0);
      
        item.css('z-index', 1);

        item.parent().append(shadow);
      }
    },
    
    _columnizeLists: function() {
      var baseWidth = 162;
      var columns   = parseInt($('#main-nav .wrapper').outerWidth() / baseWidth);
      
      if(columns % 2 != 0) {
        columns--;
      }

      $('#artists ul').columnizeList({cols: columns, width: baseWidth, unit:'px'});
      $('#venue-list ul').each(function() {
	      $(this).columnizeList({cols: columns, width: baseWidth, unit:'px'});
 	    });      
    },
    
    _initSettings: function() {
      var ui       = this;
      var settings = $('#settings');
      
      var settingsClasses = [Fancy.UI.Settings.Free, Fancy.UI.Settings.Brooklyn, Fancy.UI.Settings.Manhattan, Fancy.UI.Settings.NearLocation];
      
      $.each(settingsClasses, function(index, settingClass) {
        var li   = $('<li>');
        var impl = new settingClass(ui);
        
        settings.append(li);
        impl.render(li);
      });
      
      settings.find('li').not('li:last-child').each(function() {
        this.appendChild(document.createTextNode(' / '));
      });
    },
    
    _initPreviews: function() {
      var ui      = this;
      var manager = new Fancy.PreviewManager();

      this.preview_manager = manager;

      var preview = $('#preview');

      preview.delegate('a.toggle-play-state', 'click', function(event) {
        event.preventDefault();

        manager.isPaused() ? manager.play() : manager.pause();
      });
      
      preview.delegate('a.prev', 'click', function(event) {
        event.preventDefault();

        var showId = ui.getPrevShowWithPreview( manager.getShowId() );

        if(showId) {
          ui.setCurrentShow(showId);
        }
      });

      preview.delegate('a.next', 'click', function(event) {
        event.preventDefault();

        var showId = ui.getNextShowWithPreview( manager.getShowId() );

        if(showId) {
          ui.setCurrentShow(showId);
        }
      });
      
      preview.delegate('.info', 'click', function(event) {
        ui.expandShowPanel();
      });

      manager.on('preview-state', function(position, duration) {
        var state = preview.find('.state');

        var p = ui.formatTime(position);
        var d = ui.formatTime(duration);

        state.text( duration ? p + '/' + d : p );
      });

      manager.on('preview-play', function() {
        var meta = manager.getMeta();
        preview.css('display', 'block');
        preview.html('');
        
        var header = $('<span>').addClass('info').appendTo(preview);
        
        if(meta.artist) {
          $('<span>').addClass('artist').text(meta.artist).appendTo(header)
        }
        
        $('<span>').addClass('title').text(meta.title).appendTo(header);
        
        var controls = $('<span>').addClass('controls').appendTo(preview);
        
        $('<span>').addClass('state').text('0:00').appendTo(controls);
        $('<a href="#">').addClass('toggle-play-state').text('Pause').appendTo(controls);
        
        controls.append(document.createTextNode(' / '));
        if(ui.getPrevShowWithPreview( manager.getShowId() )) {
          $('<a href="#">').addClass('prev').text('Go Back').appendTo(controls);
        } else {
          $('<span>').addClass('disabled').text('Go Back').appendTo(controls);
        }

        controls.append(document.createTextNode(' / '));
        if(ui.getNextShowWithPreview( manager.getShowId() )) {
          $('<a href="#">').addClass('next').text('Skip').appendTo(controls);
        } else {
          $('<span>').addClass('disabled').text('Skip').appendTo(controls);
        }
      });

      manager.on('preview-pause', function() {
        preview.find('a.toggle-play-state').text('Resume');
      });

      manager.on('preview-resume', function() {
        preview.find('a.toggle-play-state').text('Pause');
      });

      manager.on('preview-stop', function() {
        preview.html('');
      });

      manager.on('preview-finish', function() {
        var showId  = this.getShowId();

        var nextShowId = ui.getNextShowWithPreview(showId);

        if(nextShowId) {
          ui.setCurrentShow(nextShowId);
        }
      });
    },
    
    getShowEl: function(showId) {
      return $('#show-' + showId);
    },
    
    _firstShowWithPreview: function(shows) {
      var me     = this;
      var showId = null;

      shows.each(function() {
        showId = me._showFromElement(this).showId;

        return false;
      });

      return showId;
    },

    
    _firstShowWithPreview: function(shows) {
      var me     = this;
      var showId = null;

      shows.each(function() {
        var info = me._showFromElement(this);

        if(info.preview) {
          showId = info.showId;

          return false;
        }
      });

      return showId;
    },
    
    getPrevShow: function(showId) {
      return this._firstShow($('#show-' + showId).prevAll());
    },
    
    getNextShow: function(showId) {
      return this._firstShow($('#show-' + showId).nextAll());
    },
    
    getPrevShowWithPreview: function(showId) {
      return this._firstShowWithPreview($('#show-' + showId).prevAll());
    },

    getNextShowWithPreview: function(showId) {
      return this._firstShowWithPreview($('#show-' + showId).nextAll());
    },

    _showFromElement: function(el) {
      var info = {
        'showId': el.getAttribute('show-id')
      };

      if(el.getAttribute('preview-url')) {
        info.preview = {
          'artist':    el.getAttribute('preview-artist'),
          'title':     el.getAttribute('preview-title'),
          'streamUrl': el.getAttribute('preview-url')
        };
      }

      return info;
    },

    formatTime: function(milliseconds) {
      var seconds = parseInt(milliseconds / 1000);
      var minutes = parseInt(seconds / 60);
      
      seconds = seconds - minutes * 60;

      if(seconds < 10) {
        seconds = '0' + seconds;
      }
      
      return minutes + ':' + seconds;
    },
    
    _initEvents: function() {
      var ui = this;
      
      $(window).resize(function() {
        ui._columnizeLists();
      });
      
      $('#venue-chooser a').bind('click', function(ev) {
        ev.preventDefault();
        
        if(ui.venuePanelIsOpen) {
          ui.closeVenuePanel();
        } else {
          ui.openVenuePanel();
        }
      });
      
      this.shows.delegate('li.show', 'mouseenter', function(ev) {
        $(this).addClass('mouse-over');
      });
      
      this.shows.delegate('li.show', 'mouseleave', function(ev) {
        $(this).removeClass('mouse-over');
      });

      this.shows.delegate('#state', 'click', function(ev) {
        ev.preventDefault();

        if(ui.displayState == 'selected') {
          ui.showTopShows();
        } else if(ui.displayState == 'all') {
          ui.showTopShows();
        } else {
          ui.showAllShows();
        }
      });
      
      this.shows.delegate('#prev', 'click', function(ev) {
        ev.preventDefault();

        ui.prevPage();
      });
      
      this.shows.delegate('#next', 'click', function(ev) {
        ev.preventDefault();

        ui.nextPage();
      });
      
      this.shows.delegate('.more-info', 'click', function() {
        var show = $(this).parents('.show').first();
        
        show.addClass('details-shown');
      });

      this.shows.delegate('.close', 'click', function() {
        var show = $(this).parents('.show').first();
        
        show.removeClass('details-shown');
      });

      this.artists.delegate('a', 'click', function(ev) {
        ev.preventDefault();

        var artist_info = $(this).parents('li').first();
        
        var showIds     = artist_info.get(0).getAttribute('data-shows').split(',');
        
        ui.showSelected(showIds);
        
        ui.clearArtistSelection();
        
        artist_info.addClass('selected');
      });
    },
    
    openVenuePanel: function() {
      $('#venue-chooser').addClass('active');

      $('#venue-nav').slideDown();
      
      // We need to redo the columns here in case the window
      // was resized while we were hidden
      this._columnizeLists();
      
      this.venuePanelIsOpen = true;
    },
    
    closeVenuePanel: function(instant) {
      if(instant) {
        $('#venue-nav').css('display', 'none');
      } else {
        $('#venue-nav').slideUp(function() {
          $('#venue-chooser').removeClass('active');
        });        
      }

      this.venuePanelIsOpen = false;
    },    
    
    setCurrentShow: function(showId) {
      var showEl     = document.getElementById('show-' + showId);
      var info       = this._showFromElement(showEl);
      var manager    = this.preview_manager;
      
      this.currentShowId = showId;

      if(info.preview) {
        manager.startPreview(info.showId, info.preview.streamUrl, {'artist': info.preview.artist, 'title': info.preview.title});
      } else {
        manager.stop();

        $('#preview').text("Sorry, we don't have a preview for this one just yet");
      }      
      
      this.currentShowId = showId;
      this.updateShowPanel(showId);
      this.highlightShow(showId);
    },
    
    highlightShow: function(showId) {
      var ui = this;

      ui.shows.find('.show-detail').each(function() {
        var det = $(this);

        det.removeClass('show-detail');

        ui._syncDetailsUnder(det);
      });

      var newShow = $('#show-' + showId);

      newShow.addClass('show-detail');

      ui._showDetails(newShow);
    },
 
    collapseShowPanel: function() {
      $('#show-info').animate({height: 0}, 'fast', function() { $(this).css('display', 'none') });
    },
    
    expandShowPanel: function(forceExpand) {
      var info = $('#show-info');

      info.css('display', 'block');
      info.animate({height: 100 }, 'fast');
    },
    
    updateShowPanel: function(showId) {
      var ui = this;

      if(this.requests.showDetails) {
        this.requests.showDetails.abort();
        this.requests.showDetails = null;
      }

      this.requests.showDetails = $.ajax({
        'url':     '/show/' + showId + '/details/',
        'success': function(data) {
          var info = $('#show-info');
          
          info.html(data);
          
          if(!ui.showPanelWasClosed) {
            ui.expandShowPanel();
          }
        },
        'error': function() {
          var info = $('#show-info');
          
          info.html('Ooop, your show details were eaten by gremlins. Please try again')
          
          info.animate({height: 17}, 'fast');
        },
        'complete': function() {
          ui.requests.showDetails = null;
        }
      });
    },
    
    showHeight: function() {
      var showSet    = $('#shows ul').first();
      var showSetEl  = showSet.get(0);

      return showSet.children('.show').first().outerHeight(true);      
    },
    
    showPage: function(pageNum) {
      var showSet    = $('#shows ul').first();
      var showHeight = this.showHeight();

      showSet.scrollTo(showHeight * 2 * pageNum, 500);
    },
    
    nextPage: function() {
      this.showPage(this.page + 1);
      
      this.page++;
    },
    
    prevPage: function() {
      if(this.page > 0) {
        this.showPage(this.page - 1);
      
        this.page--;
      }
    },
    
    clearArtistSelection: function() {
      this.artists.find('li').removeClass('selected');
    },
    
    setDisplayState: function(newState) {
      this.displayState = newState;
  
      var map = {
        'all':      'Show Less',
        'top':      'Show More',
        'selected': 'Show Top'
      }

      if(newState != 'selected') {
        this.clearArtistSelection();        
      }

      $('#state').text( map[this.displayState] );
      
      for(var state in map) {
        this.shows.removeClass(state);        
      }

      this.shows.addClass(newState);
    },

    showAllShows: function() {
      var showSet    = $('#shows ul').first();
      var showSetEl  = showSet.get(0);
      var showHeight = showSet.children('.show').first().outerHeight(true);
      
      this.page = 0;

      showSet.scrollTop(0);

      showSet.animate({height: showSetEl.scrollHeight}, 'fast', function() {
        showSet.css('height', 'auto');
        showSet.children('.show').each(function() { $(this).css('display', 'block'); });
      });

      this.setDisplayState('all');
    },
    
    showTopShows: function() {
      var showSet    = $('#shows ul').first();
      var showSetEl  = showSet.get(0);
      var showHeight = showSet.children('.show').first().outerHeight(true);
      
      this.page = 0;
      
      showSet.scrollTop(0);
      
      showSet.animate({height: 2 * showHeight}, 'fast', function() {
        showSet.children('.show').each(function() { $(this).css('display', 'block'); });
      });
      $.scrollTo(document.body, {'duration': 500, 'offset': {'top': -100}});
      
      this.setDisplayState('top');
    },
    
    showSelected: function(showIds) {
      var requestedShows = { };
      var showSet        = $('#shows ul').first();
      var showSetEl      = showSet.get(0);
      var showHeight     = showSet.children('.show').first().outerHeight(true);
      
      for(var i in showIds) {
        requestedShows[showIds[i]] = true;
      }
      
      showSet.fadeOut('fast', function() {
        showSet.children('.show').each(function() {
          var showId = this.getAttribute('data-id');

          if(!requestedShows[showId]) {
            $(this).css('display', 'none');
          } else {
            $(this).css('display', null);
          }
        });

        showSet.fadeIn('fast');
      });

      this.setDisplayState('selected');
    },
    
    freeFilterIsSet: function() {
      return this.filters.free;
    },

    setFreeFilter: function(setFilter) {
      this.filters.free = setFilter;
      
      this.fire('free-filter-changed');

      this.refreshShows()
    },
    
    outdoorFilterIsSet: function() {
      return this.filters.outdoors;
    },

    setOutdoorFilter: function(setFilter) {
      this.filters.outdoors = setFilter;
      
      this.fire('outdoor-filter-changed');

      this.refreshShows()
    },
    
    setCountyFilter: function(county) {
      this.filters.county = county;

      this.fire('county-filter-changed');

      this.refreshShows();
    },
    
    countyFilter: function(county) {
      return this.filters.county;
    },
    
    setGeoFilter: function(geo) {
      this.filters.geo = geo;
      
      this.fire('geo-filter-changed');

      this.refreshShows();
    },
    
    geoFilter: function() {
      return this.filters.geo;
    }
  };
  Y.augment(Fancy.UI, Y.EventTarget);
  
  Fancy.UI.Settings = { };
  
  Fancy.UI.Settings.Free = function(ui) {
    this.init(ui);
  };
  
  Fancy.UI.Settings.Free.prototype = {
    init:   function(ui)        { this.ui = ui },
    render: function(container) {
      var ui = this.ui;
      var a  = $('<a href="#">').text('Free Summer Shows!')

      container.append(a);
      
      a.click(function(ev) {
        ev.preventDefault();

        ui.setFreeFilter(!ui.freeFilterIsSet());
      });
      
      ui.on('free-filter-changed', function() {
        ui.freeFilterIsSet() ? a.addClass('enabled') : a.removeClass('enabled');
      });
    }
  };
  
  Fancy.UI.Settings.Outdoors = function(ui) {
    this.init(ui);
  };
  
  Fancy.UI.Settings.Outdoors.prototype = {
    init:   function(ui)        { this.ui = ui },
    render: function(container) {
      var ui = this.ui;
      var a  = $('<a href="#">').text('Outdoors')

      container.append(a);
      
      a.click(function(ev) {
        ev.preventDefault();

        ui.setOutdoorFilter(!ui.outdoorFilterIsSet());
      });
      
      ui.on('outdoor-filter-changed', function() {
        ui.outdoorFilterIsSet() ? a.addClass('enabled') : a.removeClass('enabled');
      });
    }
  };

  var CountySetting = {
    render: function(container) {
      var setting = this;
      var ui      = this.ui;
      var a       = $('<a href="#">').text(this.displayName)

      container.append(a);
      
      a.click(function(ev) {
        ev.preventDefault();
        
        if(ui.countyFilter() == setting.county) {
          ui.setCountyFilter(null);
        } else {
          ui.setGeoFilter(null);
          ui.setCountyFilter(setting.county);
        }        
      });
      
      ui.on('county-filter-changed', function() {
        if(ui.countyFilter() == setting.county) {
          a.addClass('enabled');          
        } else {
          a.removeClass('enabled');
        }
      });
    }
  };

  Fancy.UI.Settings.Manhattan = function(ui) {
    this.init(ui);
  };
  
  Fancy.UI.Settings.Manhattan.prototype = {
    init:   function(ui) {
      this.ui          = ui;
      this.displayName = 'Manhattan';
      this.county      = 'ny-manhattan';
    }
  };
  Y.aggregate(Fancy.UI.Settings.Manhattan.prototype, CountySetting);
  
  Fancy.UI.Settings.Brooklyn = function(ui) {
    this.init(ui);
  };
  
  Fancy.UI.Settings.Brooklyn.prototype = {
    init:   function(ui) {
      this.ui          = ui;
      this.displayName = 'Brooklyn';
      this.county      = 'ny-brooklyn';
    }
  };
  Y.aggregate(Fancy.UI.Settings.Brooklyn.prototype, CountySetting);
  
  Fancy.UI.Settings.NearLocation = function(ui) {
    this.init(ui);
  };
  
  Fancy.UI.Settings.NearLocation.prototype = {
    init:   function(ui) {
      this.ui       = ui;
      this.position = null;
      this.queryInProgress = false;
    },
    render: function(container) {
      var me    = this;
      var ui    = this.ui;
      var title = $('<span>').text('Near ');
      var input = $('<input type="text" />');
      var geoTrigger    = $('<a href="#" title="Get My Location">').text('Locate Me').addClass('geo-trigger');
      var searchTrigger = $('<a href="#">').text('Search');
      var error      = $('<div>');
      var searchContainer = $('<span>').addClass('search-container');
      
      this.container = container;

      container.addClass('location-filter');
      container.append(title);
      container.append(searchContainer);
      searchContainer.append(input);
      searchContainer.append(searchTrigger);
      
      if(navigator.geolocation) {
        searchContainer.append(geoTrigger);
      }

      container.append(error);
      
      this.input   = input;
      this.errorEl = error;
      
      geoTrigger.click(function(event) {
        event.preventDefault();

        me.updateCurrentPosition();
      });
      
      searchTrigger.click(function(event) {
        event.preventDefault();

        me.updatePositionFromSearch(input.val());
      });
      
      input.keyup(function(event) {
        if(event.keyCode == 13) {
          me.updatePositionFromSearch(input.val());
        }
      });

      ui.on('geo-filter-changed', function() {
        var geo = ui.geoFilter();

        if(geo) {
          me.setError('');

          me.input.val(geo.name);

          title.addClass('enabled');
        } else {
          title.removeClass('enabled');          
        }
      });
    },
    
    geoBounds: function() {
      var sw = new google.maps.LatLng(40.4773990, -79.7625900);
      var ne = new google.maps.LatLng(45.0158650, -71.7774910);

      return new google.maps.LatLngBounds(sw, ne);
    },

    // FIXME currently this is hardcoded to NY
    geoRequest: function(search, callback) {
      var me       = this;
      var geocoder = new google.maps.Geocoder();

      if(!search.bounds) {
        search.bounds = this.geoBounds();
      }
      
      function filterWithinBounds(results, status) {
        if(status == google.maps.GeocoderStatus.OK) {
          var bounds     = me.geoBounds();
          var newResults = [];
          
          $.each(results, function() {
            if(bounds.contains(this.geometry.location)) {
              newResults.push(this);
            }
          });
          
          if(newResults.length == 0) {
            status = google.maps.GeocoderStatus.ZERO_RESULTS;
          }

          callback(newResults, status);
        } else {
          callback(results, status);
        }
      }

      geocoder.geocode(search, filterWithinBounds);
    },
    
    updatePositionFromSearch: function(search) {
      var me        = this;
      
      this.geoRequest({'address': search}, function(results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
          var loc = results[0].geometry.location;

          var geo = {
            'lat':  loc.lat(),
            'long': loc.lng(),
            'name': search
          }

          me.ui.setGeoFilter(geo);          
          me.ui.setCountyFilter(null);
        } else {
          me.setError('Unable to find that location');
        }
      });
    },

    updateCurrentPosition: function() {
      if(this.queryInProgress) {
        return;
      }
      
      var me = this;
      
      function updated(pos) { me._positionUpdate(pos); }
      function failed(err)  { me._positionUpdateFailed(err); }
      
      var opts = {
        enableHighAccuracy: false,
        maximumAge:         30 * 1000
      };
      
      navigator.geolocation.getCurrentPosition(updated, failed, opts);
      
      this.queryInProgress = true;
    },
    
    _positionUpdate: function(pos) {
      this.queryInProgress = false;
      
      this.position = pos;
      var me        = this;
      var geocoder  = new google.maps.Geocoder();
      var latlng    = new google.maps.LatLng(pos.coords.latitude, pos.coords.longitude);

      geocoder.geocode({'latLng': latlng}, function(results, status) {
        var geo = {
          'lat':  pos.coords.latitude,
          'long': pos.coords.longitude
        }

        if (status == google.maps.GeocoderStatus.OK) {
          geo.name = me._bestDescriptiveName(results);
        } else {
          geo.name = 'My Current Location';
        }

        me.ui.setGeoFilter(geo);
        me.ui.setCountyFilter(null);
      });
    },
    
    _bestDescriptiveName: function(addresses) {
      var ordering = ['neighborhood', "sublocality", "political"];
      
      var wantType  = { };
      var foundType = { };
      
      $.each(ordering, function() {
        wantType[this]   = true;
        foundType[ this] = null;
      });

      $.each(addresses, function() {
        var address = this;

        $.each(this.types, function() {
          if(wantType[this] && !foundType[this]) {
            foundType[this] = address;
          }
        });
      });
      
      var best = addresses[0];
      
      $.each(ordering, function() {
        if(foundType[this]) {
          best = foundType[this];
          
          return false;
        }
      });
      
      var name = null;
      
      $.each(best.address_components, function() {        
        for(var i = 0; i < this.types.length; i++) {
          if(wantType[this.types[i]]) {
            name = this.long_name;

            return false;
          }
        }
        
      });
      
      return name || best.formatted_address;
    },
    
    _positionUpdateFailed: function(err) {
      this.queryInProgress = false;
      
      console.log('Unable to retrieve location: ' + err.code + ' - ' + err.message);
      
      if(err.code == 1) {
        this.setError('Sorry, but you opted not to share your location with us.');
      } else {
        this.setError('Sorry, we were unable to locate you');
      }
    },
    
    setError: function(msg) {
      this.errorEl.text(msg);
    }
  };
  Y.aggregate(Fancy.UI.Settings.NearLocation.prototype, CountySetting);
  
  Fancy.UI.Settings.ShowDetails = function(ui) {
    this.init(ui);
  };
  
  Fancy.UI.Settings.ShowDetails.prototype = {
    init:   function(ui)        { this.ui = ui },
    anchorText: function() {
      return this.ui.detailsAreShown() ? 'Hide All Details' : 'Show All Details';
    },
    render: function(container) {
      var setting = this;
      var ui      = this.ui;
      var a       = $('<a href="#">').text(this.anchorText())

      container.append(a);
      
      a.click(function(ev) {
        ev.preventDefault();

        ui.setDetailsShown(!ui.detailsAreShown());
      });
      
      ui.on('details-shown-changed', function() {
        ui.detailsAreShown() ? a.addClass('enabled') : a.removeClass('enabled');
        
        a.text(setting.anchorText());
      });
    }
  };
});
}());