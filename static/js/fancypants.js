var FancyUI = null;

(function() {
  Fancy = { };

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
 	     
 	    this.closeFilterPanel(true);
 	    
 	    this.shows.filter('.show-featured').each(function(showEl) {
 	      var show = $(showEl);
 	      
 	      show.css('position', 'absolute');
 	    });
      
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
      var baseWidth = 152;
      var columns   = parseInt($('#main-nav').outerWidth() / baseWidth);
      
      console.log($('#main-nav').outerWidth());
      
      if(columns % 2 != 0) {
        columns--;
      }

//      $('#artists ul').columnizeList({cols: columns, width: baseWidth, unit:'px'});
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
      
      $('.show-list header').bind('click', function(ev) {
        ev.preventDefault();
        
        if(ui.filterPanelIsOpen) {
          ui.closeFilterPanel();
        } else {
          ui.openFilterPanel();
        }
      });
      
      this.shows.delegate('.show-feautured', 'mouseenter', function(ev) {
        $(this).addClass('mouse-over');
      });
      
      this.shows.delegate('.show-featured', 'mouseleave', function(ev) {
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
    },
    
    openFilterPanel: function() {
      $('.show-list nav').slideDown();

      this.filterPanelIsOpen = true;
    },
    
    closeFilterPanel: function(instant) {
      if(instant) {
        $('.show-list nav').css('display', 'none');
      } else {
        $('.show-list nav').slideUp();
      }

      this.filterPanelIsOpen = false;
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
}());