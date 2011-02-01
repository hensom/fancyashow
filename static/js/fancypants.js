$(function() {
  window.Fancy = { };
  
  var URLS = {
    CURRENT_VISITOR:             '/api/v1/me/',
    CURRENT_VISITOR_SAVED_SHOWS: '/api/v1/me/saved_shows/'
  }

  var DAYS   = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'];
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'];

  function simpleDateFormat(datetime) {
    return MONTHS[datetime.getMonth()] + ' ' + datetime.getDate();
  }

  function parseDateTime(datetime) {
    if(datetime === null) {
      return null;
    } else if(_.isString(datetime)) {
      var parts = datetime.split('T');
      var date  = parts[0].split('-');
      var time  = parts[1].split(':');
      
      return new Date(date[0], date[1] - 1, date[2], time[0], time[1], time[2]);
    } else {
      return datetime;
    }
  }

  function parseShowJSON(o) {
    o.date      = parseDateTime(o.date);
    o.show_time = parseDateTime(o.show_time);
    o.door_time = parseDateTime(o.door_time);

    return o;
  }
  
  Fancy.Show = Backbone.Model.extend({
    parse: function(response) {
      return parseShowJSON(response);
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
    },
  });
  
  Fancy.ShowList = Backbone.Collection.extend({
    model: Fancy.Show
  });

  Fancy.Visitor = Backbone.Model.extend({
    url: URLS.CURRENT_VISITOR,
    initialize: function() {
      this.upcomingShows = new Fancy.ShowList([], {
        comparator: function(show) {
          return show.get('date');
        }
      });
    },
    parse: function(response) {
      this.upcomingShows.refresh(_.map(response.upcoming_shows, parseShowJSON));

      return response;
    },

    loggedIn: function() {
      return this.get('id') !== undefined;
    },

    addShow: function(show) {
      this.upcomingShows.add(show);

      $.post(URLS.CURRENT_VISITOR_SAVED_SHOWS, {'add': show.id});
    },

    removeShow: function(show) {
      this.upcomingShows.remove(show);

      $.post(URLS.CURRENT_VISITOR_SAVED_SHOWS, {'remove': show.id});
    }
  });
  
  Fancy.SavedShowItemView = Backbone.View.extend({
    tagName:  'li',
    template: _.template($('#saved-show-template').html()),
    events: {
      'click a.remove-saved-show': 'remove'
    },
    initialize: function(options) {
      this.visitor    = options.visitor;
      this.model      = options.model;
    },
    render: function() {
      var context = {
        'date':  simpleDateFormat(this.model.get('date')),
        'title': this.model.getDisplayTitle(),
        'url':   this.model.get('url')
      }

      $(this.el).html(this.template(context));
      
      return this;
    },
    remove: function() {
      this.visitor.removeShow(this.model);

      return false;
    }
  });

  Fancy.SavedShowListView = Backbone.View.extend({
    el:       $('#my-calendar'),
    template: _.template($('#my-calendar-template').html()),

    initialize: function(options) {
      _.bindAll(this, 'render');

      this.collection = options.collection;
      this.visitor    = options.visitor;
      
      this.collection.bind('add',     this.render);
      this.collection.bind('remove',  this.render);
      this.collection.bind('refresh', this.render);

      this.visitor.bind('auth:login',  this.render);
      this.visitor.bind('auth:logout', this.render);
    },
    
    render: function() {
      var el = $(this.el);

      var context = {
        message:   (this.collection.length == 0) ? 'Your calendar is empty' : '',
        logged_in: this.visitor.loggedIn()
      };

      el.html(this.template(context));

      var collection = this.collection;
      var self       = this;

      this.collection.each(function(show) {
        el.find('ol').append(new Fancy.SavedShowItemView({'model': show, 'visitor': self.visitor}).render().el);
      });
    }
  });

  Fancy.UI = Backbone.View.extend({
    el: $('body'),

    events: {
      'click a.save-show-action': 'toggleShowSavedState',
      'click a.login':            'login',
      'click a.logout':           'logout'
    },
    
    initialize: function(options) {
      this.facebookAppId = options.facebookAppId;
      
      this.visitor           = new Fancy.Visitor();
      this.shows             = new Fancy.ShowList();
      this.upcomingShowsView = new Fancy.SavedShowListView({collection: this.visitor.upcomingShows, visitor: this.visitor});
      this.postLoginQueue    = [];

      this.visitor.set(this.visitor.parse(options.visitor));
      this.shows.refresh(_.map(options.shows, parseShowJSON));

      this._initDisplayCompat();
      this._initAuth();
      this._initEvents();

      this.upcomingShowsView.render();

      if(this.visitor.loggedIn()) {
        this.visitor.trigger('auth:login');
      }
    },
    
    _parseShows: function(response) { 
      response.date      = parseDateTime(response.date);
      response.show_time = parseDateTime(response.show_time);
      response.door_time = parseDateTime(response.door_time);

      return response;
    },

    _initDisplayCompat: function() {
      var root = $(this.el);

      root.filter('.show-featured').each(function(showEl) {
        $(showEl).css('position', 'absolute');
 	    });
 	    
 	    if(!Modernizr.textshadow) {
        root.filter('.show-featured h2').each(this._createShadow);
        root.filter('.show-featured .venue').each(this._createShadow);
      }
    },
    
    toggleShowSavedState: function(event) {
      var self   = this;
      var showId = $(event.target).parents('.show').attr('data-show-id');
      var show   = this.shows.get(showId);
      // FIXME this is probably less than ideal
      var saved  = this.visitor.upcomingShows.get(showId);
      
      var handleToggle = function() {
        if(saved) {
          self.visitor.removeShow(saved);
        } else {
          self.visitor.addShow(show);
        }
      }

      if(!this.visitor.loggedIn()) {
        this.postLoginQueue.push(handleToggle);
        this.login();
      } else {
        handleToggle();
      }
      
      return false;
    },

    _initEvents: function() {
      var self  = this;
      var shows = $(this.el).find('.show-featured');
      
      this.visitor.upcomingShows.bind('add', function(show) {
        shows.each(function() {
          if(this.getAttribute('data-show-id') == show.id) {
           $(this).addClass('show-saved') 
          }
        });
      });
      
      this.visitor.upcomingShows.bind('remove', function(show) {        
        shows.each(function() {
          if(this.getAttribute('data-show-id') == show.id) {
           $(this).removeClass('show-saved') 
          }
        });
      });
      
      this.visitor.bind('auth:login', function() {
        $('body').removeClass('logged_out').addClass('logged_in');
        _.each(self.postLoginQueue, function(cb) { cb() });
      });
      
      this.visitor.bind('auth:logout', function() {
        $('body').removeClass('logged_in').addClass('logged_out');
        self.postLoginQueue = [];
      });
    },
    
    _initAuth: function() {
      var self = this;

      FB.init({ appId:this.facebookAppId, cookie:true, status:true });
      
      FB.Event.subscribe('auth.sessionChange', function(response) {
        self._handleSessionChange(response);
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
    }
  });
});
