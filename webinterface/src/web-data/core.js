Element.prototype.fadeIn = function(parms, out) {
		var _this = this;
		var opacityTo = function(elm,v){
		    elm.style.opacity = v/100;		 
		    elm.style.MozOpacity =  v/100;		 
		    elm.style.KhtmlOpacity =  v/100;		 
		    elm.style.filter=" alpha(opacity ="+v+")";
		};
		var delay = parms.delay;
		var to = parms.to;
		if(!to)
			to = 100;
		
		_this.style.zoom = 1;
		// for ie, set haslayout
		_this.style.display = "block";
	
		for (var i=1; i<=to; i++) {
			(function(j) {
				setTimeout(function() {
					if (out == true)
						j = to - j;
					opacityTo(_this, j);
				}, j * delay / to);
			})(i);
		};
	};
Element.prototype.fadeOut = function(delay) {
		this.fadeIn({'delay' : delay}, true);
	};

// General Helpers
function toOptionList(lst, selected) {
	var list = Array();
	var i = 0;
	var found = false;

	for (i = 0; i < lst.length; i++) {
		if (lst[i] == selected) {
			found = true;
		}
	}

	if (!found) {
		lst = [ selected ].concat(lst);
	}

	for (i = 0; i < lst.length; i++) {
		list[i] = {
				'value': lst[i],
				'txt': lst[i],
				'selected': (lst[i] == selected ? "selected" : " ")};
	}

	return list;
}

function debug(item){
	if(userprefs.data.debug)
		console.log(item);
}

function parseNr(num) {
	if(isNaN(num)){
		return 0;
	} else {
		return parseInt(num);
	}
}

var Controller = Class.create({
	initialize: function(model){
		this.model = model;
		this.model.onFinished[this.model.onFinished.length] = this.registerEvents.bind(this);
		this.model.onFinished[this.model.onFinished.length] = this.onFinished.bind(this);
		this.eventsregistered = false;
	},

	registerEvents: function(){
		this.eventsregistered = true;
	},
	
	onFinished: function(){}
});

var Bouquets = Class.create(Controller, {
	initialize: function($super, targetBouquets, targetMain){
		$super(new BouquetListHandler(targetBouquets, targetMain));
		this.loadFirstOnFinished = false;
	},
	
	load: function(sRef, loadFirstOnFinished){
		if(loadFirstOnFinished)
			this.loadFirstOnFinished = true;
		this.model.load( {'sRef' : sRef} );
	},
	
	loadBouquetsTv: function(){
		this.load(bouquetsTv);
	},
	
	loadProviderTv: function(){
		this.load(providerTv);
	},
	
	loadSatellitesTv: function(){
		this.load(satellitesTv);
	},
	
	loadBouquetsRadio: function(){
		this.load(bouquetsRadio);
	},
	
	loadProviderRadio: function(){
		this.load(providerRadio);
	},
	
	loadSatellitesRadio: function(){
		this.load(satellitesRadio);
	},
	
	onFinished: function(){
		var bouquet = this.model.data.bouquets[0];
		if(bouquet){
			setContentHd(bouquet.servicename);
			if(this.loadFirstOnFinished){
				this.loadFirstOnFinished = false; 
				hash = core.getBaseHash() + '/' + bouquet.servicereference;
				hashListener.setHash(hash);
			}
		}
	}
});

var Current = Class.create(Controller, {
	initialize: function($super, curTarget, volTarget){
		$super(new CurrentHandler(curTarget, volTarget));
		this.model.onFinished[this.model.onFinished.length] = this.restoreDisplayStyle.bind(this);
	},
	
	load: function(){
		var ext = $('trExtCurrent'); 
		if(ext != null){
			this.display = $('trExtCurrent').style.display;
		}
		this.model.load({});
	},
	
	restoreDisplayStyle: function(){
		var ext = $('trExtCurrent'); 
		if(ext != null){
			ext.style.display = this.display;
		}
	}
});

var EPG = Class.create(Controller, {
	initialize: function($super){
		$super(new EpgListHandler(this.show.bind(this)));
		this.window = '';
	},
	
	show:function(html){
		if (this.window.closed || !this.window.location){
			this.eventsregistered = false;
			this.window = core.popup("EPG", html, 900, 500);
			this.doRegisterEvents();
		}
	},
	
	load: function(sRef){
		this.model.load({'sRef' : sRef});
	},

	search: function(needle){
		this.initWindow();
		this.model.search({'search' : needle});
	},
	
	doRegisterEvents: function(){
		if(!this.eventsregistered){
			this.eventsregistered = true;				
			var win = this.window;
			var elem = win.document;
			var onload = function(event){
				elem.on(
					'click',
					'.eListAddTimer',
					function(event, element){
						debug('eListAddTimer');
					}
				);
				elem.on(
					'click',
					'.eListZapTimer',
					function(event, element){
						debug('eListZapTimer');
					}
				);
				elem.on(
					'click',
					'.eListEditTimer',
					function(event, element){
						debug('eListEditTimer');
					}
				);
			};
			if(typeof(elem.on) == "function"){
				onload();
			} else {
				win.onload = onload;
			}
			
		}
	}
});

var Power = Class.create({
	STATES: {'toggle' : 0, 'deep' : 1, 'reboot' : 2, 'gui' : 3},
	
	initialize: function(){
		this.provider = new PowerstateProvider(this.onLoadFinished.bind(this));
		this.callbacks = [];
		this.isLoading = false;
		this.isStandby = false;
	},
	
	load: function(params){
		this.isLoading = true;
		this.provider.load(params);
	},
	
	onLoadFinished:function (isStandby){
		this.isStandby = isStandby;
		this.isLoading = false;
		var len = this.callbacks.length;
		for(var i = 0; i < len; i++){
			callback = this.callbacks.pop();
			callback(this.isStandby);
		}
	},
	
	isStandby: function(callback){
		this.callbacks[this.callbacks.length] = callback;
		if(!this.sLoading){
			this.load({});
		}
	},
	
	set: function(newstate, callback){
		this.callbacks[this.callbacks.length] = callback;
		this.load({'newstate' : this.STATES[newstate]});
	}
});

var LocationsAndTags = Class.create({
	initialize: function(){
		this.currentLocation = '';
		this.locations = [];
		this.tags = [];
		this.isCurrentLocationsLoading = false;
		this.isCurrentLocationReady = false;
		this.isLocationsLoading = false;
		this.isLocationsReady = false;
		this.isTagsLoading = false;
		this.isTagsReady = false;
		this.curLocCallbacks = [];
		this.locCallbacks = [];
		this.tagCallbacks = [];
		this.locTagCallbacks = [];
		
		this.curlocprovider = new CurrentLocationProvider(this.onCurrentLocationAvailable.bind(this));
		this.locprovider = new LocationProvider(this.onLocationsAvailable.bind(this));		
		this.tagprovider = new TagProvider(this.onTagsAvailable.bind(this));
	},
	
	getCurrentLocation: function(callback){
		if(this.isCurrentLocationReady){
			callback(this.currentLocation);
		} else {
			this.curLocCallbacks[this.curLocCallbacks.length] = callback;
			if(!this.isCurrentLocationLoading){
				this.curlocprovider.load({});
				this.isCurrentLocationLoading = true;
			}
		}
	},
	
	onCurrentLocationAvailable: function(currentLocation){
		debug("[LocationsAndTags].onCurrentLocationAvailable");
		this.isCurrentLocationReady = true;
		this.isCurrentLocationLoading = false;
		this.currentLocation = currentLocation;
		var len = this.curLocCallbacks.length;
		for(var i = 0; i < len; i++){
			callback = this.curLocCallbacks.pop();
			callback(this.currentLocation);
		}
		this.onLocationsOrTagsAvailable();
	},
	
	getLocations: function(callback){
		if(this.isLocationsReady){
			callback(this.locations);
		} else {
			this.locCallbacks[this.locCallbacks.length] = callback;
			if(!this.isLocationsLoading){
				this.locprovider.load({});
				this.isLocationsLoading = true;
			}
		}
	},
	
	onLocationsAvailable: function(locations){
		debug("[LocationsAndTags].onLocationsAvailable");
		this.isLocationsReady = true;
		this.isLocationsLoading = false;
		this.locations = locations.getList();
		var len = this.locCallbacks.length;
		for(var i = 0; i < len; i++){
			callback = this.locCallbacks.pop();
			callback(this.locations);
		}
		this.onLocationsOrTagsAvailable();
	},
	
	getTags: function(callback){
		if(this.isTagsReady){
			callback(this.tags);
		} else {
			this.tagCallbacks[this.tagCallbacks.length] = callback;
			if(!this.isTagsLoading){
				this.tagprovider.load({});
				this.isTagsLoading = true;
			}
		}
	},
	
	onTagsAvailable: function(tags){
		debug("[LocationsAndTags].onTagsAvailable");
		this.isTagsReady = true;
		this.isTagsLoading = false;
		this.tags = tags.getList();
		var len = this.tagCallbacks.length;
		for(var i = 0; i < len; i++){
			callback = this.tagCallbacks.pop();
			callback(this.tags);
		}
		this.onLocationsOrTagsAvailable();
	},
	
	getLocationsAndTags: function(callback){
		if(this.isCurrentLocationReady && this.isLocationsReady && this.isTagsReady){
			callback(this.currentLocation, this.locations, this.tags);
		} else {
			this.locTagCallbacks[this.locTagCallbacks.length] = callback;
			if(!this.isCurrentLocationLoading)
				this.curlocprovider.load({});
			if(!this.isLocationsLoading)
				this.locprovider.load({});
			if(!this.isTagsLoading)
				this.tagprovider.load({});
		}
	},
	
	onLocationsOrTagsAvailable: function(){
		if(this.isCurrentLocationReady && this.isLocationsReady && this.isTagsReady){
			var len = this.locTagCallbacks.length;
			for(var i = 0; i < len; i++){
				callback = this.locTagCallbacks.pop();
				callback(this.currentLocation, this.locations, this.tags);
			}
		}
	}
});

var Messages = Class.create({
	initialize: function(){
		this.model = new SimpleRequestHandler();
	},
	
	send: function(text, type, timeout){
		this.model.load(URL.message, {'text' : text, 'type' : type, 'timeout' : timeout});
	}
});

var Movies = Class.create(Controller, {
	initialize: function($super, listTarget, navTarget){
		$super(new MovieListHandler(listTarget));
		this.navModel = new MovieNavHandler(navTarget);
	},
	
	load: function(location, tags){	
		if(!location){
			var sethash = function(location){
				var hash = [core.getBaseHash(), encodeURIComponent(location), encodeURIComponent(tags)].join("/");
				hashListener.setHash(hash);
			};
			if(core.currentLocation == ""){ //wait for currentLocation to be set;
				core.lt.getCurrentLocation(sethash);
			} else {
				sethash(core.currentLocation);
			}
			return;
		}
				
		this.model.load({'dirname' : location, 'tag' : tags});
	},
	
	loadNav: function(){
		core.lt.getLocationsAndTags(this.showNav.bind(this));
	},
	
	showNav: function(currentLocation, locations, tags){
		this.navModel.load(toOptionList(locations, currentLocation), toOptionList(tags));
	},
	
	del: function(element){
		this.model.del(element);
	}
});

var RemoteControl = Class.create({
	initialize: function(){
		this.model = new RemoteControlHandler();
		this.window = '';
	},
	
	open: function(){
		if(!this.window)
			this.window = '';
		if (this.window.closed || !this.window.location){
			var tpl;
			switch(core.deviceInfo.info.devicename){
			case 'dm8000':
			case 'dm7020hd':
				tpl = 'tplWebRemote';
				break;
			default:
				tpl = 'tplWebRemoteOld';
			}
			
			templateEngine.fetch(tpl, function(template){
				this.eventsregistered = false;
				this.window = core.popup('WebRemote', template, 250, 600);
				this.registerEvents();
			}.bind(this));
		}
	},
	
	sendKey: function(cmd, type, shotType){
		debug("[RemoteControl].sendKey: " + cmd); 
		this.model.sendKey({'command' : cmd, 'type': type});
		
		var hash = '!/control'; //FIXME
		switch(shotType){		
		case undefined:
		case '':
			return;
		case 'osd':
			hash = [hash, 'osdshot'].join("/");
			break;
		case 'all':
			hash = [hash, 'screenshot'].join("/");
			break;
		}
		//the box needs at least a little bit of time to actually draw the window
		//wait 250ms before fetching a new screenshot
		setTimeout(
				function(){
					hashListener.setHash(hash);
					if(hash == hashListener.getHash()){
						core.onHashChanged(true);
					}
				},
				250);
	},
	
	registerEvents:function(){
		var _this = this;
		var win = this.window;		
		var elem = win.document;
		
		var onload = function(event){			
			elem.on(
				'click',
				'.remoteKey',
				function(event, element){
					var id = element.readAttribute('data-keyid');
					var long = _this.window.document.getElementById('long').checked;
					var screenshot = _this.window.document.getElementById('screenshot').checked;
					var video = _this.window.document.getElementById('video').checked;
					var type = '';
					if(long){
						type = 'long';
					}
					var shotType = 'none';
					if(screenshot && video){
						shotType = 'all';
					} else if (screenshot && !video) {
						shotType = 'osd';
					}
					_this.sendKey(id, type, shotType);
				}
			);
		};
		if(typeof(elem.on) == "function"){
			onload();
		} else {
			win.onload = onload;
		}
	}
});

var Screenshots = Class.create(Controller, {
	TYPE_OSD : 'o',
	TYPE_VIDEO : 'v',
	TYPE_ALL : '',
	
	initialize: function($super, target){
		$super(new ScreenshotHandler(target));
	},
	
	load: function(type){
		var filename = '/tmp/' + new Date().getTime();
		var params = {'format' : 'jpg', 'r': '720', 'filename' : filename};
		
		switch(type){
			case this.TYPE_OSD:
				params['o'] = '';
				params['n'] = '';
				break;
			case this.TYPE_VIDEO:
				params['v'] = '';
				break;
			default:
				break;
		}
		this.model.load(params);		
	},

	shootOsd: function(){
		this.load(this.TYPE_OSD);
	},
	
	shootVideo: function(){
		this.load(this.TYPE_VIDEO);
	},
	
	shootAll: function(){
		this.load(this.TYPE_ALL);
	}
});

var Services = Class.create(Controller, {
	initialize: function($super, target, epg){
		$super(new ServiceListHandler(target));
		this.epg = epg;
		this.cachedServiceElements = null;
	},
	
	zap: function(sRef){
		this.model.zap({'sRef' : sRef});
	},
	
	load: function(sRef){
		this.model.load({'bRef' : sRef});
	},
	
	getNowNext: function(){
		this.model.getNowNext();
	},
	
	getSubservices: function(){
		this.model.getSubservices();
	},
	
	loadAllTv: function(){
		this.load(allTv);
		setContentHd("All (Tv)");
	},

	loadAllRadio: function(){
		this.load(allRadio);
		setContentHd("All (Radio)");
	},
	
	onFilterFocus: function(event){
		event.element().value = '';
		this.cachedServiceElements = null;
		this.filter(event);
	},

	filter: function(event){
		var needle = event.element().value.toLowerCase();
		
		if(cachedServiceElements == null){
			cachedServiceElements = $$('.sListRow');
		}
		
		for(var i = 0; i < cachedServiceElements.length; i++){
			var row = cachedServiceElements[i];
			var serviceName = row.readAttribute('data-servicename').toLowerCase();
			
			if(serviceName.match(needle) != needle && serviceName != ""){
				row.hide();
			} else {		
				row.show();
			}
		}
	},
	
	addFilterInput: function(){
		var input = new Element('input');
		input.id = 'serviceFilter';
		input.value = 'Filter Services';		
		$('contentHdExt').update(input);		
		input.on('focus', this.onFilterFocus.bind(this));
		input.on('keyup', this.filter.bind(this));	
	},
	
	onFinished: function(){
		this.addFilterInput();
		core.startUpdateBouquetItemsPoller();
	}
});

var SimplePages = Class.create({
	PAGE_ABOUT : 'tplAbout',
	PAGE_GEARS : 'tplGears',
	PAGE_MESSAGE : 'tplSendMessage',
	PAGE_POWER : 'tplPower',
	PAGE_SETTINGS: 'tplSettings',
	PAGE_TOOLS: 'tplTools',
	
	initialize: function(target){
		this.simpleHandler = new SimplePageHandler(target);
		this.deviceInfoHandler = new DeviceInfoHandler(target);
	},
	
	show: function(tpl, data){
		if(!data)
			data = {};
		this.simpleHandler.show(tpl, data);
	},

	loadAbout: function(){
		this.show(this.PAGE_ABOUT);
	},
	
	loadGears: function(){
		var enabled = false;
		
		if (window.google && google.gears){
			enabled = gearsEnabled();
		}
		
		data = { 'useGears' : enabled };
		this.show(this.PAGE_GEARS, data);
	},
	
	loadMessage: function(){
		this.show(this.PAGE_MESSAGE);
	},
	
	loadPower: function(){
		this.show(this.PAGE_POWER);
	},
	
	loadSettings: function(){
		var debug = userprefs.data.debug;
		var debugChecked = "";
		if(debug){
			debugChecked = 'checked';
		}
		
		var updateCurrentInterval = userprefs.data.updateCurrentInterval / 1000;
		var updateBouquetInterval = userprefs.data.updateBouquetInterval / 1000;

		data = {'debug' : debugChecked,
				'updateCurrentInterval' : updateCurrentInterval,
				'updateBouquetInterval' : updateBouquetInterval
		};
		this.show(this.PAGE_SETTINGS, data);
	},
	
	loadTools: function(){
		this.show(this.PAGE_TOOLS);
	},
	
	loadDeviceInfo: function(){
		this.deviceInfoHandler.load({});
	},
	
	getDeviceInfo: function(callback){
		this.deviceInfoHandler.get({}, callback);
	}
});

var Timers = Class.create({
	initialize: function(target){
		this.listHandler = new TimerListHandler(target);
		this.timerHandler = new TimerHandler(target, this.loadList.bind(this));
	},
	
	loadList: function(){
		this.listHandler.load({});
	},
	
	create: function(){
		//TODO create Timer;
	},
	
	edit: function(element){
		this.timerHandler.load(element);
	},
	
	toggleDisabled: function(element){
		this.timerHandler.toggleDisabled(element);
	},
	
	del: function(element){
		this.timerHandler.del(element);
	}
});

var Volume = Class.create(Controller, {
	initialize: function($super, target){
		$super(new VolumeHandler(target));
	},
	
	load: function(){
		this.model.load({});
	},
	
	set: function(value){
		this.model.load({'set' : value});
	}
});

var E2WebCore = Class.create({
	initialize: function(){	
		this.mediaPlayerStarted = false; 
		this.popUpBlockerHinted = false;
		this.settings = null;
		this.parentControlList = null;

		this.debugWin = '';
		this.signalWin = '';
		this.webRemoteWin = '';
		this.EPGListWin = '';

		this.currentBouquet = bouquetsTv;

		this.updateBouquetItemsPoller = '';
		this.updateCurrentPoller = '';
		this.signalPanelUpdatePoller = '';

		this.hideNotifierTimeout = '';

		this.isActive = {};
		this.isActive.getCurrent = false;
		
		this.locationsList = [];
		this.tagList = [];

		this.boxtype = "dm8000";
		this.mode = "";
		this.subMode = "";
		
		//create required Instances
		this.bouquets = new Bouquets('contentBouquets', 'contentMain');
		this.current = new Current('currentContent', 'volContent');
		this.epg = new EPG(new EpgListHandler());
		this.lt = new LocationsAndTags();
		this.messages = new Messages();
		this.movies = new Movies('contentMain', 'navContent');
		this.power = new Power();
		this.remote = new RemoteControl();
		this.services = new Services('contentServices', this.epg);
		this.screenshots = new Screenshots('contentMain');
		this.simplepages = new SimplePages('contentMain');
		this.timers = new Timers('contentMain');
		this.volume = new Volume('volContent');
		
		this.currentLocation = this.lt.getCurrentLocation(function(location){this.currentLocation = location;}.bind(this));
		this.deviceInfo = this.simplepages.getDeviceInfo(function(info){this.deviceInfo = info;}.bind(this));
		
		this.navlut = {
			'tv': {
				'bouquets' : this.bouquets.loadBouquetsTv.bind(this.bouquets), 
				'provider' : this.bouquets.loadProviderTv.bind(this.bouquets),
				'all' : this.services.loadAllTv.bind(this.services)
				},
			'radio': {
				'bouquets' : this.bouquets.loadBouquetsRadio.bind(this.bouquets),
				'provider' : this.bouquets.loadProviderRadio.bind(this.bouquets),
				'all' : this.services.loadAllRadio.bind(this.services)
			},
			'movies':{
				'filter' : function(){} //DON'T TOUCH THIS!
			},
			'timer': {
				'create' : this.timers.create.bind(this.timers), //TODO create Timer
				'edit' : false,
				'delete' : false,
				'toggle' : false
			},
			'control': {
				//TODO add & use controller for Boxcontrols
				'message' : this.simplepages.loadMessage.bind(this.simplepages),
				'power' : this.simplepages.loadPower.bind(this.simplepages),
				'remote' : function(){}, //TODO loadControl
				'osdshot' : this.screenshots.shootOsd.bind(this.screenshots),
				'screenshot' : this.screenshots.shootAll.bind(this.screenshots),
				'videoshot' : this.screenshots.shootVideo.bind(this.screenshots)
			},
			'extras': {
				'about' : this.simplepages.loadAbout.bind(this.simplepages),
				'deviceinfo' : this.simplepages.loadDeviceInfo.bind(this.simplepages),
				'gears' : this.simplepages.loadGears.bind(this.simplepages),
				'settings' : this.simplepages.loadSettings.bind(this.simplepages),
				'tools' : this.simplepages.loadTools.bind(this.simplepages)
			}
		};
	},
	
	hideNotifier: function(){
		debug("[E2WebCore].hideNotifier");
		$('notification').fadeOut(500);
	},

	notify: function(text, state){
		debug("[E2WebCore].notify");
		notif = $('notification');

		if(notif !== null){
			//clear possibly existing hideNotifier timeout of a previous notfication
			clearTimeout(this.hideNotifierTimeout);
			if(state === false){
				notif.style.background = "#C00";
			} else {
				notif.style.background = "#85C247";
			}				

			this.set('notification', "<div>"+text+"</div>");
			notif.fadeIn({'delay' : 500, 'to' : 90});
			var _this = this;
			this.hideNotifierTimeout = setTimeout(_this.hideNotifier.bind(this), 5000);
		}
	},
	
	set: function(element, value){
		element = parent.$(element);
		if (element){
			element.update(value);
		}
	},
	
	setAjaxLoad: function(targetElement){
		target = $(targetElement);
		if(target != null){
			target.update( getAjaxLoad() );
		}
	},
	
	messageBox: function(message){
		alert(message);
	},
	
	popUpBlockerHint: function(){
		if(!this.popUpBlockerHinted){
			this.popUpBlockerHinted = true;
			this.messageBox("Please disable your Popup-Blocker for enigma2 WebControl to work flawlessly!");

		}
	},
	
	setWindowContent: function(window, html){
		window.document.write(html);
		window.document.close();
	},
	
	popup: function(title, html, width, height, x, y){
		try {
			var popup = window.open('about:blank',title,'scrollbars=yes, width='+width+',height='+height);		
			this.setWindowContent(popup, html);
			return popup;
		} catch(e){
			this.popUpBlockerHint();
			return "";
		}
	},
	
	updateItems: function(){
		debug("[E2WebCore].updateItems");
		this.current.load();
	},

	updateItemsLazy: function(){
		debug("[E2WebCore].updateItemsLazy");
		this.services.getNowNext();
		this.services.getSubservices();
	},
	
	startUpdateCurrentPoller: function(){
		debug("[E2WebCore].startUpdateCurrentPoller");
		clearInterval(this.updateCurrentPoller);
		var _this = this;
		this.updateCurrentPoller = setInterval(_this.updateItems.bind(this), userprefs.data.updateCurrentInterval);
	},
	
	stopUpdateCurrentPoller: function(){
		clearInterval(this.updateCurrentPoller);
	},
	
	startUpdateBouquetItemsPoller: function(){
		debug("[E2WebCore].startUpdateBouquetItemsPoller");
		clearInterval(this.updateBouquetItemsPoller);
		var _this = this;
		this.updateBouquetItemsPoller = setInterval(_this.updateItemsLazy.bind(this), userprefs.data.updateBouquetInterval);
	},
	
	stopUpdateBouquetItemsPoller: function(){
		debug("[E2WebCore].stopUpdateBouquetItemsPoller");
		clearInterval(this.updateBouquetItemsPoller);
	},
	
	onHashChanged: function(isReload){
		var hash = hashListener.getHash();		
		var parts = hash.split("/");
	
		var len = parts.length;
		if(len >= 2){
			var mode = parts[1];
			if(mode != this.mode || isReload || ( len <= 2 && this.subMode != '') ){
				this.switchMode(mode);
				this.subMode = '';
			}
			this.mode = mode;
			if(len > 2){
				var subMode = parts[2];
				if(subMode != this.subMode || isReload){
					this.subMode = subMode;
					if(!this.navlut[this.mode][this.subMode]){
						return;
					} else {
						this.navlut[this.mode][this.subMode]();
					}
				}				
				if(len > 3){
					switch(this.mode){
					case 'tv':
					case 'radio':
						this.services.load(unescape(parts[3]));
						break;
					case 'movies':
						var location = decodeURIComponent(parts[3]);						
						this.currentLocation = location;
						this.movies.load(decodeURIComponent(parts[3]), decodeURIComponent(parts[4]));
					default:
						return;
					}
				}
			}
		}
	},
	
	getBaseHash: function(){
		var hash = ['#!', this.mode].join("/");
		if(this.subMode != ''){
			hash = [hash, this.subMode].join("/");
		}
		return hash;
	},
	
	loadDefault: function(){
		debug("[E2WebCore].loadDefault");
		this.switchMode('tv');
		this.mode = 'tv';
		this.subMode = 'bouquets';
		this.bouquets.load(bouquetsTv, true);
	},

	run: function(){
		debug("[E2WebCore].run");
		if( parseNr(userprefs.data.updateCurrentInterval) < 10000){
			userprefs.data.updateCurrentInterval = 120000;
			userprefs.save();
		}
		
		if( parseNr(userprefs.data.updateBouquetInterval) < 60000 ){
			userprefs.data.updateBouquetInterval = 300000;
			userprefs.save();
		}
		
		if (typeof document.body.style.maxHeight == undefined) {
			alert("Due to the tremendous amount of work needed to get everthing to " +
			"work properly, there is (for now) no support for Internet Explorer Versions below 7");
		}
		hashListener.onHashChanged = this.onHashChanged.bind(this);
		hashListener.init();
		
		this.registerEvents();
		
//		TODO getBoxtype();

		this.setAjaxLoad('navContent');
		this.setAjaxLoad('contentMain');

		templateEngine.fetch('tplServiceListEPGItem');
		templateEngine.fetch('tplBouquetsAndServices');
		templateEngine.fetch('tplCurrent');
		if(hashListener.getHash().length >= 1){
			this.onHashChanged();
		} else {
			this.loadDefault();
		}
		this.updateItems();
		this.startUpdateCurrentPoller();		
	},
	
	registerEvents: function(){
		debug("[E2WebCore].registerEvents");
		//Hash-Reload-Fix
		//HACK THIS IS EVIL VOODOO, DON'T TRY THIS AT HOME!
		document.on(
			'click',
			'a',
			function(event, element){ 
				var parts = element.href.split('#');
				var curHost = window.location.href.split('#')[0];
				//Don't do this crazy stuff when the target is another host!
				if(curHost == parts[0]){
					if (parts.length > 1){
						if(parts[1] != ''){
							if(window.location == element.href){
								this.onHashChanged(true);
								return;
							}else{
								window.location == element.href;
								return;
							}
						} else {
							element.href = window.location;
						}
						return false;
					}
				}
			}.bind(this)
		);
		//Current
		$('current').on(
			'click',
			'.currentExtShowHide',
			function(event, element){
				//FIXME
				element.href = '#';	
				var ext = $('trExtCurrent');
				if(ext){
					if(ext.visible())
						ext.hide();
					else
						ext.show();
				}
			}
		);
		//EPG-Search
		$('epgSearchForm').on(
			'submit',
			function(event, element){
				this.epg.search($F('epgSearch'));
				return false;
			}.bind(this)
		);		
		$('epgSearch').on(
			'focus',
			function(event, element){
				element.value = "";
			}.bind(this)
		);		
		$('epgSearchClear').on(
				'click',
				function(event, element){
					$('epgSearch').value = '';
					return false;
				}.bind(this)
		);		
		//Movienav
		var nav = $('navContent');
		nav.on(
			'change',
			'.mNavLoc',
			function(event, element){
				debug($("locations").value);
				debug($("tags").value);
				var hash = [this.getBaseHash(), encodeURIComponent($("locations").value), encodeURIComponent($("tags").value)].join("/");
				hashListener.setHash(hash);
			}.bind(this)
		);
		
		nav.on(
			'change',
			'.mNavTags',
			function(event, element){
				debug($("locations").value);
				debug($("tags").value);
				var hash = [this.getBaseHash(), encodeURIComponent($("locations").value), encodeURIComponent($("tags").value)].join("/");
				hashListener.setHash(hash);
			}.bind(this)
		);
		//RemoteControl
		nav.on(
			'click',
			'.webremote',
			this.remote.open.bind(this.remote)
		);
		//Volume
		$('navVolume').on(
			'click',
			'a.volume',
			function(event, element){
				this.volume.set(element.readAttribute('data-volume'));
				return false;
			}.bind(this)
		);
		
		//Content
		var content = $('contentMain');
		//Message
		content.on(
			'click',
			'.messageSend',
			function(event, element){
				var t = $('messageType');
				text = $('messageText').value;
				timeout = $('messageTimeout').value;
				type = t.options[t.selectedIndex].value;
				this.messages.send(text, type, timeout);
			}.bind(this)
		);
		//Movielist
		content.on(
			'click', 
			'a.mListDelete', 
			function(event, element){
				//FIXME
				element.href = '#';				
				this.movies.del(element);
				return false;
			}.bind(this)
		);
		//Powerstate
		content.on(
			'click',
			'.powerState',
			function(event, element){
				var cb = function(isStandby){
					var text = "Device is now Running";
					if(isStandby)
						text = "Device is now in Standby";
					this.notify(text, true);
				}.bind(this);
				this.power.set(element.readAttribute("data-state"), cb);
			}.bind(this)
		);
		//Settings
		content.on(
			'click',
			'.saveSettings',
			function(event, element){
				this.saveSettings();
			}.bind(this)
		);
		//Servicelist
		content.on(
			'click', 
			'a.sListSLink', 
			function(event, element){
				//FIXME
				element.href = '#';				
				this.services.zap(unescape(element.id));
				return false;
			}.bind(this)
		);
		content.on(
			'click', 
			'a.sListServiceEpg', 
			function(event, element){
				//FIXME
				element.href = '#';
				var ref = unescape( element.readAttribute('data-servicereference') );
				this.epg.load(ref);
				return false;
			}.bind(this)
		);
		content.on(
			'click', 
			'a.sListExtEpg',
			function(event, element){
				//FIXME
				element.href = '#';
				var target = element.down('.sListExtEpgLong');
				if(target){
					if(target.visible()){
						target.hide();
					} else {
						target.show();
					}
				}
				return false;
			}.bind(this)
		);
		//Timerlist
		content.on(
			'click', 
			'.tListDelete', 
			function(event, element){		
				this.timers.del(element);
				return false;
			}.bind(this)
		);
		content.on(
			'click', 
			'.tListToggleDisabled', 
			function(event, element){
				this.timers.toggleDisabled(element);
				return false;
			}.bind(this)
		);
		content.on(
			'click', 
			'.tListEdit', 
			function(event, element){
				var hash = [this.getBaseHash(), "edit"].join("/");
				hashListener.setHash(hash);
				this.timers.edit(element);
				return false;
			}.bind(this)
		);
	},

	/*
	 * Loads another navigation template and sets the navigation header
	 * @param template - The name of the template
	 * @param title - The title to set for the navigation
	 */
	reloadNav: function(template, title){
		this.setAjaxLoad('navContent');
		templateEngine.process(template, null, 'navContent');
		setNavHd(title);
	},

	reloadNavDynamic: function(fnc, title){
		this.setAjaxLoad('navContent');
		setNavHd(title);
		fnc();
	},

	/*
	 * Loads dynamic content to $(contentMain) by calling a execution function
	 * @param fnc - The function used to load the content
	 * @param title - The Title to set on the contentpanel
	 */
	loadContentDynamic: function(fnc, title){
		setContentHd(title);
		this.stopUpdateBouquetItemsPoller();
		fnc();
	},

	/*
	 * Loads a static template to $(contentMain)
	 * @param template - Name of the Template
	 * @param title - The Title to set on the Content-Panel
	 */
	loadContentStatic: function(template, title){
		this.setAjaxLoad('contentMain');
		setContentHd(title);
		this.stopUpdateBouquetItemsPoller();
		templateEngine.process(template, null, 'contentMain');
	},
	
	switchMode: function(mode){
		switch(mode){
		case "tv":
			if(this.mode != 'tv' && this.mode != 'radio'){
				this.services.registerEvents();
			}
			this.reloadNav('tplNavTv', 'TeleVision');
			break;
	
		case "radio":
			if(this.mode != 'TV' && this.mode != 'Radio'){
				this.services.registerEvents();
			}		
			this.reloadNav('tplNavRadio', 'Radio');
			break;
	
		case "movies":	
			this.reloadNavDynamic(this.movies.loadNav.bind(this.movies), 'Movies');
//			this.loadContentDynamic(this.movies.load.bind(this.movies), 'Movies');
			break;
	
		case "timer":
			this.reloadNav('tplNavTimer', 'Timer');
			this.loadContentDynamic(this.timers.loadList.bind(this.timers), 'Timer');
			break;
	
		case "mediaplayer":
			//TODO this.loadContentDynamic(loadMediaPlayer, 'MediaPlayer');
			debug("mediaplayer not implemented");
			break;
	
		case "control":
			this.reloadNav('tplNavBoxControl', 'BoxControl');
			break;
	
		case "extras":
			this.reloadNav('tplNavExtras', 'Extras');
			break;
			
		default:
			break;
		}
	},
	
	saveSettings: function(){
		userprefs.load();
		
		var debug = $('enableDebug').checked;
		var changed = false;
		if(debug != undefined){
			if( userprefs.data.debug != debug ){
				userprefs.data.debug = debug;
				changed = true;
			}
		}
		
		var updateCurrentInterval = parseNr( $F('updateCurrentInterval') ) * 1000;
		if( updateCurrentInterval < 10000){
			updateCurrentInterval = 120000;
		}
		
		if( userprefs.data.updateCurrentInterval != updateCurrentInterval){
			userprefs.data.updateCurrentInterval = updateCurrentInterval;
			
			changed = true;
			this.startUpdateCurrentPoller();
		}
		
		var updateBouquetInterval = parseNr( $F('updateBouquetInterval') )  * 1000;
		if( updateBouquetInterval < 60000){
			updateBouquetInterval = 300000;
		}
		
		if( userprefs.data.updateBouquetInterval != updateBouquetInterval){
			userprefs.data.updateBouquetInterval = updateBouquetInterval;
			
			changed = true;
			this.startUpdateBouquetItemsPoller();
		}
		
		if(changed){
			userprefs.save();
			this.notify("Settings saved");
		} else {
			this.notify("Nothing changed! No need to save!");
		}
	}
});
core = new E2WebCore();