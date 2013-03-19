URL.internetradioFavorites = "/internetradio/web/getfavoriteslist";
URL.internetradioAddFavorite = "/internetradio/web/addfavorite";
URL.internetradioRemoveFavorite = "/internetradio/web/removefavorite";
URL.internetradioRenameFavorite = "/internetradio/web/renamefavorite";
URL.internetradioStatus= "/internetradio/web/status";
URL.internetradioPlay = "/internetradio/web/play?";
URL.internetradioStop = "/internetradio/web/stopplaying";

var InternetRadioFavorite = Class.create({
	initialize: function(xml){
		this.name = getNodeContent(xml, 'e2favoritename', "");
		this.text = getNodeContent(xml, 'e2favoritetext', "");
		this.type = getNodeContent(xml, 'e2favoritetype', "");
		this.tags = getNodeContent(xml, 'e2favoritetags', "").split(' ');
		this.country = getNodeContent(xml, 'e2favoritecountry');
		this.homepage = getNodeContent(xml, 'e2favoritehomepage', "");

		this.json = {
			'name' : this.name,
			'text' : this.text,
			'type' : this.type,
			'tags' : this.tags,
			'country' : this.country,
			'homepage' : this.homepage
		};
	},

	toJSON: function(){
		return this.json;
	}

});

var InternetRadioFavoriteList = Class.create({
	initialize: function(xml){
		this.list = this.parse(xml);
	},

	parse: function(xml){
		var items = xml.getElementsByTagName("e2internetradio_favorite_item");
		var list = [];
		var len = items.length;
		for(var i = 0; i < len; i++){
			var fav = new InternetRadioFavorite(items[i]).toJSON();
			list.push(fav);
		}
		return list;
	},

	getArray: function(){
		return this.list;
	}
});

/**
 * MovieListProvider
 * Handles a list of movies including deleting actions
 */
var InternetRadioFavoritesProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super(URL.internetradioFavorites, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new InternetRadioFavoriteList(xml).getArray();
		return {favorites : list};
	}
});

var radioTemplateEngine = new TemplateEngine('/internetradio/tpl/')
var AbstractRadioContentHandler = Class.create(AbstractContentHandler,  {
	show: function(data){
		this.data = data;
		radioTemplateEngine.process(this.tpl, data, this.target, this.finished.bind(this));
	}
});

var InternetRadioFavoritesHandler  = Class.create(AbstractRadioContentHandler, {
	initialize: function($super, target, statusTarget, stopTarget){
		$super('tplFavorites', target);
		this.provider = new InternetRadioFavoritesProvider(this.show.bind(this));
		this.ajaxload = true;
		this.refresh = false;
		this.statusTarget = statusTarget;
		this.stopTarget = stopTarget;
	},
	getData: function(element){
		var fav = {
			name: unescape(element.readAttribute('data-name')),
			text: unescape(element.readAttribute('data-text')),
			type: unescape(element.readAttribute('data-type')),
			tags: unescape(element.readAttribute('data-tags')),
			country: unescape(element.readAttribute('data-country')),
			homepage: unescape(element.readAttribute('data-homepage'))
		};
		return fav;
	},

	add: function(form){
		var values = form.serialize(true);
		this.provider.refresh = true;
		this.provider.simpleResultQuery(
			URL.internetradioAddFavorite,
			{
				name : values.name,
				text: values.text,
				favoritetype : values.favoritetype,
				tags : values.tags,
				country : values.country,
				homepage : values.homepage
			},
			this.simpleResultCallback.bind(this)
		);
	},
	
	rename: function(form){
		var values = form.serialize(true);
		
		this.provider.refresh = false
		if(values.newname != null && values.newname != ""  && values.newname != values.name){
			this.provider.refresh = true;
			this.provider.simpleResultQuery(
				URL.internetradioRenameFavorite, 
				{
					name : values.name, 
					text: values.text, 
					favoritetype : values.favoritetype, 
					newname : values.newname
				},
				this.simpleResultCallback.bind(this)
			);
		}
	},
	
	remove: function(element){
		favorite = this.getData(element);

		var result = confirm( "Are you sure want to remove the internet Radiostation\n\n" +
				favorite.name + "\n\n" + 
				" from your favorites?");

		this.provider.refresh = result;
		if(result){
			this.provider.simpleResultQuery(
				URL.internetradioRemoveFavorite, 
				{
					name : favorite.name,
					text: favorite.text,
					favoritetype :favorite.type
				},
				this.simpleResultCallback.bind(this)
			);
		}
	},
	
	play: function(element) {
		favorite = this.getData(element);
		this.provider.simpleResultQuery(
			URL.internetradioPlay, 
			{
				name : favorite.name,
				url: favorite.text
			},
			this.simpleResultCallback.bind(this)
		);
	},
	
	quickPlay: function(form){
		var values = form.serialize(true);
		this.provider.simpleResultQuery(
			URL.internetradioPlay, 
			{
				name : values.name,
				url: values.text
			},
			this.simpleResultCallback.bind(this)
		);
	},
	
	stop: function(){
		this.provider.simpleResultQuery(
			URL.internetradioStop, 
			{},
			this.simpleResultCallback.bind(this)
		);
	},
	
	getStatus: function(){
		this.provider.simpleResultQuery(
			URL.internetradioStatus, 
			{},
			this.onStatusReady.bind(this)
		);
	},
	
	onStatusReady: function(transport){
		var result = this.provider.simpleResultRenderXML(this.provider.getXML(transport));
		$(this.statusTarget).update(result.getStateText());
		var stop = $(this.stopTarget);
		if(result.getState()){
			$(this.stopTarget).show();
		} else {
			$(this.stopTarget).hide();
		}
	}
	
});

var Controller = Class.create({
	initialize: function(handler){
		this.handler = handler;
		this.handler.onFinished.push(this.registerEvents.bind(this));
		this.handler.onFinished.push(this.onFinished.bind(this));
		this.eventsregistered = false;
	},

	registerEvents: function(){
		this.eventsregistered = true;
	},

	onFinished: function(){}
});

var InternetRadio = Class.create(Controller, {
	initialize: function($super, target, statusTarget, stopTarget){
		$super(new InternetRadioFavoritesHandler(target, statusTarget, stopTarget));
	},
	
	load: function(){
		this.handler.load();
	},

	play: function(element){
		this.handler.play(element);
	},
	
	quickPlay: function(form){
		this.handler.quickPlay(form);
	},

	stop: function(element){
		this.handler.stop(element);
	},

	add: function(form){
		this.handler.add(form);
	},

	remove: function(element){
		this.handler.remove(element);
	},

	rename: function(element){
		this.handler.rename(element);
	},
	
	getStatus: function(){
		this.handler.getStatus();
	}
});

var Radio = Class.create({
	initialize: function(){
		this.internetRadio = new InternetRadio('contentMain', 'currentText', 'stop');
		this.sessionProvider = new SessionProvider( this.onSessionAvailable.bind(this) );
		this.poller = null;
	},
	
	run: function(){
		debug("[Radio].run");
		this.sessionProvider.load({});
	},

	onSessionAvailable: function(sid){
		debug("[Radio].onSessionAvailable, " + sid)
		global_sessionid = sid;

		this.internetRadio.load();
		this.registerListeners();
		this.pollStatus();
	},
	
	pollStatus: function(){
		if(this.poller == null){
			var _this = this;
			this.poller = setInterval(_this.pollStatus.bind(this), 5000);
		}
		this.internetRadio.getStatus();
	},

	registerListeners: function(){
		var content =  $('contentMain');
		content.on(
			'click',
			'.item',
			function(event,element){
				event.stop();
				this.internetRadio.play(element);
			}.bind(this)
		);
		content.on(
			'click',
			'.edit',
			function(event, element){
				event.stop();
				var edit = element.up('.listItem').down('.editEntry');
				if(edit.visible())
					edit.hide();
				else
					edit.show();
			}
		);
		content.on(
			'change',
			'.removeConfirm',
			function(event, element){
				event.stop();
				var button = element.next();
				if(element.checked){
					button.enable();
				} else {
					button.disable();
				}
			}
		);
		content.on(
			'click',
			'.removeFav',
			function(event, element){
				event.stop();
				var entry = element.up('.listItem').down('.irListEntry');
				this.internetRadio.remove(entry);
			}.bind(this)
		);
		
		content.on(
			'click',
			'.renameFav',
			function(event, element){
				event.stop();
				var id = element.readAttribute("data-form-id");
				var form = $(id);
				this.internetRadio.rename(form);
			}.bind(this)
		);
		content.on(
			'click',
			'.quickplay',
			function(event, element){
				event.stop();
				var form = $('new');
				this.internetRadio.quickPlay(form);
			}.bind(this)
		);
		content.on(
			'click',
			'.savenew',
			function(event, element){
				event.stop();
				var form = $('new');
				this.internetRadio.add(form);
			}.bind(this)
		);
		$('stop').on(
			'click',
			function(event, element){
				event.stop();
				this.internetRadio.stop();
			}.bind(this)
		);
		$('newStation').on(
			'click',
			function(event, element){
				event.stop();
				var form = $('new');
				if(form.visible()){
					form.hide();
				} else {
					form.show();
					$('contentMain').scrollTop = 0;
				}
			}.bind(this)
		);
	}
});
var radio = new Radio();

