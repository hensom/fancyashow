$(function() {
  if(window.Fancy) {
    return;
  }

  window.Fancy = { Models: { }, Collections: { }, Views: { }, Controllers: { } };
  
  var Template = function(str) {
    var tmpl = _.template(str);

    return function(data) { return innerShiv(tmpl(data)); };
  }

  var URLS = {
    CURRENT_VISITOR:             '/api/v1/me/',
    CURRENT_VISITOR_SAVED_SHOWS: '/api/v1/me/saved_shows/'
  };

  var SIMPLE_DATE_FORMAT = "ddd, MMM d";
  
  function dateOnly(datetime) {
    return new Date(datetime.getFullYear(), datetime.getMonth(), datetime.getDate());
  }

  function parseDateTime(datetime) {
    if(datetime === null) {
      return null;
    } else if(_.isString(datetime)) {
      var parts = datetime.split('T');
      var date  = parts[0].split('-');
      var time  = (parts.length > 1) ? parts[1].split(':') : [0, 0, 0];
      
      return new Date(date[0], date[1] - 1, date[2], time[0], time[1], time[2]);
    } else {
      return datetime;
    }
  }

  Fancy.Models.ShowContext = Backbone.Model.extend({
    parse: function(response) {
      response.start_date = parseDateTime(response.start_date);
      response.end_date   = parseDateTime(response.end_date);

      return response;
    },
    getPeriodName: function() {
      var today    = Date.today(),
          tomorrow = Date.today().addDays(1)
          start    = this.get('start_date'),
          end      = this.get('end_date')
          
      if(start.equals(end)) {
        if(start.equals(today)) {
          return 'Tonight'
        } else if(start.equals(tomorrow)) {
          return 'Tomorrow'
        } else {
          return start.toString(SIMPLE_DATE_FORMAT);
        }
      } else {
        return start.toString(SIMPLE_DATE_FORMAT) + " to " + end.toString(SIMPLE_DATE_FORMAT);
      }
    },
    getLocationName: function() {
      
    },
    getTitle: function() {
      if(this.get('visitor')) {
        return "My Shows";        
      } else {
       return this.getPeriodName(); 
      }
    }
  });

  Fancy.Models.Venue        = Backbone.Model.extend({ });
  Fancy.Models.City         = Backbone.Model.extend({ });
  Fancy.Models.Neighborhood = Backbone.Model.extend({ });
  Fancy.Models.Show         = Backbone.Model.extend({
    parse: function(response) {
      response.date      = parseDateTime(response.date);
      response.show_time = parseDateTime(response.show_time);
      response.door_time = parseDateTime(response.door_time);

      return response;
    },
    getDisplayTitle: function() {
      parts = [ ]
  
      if(this.get('title')) {
        parts.push(this.get('title'));
      }

      var artists = this.get('artists');
  
      if(artists.length > 0 && parts.length > 0) {
        parts[0] += ':'
      }

      _.each(artists, function(artist, i) {
        parts.push(artist.name);

        if(i != artists.length - 1) {
          parts[i - 1] += ',';
        }
      });

      return parts.join(',');
    }
  });
  
  Fancy.Collections.ShowList = Backbone.Collection.extend({
    model: Fancy.Models.Show,
    parse: function(response) {
      return _.map(response, this.model.prototype.parse);
    }
  });

  Fancy.Models.Visitor = Backbone.Model.extend({
    url: URLS.CURRENT_VISITOR,
    initialize: function(attributes) {
      _.bindAll(this, "_updateSavedShows", "_processQueue", "_clearQueue");
      this.postLoginQueue = [];
      this.saved_shows = new Fancy.Collections.ShowList(attributes.saved_shows);
      this.bind("change:saved_shows", this._updateSavedShows);
      this.bind("auth:logout", this._clearQueue);
      this.bind("auth:login",  this._processQueue);
    },
    _clearQueue: function() {
      this.postLoginQueue = [];
    },
    _processQueue: function() {
      _.each(this.postLoginQueue, function(cb) { cb() });
      this.postLoginQueue = [];
    },
    _updateSavedShows: function() {
      this.saved_shows.refresh(this.get('saved_shows'))
    },
    parse: function(response) {
      response.saved_shows = this.saved_shows.parse(response.saved_shows);

      return response;
    },
    loggedIn: function() {
      return this.get('id') !== undefined;
    },
    requestLogin: function(cb) {
      if(cb) {
        this.postLoginQueue.push(cb)
      }
      this.trigger('auth:login-requested');
    },
    addShow: function(show) {
      var self = this;
      $.post(URLS.CURRENT_VISITOR_SAVED_SHOWS, {'add': show.id}, function() { self.saved_shows.add(show); });
    },
    removeShow: function(show) {
      var self = this;
      $.post(URLS.CURRENT_VISITOR_SAVED_SHOWS, {'remove': show.id}, function() { self.saved_shows.remove(show); });
    },
    showIsSaved: function(show) {
      return this.saved_shows.get(show.id) != null;
    },
    upcomingShows: function() {
      var today = dateOnly(new Date());
      return this.saved_shows.filter(function(show) { return show.get('date') >= today });
    },
    pastShows: function() {
      var today = dateOnly(new Date());
      return this.saved_shows.filter(function(show) { return show.get('date') < today });
    }
  });
  
  var displayCompatTimer = null;
  function TextShadow() {
    var item = $(this);
    
    if(this.getAttribute("data-set-shadow")) {
      return;
    } else {
      this.setAttribute("data-set-shadow", "1");
    }

    if(item.css('position') != 'absolute') {
      item.css('position', 'relative');
    }

    if(false && $.browser.msie) {
        item.textShadow();
    } else {
      var shadow = item.clone();
      var pos    = item.position();

      shadow.css('position', 'absolute');
      shadow.css('top',   pos.top + 1);
      shadow.css('left',  pos.left + 1);
      shadow.css('color', 'black');
      shadow.css('z-index', 1);

      item.css('z-index', 2);

      item.parent().append(shadow);
    }
  }
  function DisplayCompat() {
    displayCompatTimer = null;

    $(".show-featured h2").each(TextShadow);
    $(".show-featured ul").each(TextShadow);
    $(".show-featured .where-when").each(TextShadow);
  }
  function QueueDisplayCompat() {
    if(displayCompatTimer == null && !Modernizr.textshadow) {
      displayCompatTimer = setTimeout(DisplayCompat, 0);
      return;
    }    
  }

  Fancy.Views.ShowBanner = Backbone.View.extend({
    template: Template($('#featured-show-template').html()),
    tagName: 'li',
    events: {
      'click a.save-show-action': 'toggleShowSavedState'
    },
    initialize: function(options) {
      _.bindAll(this, 'render', 'maybeRender', 'toggleShowSavedState');

      this.visitor = options.visitor;
      this.show    = options.show;

      this.show.bind('change', this.render);
      this.visitor.saved_shows.bind('add',    this.maybeRender);
      this.visitor.saved_shows.bind('remove', this.maybeRender);
    },
    maybeRender: function(show) {
      if(show.id == this.show.id) {
        this.render();
      }
    },
    render: function() {
      var context = {
        'show':         this.show.toJSON(),
        'display_date': this.show.get('date').toString("MMM d"),
        'iso_date':     this.show.get('date').toString("yyyy-MM-dd"),          
        'saved':        this.visitor.showIsSaved(this.show)
      };

      $(this.el).html(this.template(context));
      
      QueueDisplayCompat();
      
      return this;
    },
    toggleShowSavedState: function(event) {
      var self   = this;
      var show   = this.show;
      var saved  = this.visitor.showIsSaved(this.show);
      
      var handleToggle = function() {
        if(saved) {
          self.visitor.removeShow(show);
        } else {
          self.visitor.addShow(show);
        }
      }

      if(!this.visitor.loggedIn()) {
        this.visitor.requestLogin(handleToggle);
      } else {
        handleToggle();
      }
      
      return false;
    }
  });
  
  Fancy.Views.Base = Backbone.View.extend({
    el: $('#wrapper'),
    base_template: Template($('#base-template').html()),
    content_selector: "section",
    render: function() {
      var context = {
        title:   this.getTitle(),
        nav:     this.getNav()
      };
      
      $(this.el).html(this.base_template(context));
            
      $(this.el).find(this.content_selector).first().append(this.getContent());
      
      return this;
    },
    getTitle:   function() { return 'IMPLEMENT TITLE';   },
    getNav:     function() { return 'IMPLEMENT NAV';     },
    getContent: function() { return 'IMPLEMENT CONTENT'; }
  })
  
  Fancy.Views.ShowGroup = Backbone.View.extend({
    template: Template($('#show-group-template').html()),
    tagName: 'section',
    initialize: function(options) {
      _.bindAll(this, 'showView');

      this.visitor            = options.visitor;
      this.shows              = options.shows;
      this.title              = options.title;
      this.show_list_selector = options.show_list_selector || 'ol';
      this.showViews          = _.map(this.shows, this.showView);
    },
    showView: function(show) {
      return new Fancy.Views.ShowBanner({visitor: this.visitor, show: show});
    },
    render: function() {
      var context = {
        title:      this.title,
        message:   (this.shows.length == 0) ? 'No shows' : ''
      };
      
      $(this.el).html(this.template(context));
      
      var list = $(this.el).find(this.show_list_selector).first();

      _.each(this.showViews, function(view) {
        list.append(view.render().el);
      });
      
      return this;
    }
  });

  Fancy.Views.ShowList = Backbone.View.extend({
    FEATURED_SIZE: 6,
    el: $("#show-list"),
    initialize: function(options) {
      _.bindAll(this, 'groupView');

      this.visitor    = options.visitor;
      this.context    = options.context;
      this.shows      = options.shows;
      this.groups     = this.groupShows(this.shows);
      this.groupViews = _.map(this.groups, this.groupView);
    },
    groupView:  function(group) {
      return new Fancy.Views.ShowGroup({visitor: this.visitor, title: group.title, shows: group.shows});
    },
    groupShows: function(shows) {
      var showsByRank   = shows.sortBy(function(show) { return -1 * show.get('rank') });
      var featuredShows = _.first(showsByRank, this.FEATURED_SIZE);
      var otherShows    = _.rest(showsByRank, this.FEATURED_SIZE);

      return [{title: 'Featured', shows: featuredShows}, {title: 'Lineup', shows: otherShows}];
    },
    render: function() {
      var el = $(this.el);
      
      el.html('');

      _.each(this.groupViews, function(view) { el.append(view.render().el); });
    }
  });
  
  Fancy.Views.VenueShowList = Fancy.Views.ShowList.extend({
    groupShows: function(shows) {
      var today         = dateOnly(new Date());
      var showsByRank   = shows.sortBy(function(show) { return -1 * show.get('rank') });
      var featuredShows = _.first(showsByRank, this.FEATURED_SIZE);
      var tonight       = _.filter(showsByRank, function(show) { return show.get('date').equals(today) })
      var lineup        = shows.sortBy(function(show) { return show.get('date') });

      return [{title: 'Tonight', shows: tonight}, {title: 'Featured', shows: featuredShows}, {title: 'Calendar', shows: lineup}];
    }
  });
  
  Fancy.Views.VisitorShowList = Fancy.Views.ShowList.extend({
    groupShows: function(shows) {
      var today        = dateOnly(new Date());
      var showsByDate  = _.sortBy(shows.models, function(show) { return show.get('date') });
      var futureShows  = _.filter(showsByDate,  function(show) { return show.get('date') >= today });
      var pastShows    = _.filter(showsByDate,  function(show) { return show.get('date') < today });

      return [{title: 'Upcoming Shows', shows: futureShows}, {title: 'Past Shows', shows: pastShows}];
    }
  });

  Fancy.UI = Backbone.Controller.extend({
    el: $('body'),
    initialize: function(options) {
      _.bindAll(this, "login");

      this.facebookAppId  = options.facebookAppId;
      this.page           = options.page;
      this.context        = new Fancy.Models.ShowContext();
      this.visitor        = new Fancy.Models.Visitor();
      this.shows          = new Fancy.Collections.ShowList();

      this.context.set(this.context.parse(options.context));
      this.visitor.set(this.visitor.parse(options.visitor));
      this.shows.refresh(_.map(options.shows, Fancy.Models.Show.prototype.parse));

      this._initAuth();
      this._initEvents();
      this._initEnhancements();

      if(this.visitor.loggedIn()) {
        this.visitor.trigger('auth:login');
      }
      
      this.visitor.bind("auth:login-requested", this.login);

      this.currentView = this._viewForContext();
      this.currentView.render();
    },    
    _viewForContext: function() {
      var viewClass = Fancy.Views.ShowList;

      if(this.context.get('visitor')) {
        viewClass = Fancy.Views.VisitorShowList;
      } else if(this.context.get('venue')) {
        viewClass = Fancy.Views.VenueShowList;
      }
      
      return new viewClass({context: this.context, shows: this.shows, visitor: this.visitor});
    },
    _parseShows: function(response) { 
      response.date      = parseDateTime(response.date);
      response.show_time = parseDateTime(response.show_time);
      response.door_time = parseDateTime(response.door_time);

      return response;
    },
    _initEvents: function() {
      var self  = this;
      
      this.visitor.bind('auth:login', function() {
        $('body').removeClass('logged_out').addClass('logged_in');
        self._updateUpcomingShowCount();
      });
      
      this.visitor.saved_shows.bind('add', function() {
        self._updateUpcomingShowCount();
      });

      this.visitor.saved_shows.bind('remove', function() {
        self._updateUpcomingShowCount();
      });
      
      this.visitor.bind('auth:logout', function() {
        $('body').removeClass('logged_in').addClass('logged_out');
        self._updateUpcomingShowCount();
      });
    },
    _initAuth: function() {
      var self = this;
      
      $("#site-nav .login") .click(function() { self.login();  return false; });
      $("#site-nav .logout").click(function() { self.logout(); return false; });
      
      this._updateUpcomingShowCount();

      FB.init({ appId:this.facebookAppId, cookie:true, status:true });

      FB.Event.subscribe('auth.sessionChange', function(response) {
        self._handleSessionChange(response);
      });
    },
    _updateUpcomingShowCount: function() {
      $("#site-nav .upcoming-shows").text(this.visitor.upcomingShows().length);
    },
    _initEnhancements: function() {
      this._initAddresses();
    },
    _initAddresses: function() {
      $('.fancy-address').each(function() {
        var title   = this.getAttribute('data-address-title');
        var address = this.getAttribute('data-address-address');
        var lat     = this.getAttribute('data-address-lat');
        var lng     = this.getAttribute('data-address-lng');
        var el      = $('<div class="map">')
        
        $(this).prepend(el);

      	var mapOptions = {
          zoom: 14,
          mapTypeId: google.maps.MapTypeId.ROADMAP,
      		mapTypeControl: false
        };

      	var map = new google.maps.Map(el.get(0), mapOptions);

      	var marker = new google.maps.Marker({
  	      map:      map, 
  	      position: new google.maps.LatLng(lat, lng),
  				title:    title
        });
        
        var highlightVenue = function() {
  				infoWindow.setContent(venueContent);
  			  infoWindow.open(map, marker);
  			};

  			google.maps.event.addListener(marker, 'click', function() {
  			  window.location = "http://maps.google.com/?q=" + encodeURIComponent(address);
			  });
        map.setCenter(new google.maps.LatLng(lat, lng));
      });
    },
    login: function() {
      FB.login();
      
      return false;
    },
    logout: function() {
      FB.logout();
      
      return false;
    },
    _handleSessionChange: function(response) {
      var self = this;

      if(response.session) {
        if(!this.visitor.loggedIn()) {
          $.post('/login/', function(data) {
            // TODO: return the new visitor as part of the login
            // or perhaps post to a UserSession resource
            self.visitor.fetch({
              success: function(visitor) { visitor.trigger('auth:login'); }
            });
          });
        }
      } else {
        $.post('/logout/', function(data) {
          self.visitor.clear();
          self.visitor.trigger('auth:logout');
        });
      }
    }
  });
});