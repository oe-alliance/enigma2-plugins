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

var Bouquets = Class.create(Controller, {
	initialize: function($super, targetBouquets, targetMain){
		$super(new BouquetListHandler(targetBouquets, targetMain));
		this.loadFirstOnFinished = false;
	},

	load: function(sRef, loadFirstOnFinished){
		if(loadFirstOnFinished)
			this.loadFirstOnFinished = true;
		this.handler.load( {'sRef' : sRef} );
		var services = $('contentServices');
		if(services){
			services.update(strings.select_bouquet);
		}
	},

	loadBouquetsTv: function(){
		setContentHd(strings.bouquets + ' (' + strings.tv + ')');
		this.load(bouquetsTv);
	},

	loadProviderTv: function(){
		setContentHd(strings.providers + ' (' + strings.tv + ')');
		this.load(providerTv);
	},

	loadSatellitesTv: function(){
		setContentHd(strings.satellites + ' (' + strings.tv + ')');
		this.load(satellitesTv);
	},

	loadBouquetsRadio: function(){
		setContentHd(strings.bouquets + ' (' + strings.radio + ')');
		this.load(bouquetsRadio);
	},

	loadProviderRadio: function(){
		setContentHd(strings.providers + ' (' + strings.radio + ')');
		this.load(providerRadio);
	},

	loadSatellitesRadio: function(){
		setContentHd(strings.satellites + ' (' + strings.radio + ')');
		this.load(satellitesRadio);
	},

	onFinished: function(){
		var bouquets = this.handler.data.services;
		if(bouquets){
			if(this.loadFirstOnFinished || bouquets.length == 1){
				var bouquet = bouquets[0];
				setContentHd(bouquet.servicename);
				this.loadFirstOnFinished = false;
				hash = core.getBaseHash() + '/' + bouquet.servicereference;
				hashListener.setHash(hash);
			} else {
				var currentBouquet = hashListener.getHash().split('/')[3];
				if(currentBouquet){
					bouquets.each(function(bouquet){
						if(bouquet.servicereference == currentBouquet){
							setContentHd(bouquet.servicename);
						}
					});
				}
			}
		}
	}
});

var Current = Class.create(Controller, {
	initialize: function($super, curTarget, volTarget){
		$super(new CurrentHandler(curTarget, volTarget));
		this.handler.onFinished[this.handler.onFinished.length] = this.onFinished.bind(this);
		this.display = 'none';
	},

	load: function(){
		this.handler.load({});
	},

	toggleVisibility: function(element){
		var ext = $('trExtCurrent');
		if(ext){
			var bullet = element.down('.currentBulletToggle');
			var visible = ext.visible();
			core.toggleBullet(bullet, !visible);
			if(visible)
				ext.hide();
			else
				ext.show();
			this.display = ext.style.display;
			setMaxHeight('contentMain');
		}
	},

	onFinished: function(){
		setMaxHeight('contentMain');
		var ext = $('trExtCurrent');
		if(ext){
			ext.style.display = this.display;
			var bullet = $('currentName').down('.currentBulletToggle');
			core.toggleBullet(bullet, ext.visible());
		}
		core.currentData = this.handler.data;
	}
});

var Externals = Class.create(Controller, {
	initialize: function($super, target){
		$super(new ExternalsHandler(target));
		this.loaded = false;
	},

	load: function(){
		if(!this.loaded)
			this.handler.load({});
		else
			this.handler.show(this.handler.data);
	},

	onFinished: function(){
		this.loaded = true;
	}
});

var EPG = Class.create(Controller, {
	initialize: function($super){
		$super(new EpgListHandler(this.show.bind(this)));
		this.window = '';
	},

	show:function(html){
		var win = core.popup("EPG" + new Date().getTime(), html, 900, 500);
		this.doRegisterEvents(win);
	},

	load: function(sRef){
		this.handler.load({'sRef' : sRef});
	},

	search: function(needle){
		this.handler.search({'search' : needle});
	},

	doRegisterEvents: function(win){
		var elem = win.document;
		var onload = function(event){
			elem.on(
				'click',
				'.eListAddTimer',
				function(event, element){
					core.timers.addByEventId(element, 0);
					return false;
				}
			);
			elem.on(
				'click',
				'.eListZapTimer',
				function(event, element){
					core.timers.addByEventId(element, 1);
					return false;
				}
			);
			elem.on(
				'click',
				'.eListEditTimer',
				function(event, element){
					var hash = ["#!/timer", "edit"].join("/");
					hashListener.setHash(hash);
					core.timers.editFromEvent(element);
					//return false;
				}
			);
		};
		if(elem.on){
			onload();
		} else {
			win.onload = onload;
		}
	}
});

var MultiEpg = Class.create(Controller, {
	initialize: function($super){
		$super(new MultiEpgHandler(this.show.bind(this)));
		this.tplDetails = "";
	},

	load: function(bRef){
		templateEngine.fetch(
			'tplMultiEpgDetail',
			function(tpl){
				this.tplDetails = tpl;
				this.doLoad(bRef);
			}.bind(this));
	},

	doLoad: function(bRef){
		this.handler.load({'bRef' : bRef});
	},

	show: function(html){
		var win = core.popup("MultiEpg" + new Date().getTime(), html, 900, 570);
		this.doRegisterEvents(win);
	},

	doRegisterEvents: function(win){
		var elem = win.document;
		var _this = this;
		var onload = function(event){
			elem.on(
				'click',
				'.mEpgItem',
				function(event, element){
					var detail = elem.getElementById('mEpgDetail');
					if(detail){
						var e = {};
						e.servicereference = element.readAttribute('data-servicereference');
						e.servicename = element.readAttribute('data-servicename');
						e.eventid = element.readAttribute('data-eventid');
						e.date = element.readAttribute('data-date');
						e.start = element.readAttribute('data-start');
						e.starttime = element.readAttribute('data-starttime');
						e.end = element.readAttribute('data-end');
						e.endtime = element.readAttribute('data-endtime');
						e.duration = element.readAttribute('data-duration');
						e.title = element.readAttribute('data-title');
						e.description = element.readAttribute('data-description');
						e.extdescription = element.readAttribute('data-extdescription');
						var data = {'e' : e};
						detail.update(_this.tplDetails.process(data));
						detail.fadeIn({'delay' : 300, 'to' : 95});
					}
					event.stop();
				}
			);
			elem.on(
				'click',
				'.close',
				function(event, element){
					var detail = elem.getElementById('mEpgDetail');
					if(detail)
						detail.hide();
					event.stop();
				}
			);

			elem.on(
				'click',
				'.eListAddTimer',
				function(event, element){
					core.timers.addByEventId(element, 0);
					event.stop();
				}
			);
			elem.on(
				'click',
				'.eListZapTimer',
				function(event, element){
					core.timers.addByEventId(element, 1);
					event.stop();
				}
			);
			elem.on(
				'click',
				'.eListEditTimer',
				function(event, element){
					var hash = ["#!/timer", "edit"].join("/");
					hashListener.setHash(hash);
					core.timers.editFromEvent(element);
					event.stop();
				}
			);
		};
		if(elem.on){
			if(elem.onload)
				elem.onload();
			onload();
		} else {
			win.onload = onload;
		}
	}
});

var Power = Class.create({
	STATES: {'toggle' : 0, 'deep' : 1, 'reboot' : 2, 'gui' : 3},

	initialize: function(){
		//As we do not have an real templates here, there is no handler for powerstate.
		//The Handling is up to the caller of this class
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

	inStandby: function(callback){
		this.callbacks.push(callback);
		if(!this.isLoading){
			this.load({});
		}
	},

	set: function(newstate, callback){
		this.callbacks.push(callback);
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

var MediaPlayer = Class.create(Controller, {
	initialize: function($super, target){
		$super(new MediaPlayerHandler(target));
	},

	load: function(path){
		if(!path){
			path = 'Filesystems';
		}
		var parms = {'path' : path};
		this.handler.load(parms);
	},

	playFile: function(file){
		this.handler.playFile(file);
	},

	addFile: function(file){
		this.handler.addFile(file);
	},

	removeFile: function(file){
		this.handler.removeFile(file);
	},

	savePlaylist: function(filename){
		this.handler.savePlaylist(filename);
	},

	command: function(cmd){
		this.handler.command(cmd);
	},

	onInstantPlay: function(event, element){
		var ref = $F('instantPlay').gsub(":", "%3a");
		ref = "4097:0:1:0:0:0:0:0:0:0:" + ref;
		this.playFile(ref);
		event.stop();
	},

	addInstantPlayInput: function(){
		var form = new Element('form');
		form.id = 'instantPlayForm';
		var input = new Element('input');
		input.id = 'instantPlay';
		setInputPlaceholder(input, strings.play);

		form.insert({top : input});
		form.on('submit', this.onInstantPlay.bind(this));

		$('contentHdExt').update(form);
	},

	onFinished: function(){
		this.addInstantPlayInput();
	}
});

var Messages = Class.create({
	initialize: function(){
		this.handler = new SimpleRequestHandler();
	},

	send: function(text, type, timeout){
		this.handler.load(URL.message, {'text' : text, 'type' : type, 'timeout' : timeout});
	}
});

var Movies = Class.create(Controller, {
	initialize: function($super, listTarget, navTarget, locTarget){
		$super(new MovieListHandler(listTarget));
		this.navHandler = new MovieNavHandler(navTarget, locTarget);
	},

	load: function(location, tags){
		if(!location){
			var sethash = function(location){
				var hash = [core.getBaseHash(), "filter", encodeURIComponent(location), encodeURIComponent(tags)].join("/");
				hashListener.setHash(hash);
			};
			if(core.currentLocation == ""){ //wait for currentLocation to be set;
				core.lt.getCurrentLocation(sethash);
			} else {
				sethash(core.currentLocation);
			}
			return;
		}

		this.handler.load({'dirname' : location, 'tag' : tags});
	},

	loadNav: function(){
		core.lt.getLocationsAndTags(this.showNav.bind(this));
	},

	showNav: function(currentLocation, locations, tags){
		this.navHandler.load(toOptionList(locations, currentLocation), toOptionList(tags, core.currentTag));
	},

	del: function(element){
		this.handler.del(element);
	}
});

var RemoteControl = Class.create({
	initialize: function(){
		this.handler = new RemoteControlHandler();
		var _this = this;
		this.handler.onFinished.push(_this.onKeySent.bind(_this));
		this.shotType = '';
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
			case 'dm800sev2':
			case 'dm500hdv2':
				tpl = 'tplWebRemote';
				break;
			default:
				tpl = 'tplWebRemoteOld';
			}

			templateEngine.process(tpl, null, function(html){
				this.eventsregistered = false;
				this.window = core.popup('WebRemote', html, 250, 650);
				this.registerEvents();
			}.bind(this));
		}
	},

	sendKey: function(cmd, type, shotType){
		debug("[RemoteControl].sendKey: " + cmd);
		this.shotType = shotType;
		this.handler.sendKey({'command' : cmd, 'type': type});

	},

	onKeySent: function(){
		this.screenShot(this.shotType);
	},

	screenShot: function(shotType){
		var hash = '!/control'; //FIXME
		switch(shotType){
		case 'osd':
			hash = [hash, 'osdshot'].join("/");
			break;
		case 'all':
			hash = [hash, 'screenshot'].join("/");
			break;
		default:
			return;
		}
		//the box needs at least a little bit of time to actually draw the window
		//wait 250ms before fetching a new screenshot
		setTimeout(
			function(){
				var forceReload = hash == hashListener.getHash();
				hashListener.setHash(hash);
				if(forceReload){
					core.onHashChanged(true);
				}
			},
			250);
	},

	registerEvents: function(){
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
					var shotType = '';
					if(screenshot && video){
						shotType = 'all';
					} else if (screenshot && !video) {
						shotType = 'osd';
					}
					_this.sendKey(id, type, shotType);
				}
			);
			elem.on(
				'click',
				'.screenshot',
				function(event, element){
					var video = _this.window.document.getElementById('video').checked;
					var shotType = 'osd';
					if(video)
						shotType = 'all';
					_this.screenShot(shotType);
				}
			);
		};
		if(elem.on){
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
				params['format'] = 'png';
				break;
			case this.TYPE_VIDEO:
				params['v'] = '';
				break;
			default:
				break;
		}
		this.handler.load(params);
	},

	shootOsd: function(){
		setContentHd(strings.screenshot_osd);
		this.load(this.TYPE_OSD);
	},

	shootVideo: function(){
		setContentHd(strings.screenshot_video);
		this.load(this.TYPE_VIDEO);
	},

	shootAll: function(){
		setContentHd(strings.screenshot_all);
		this.load(this.TYPE_ALL);
	}
});

var Services = Class.create(Controller, {
	initialize: function($super, target, epg){
		$super(new ServiceListHandler(target));
		this.epg = epg;
		this.cachedServiceElements = null;
	},

	zap: function(sRef, sRoot, callback){
		this.handler.zap({'sRef' : sRef, 'root' : sRoot}, callback);
	},

	load: function(sRef){
		this.handler.load({'bRef' : sRef});
	},

	getNowNext: function(){
		this.handler.getNowNext();
	},

	getSubservices: function(){
		this.handler.getSubservices();
	},

	loadAll: function(ref){
		var tpl = 'tplBouquetsAndServices';
		var fnc = function(){
			$('contentBouquets').update(strings.all);
			this.load(ref);
		}.bind(this);

		if($('contentBouquets')){
			fnc();
		} else {
			templateEngine.process(
				tpl,
				null,
				'contentMain',
				fnc
			);
			}
	},

	loadAllTv: function(){
		this.loadAll(allTv);
		setContentHd(strings.all + " (" + strings.tv + ")");
	},

	loadAllRadio: function(){
		this.loadAll(allRadio);
		setContentHd(strings.all + " (" + strings.radio + ")");
	},

	onFilterFocus: function(event){
		event.element().value = '';
		this.cachedServiceElements = null;
		this.filter(event);
	},

	filter: function(event){
		var needle = event.element().value.toLowerCase();

		if(this.cachedServiceElements == null){
			this.cachedServiceElements = $$('.sListRow');
		}
		var cls = 'even';
		for(var i = 0; i < this.cachedServiceElements.length; i++){
			var row = this.cachedServiceElements[i];
			var serviceName = row.readAttribute('data-servicename');
			if(serviceName)
				serviceName = serviceName.toLowerCase();
			var isMarker = serviceName == null;
			if( (isMarker || ( serviceName.match(needle) != needle && serviceName != "")) && needle != "" ){
				row.hide();
			} else {
				row.show();
				if(isMarker)
					continue;
				cls = cls == 'odd' ? 'even' : 'odd';
				notCls = cls == 'odd' ? 'even' : 'odd';

				var td = row.firstDescendant();
				td.removeClassName(notCls);
				td.addClassName(cls);
			}
		}
	},

	addFilterInput: function(){
		var input = new Element('input');
		input.id = 'serviceFilter';
		setInputPlaceholder(input, strings.filter_services);
		$('contentHdExt').update(input);
		input.on('focus', this.onFilterFocus.bind(this));
		input.on('keyup', this.filter.bind(this));
	},

	onFinished: function(){
		this.addFilterInput();
		core.startUpdateBouquetItemsPoller();
	}
});

var SignalWindow = Class.create(Controller, {
	initialize: function($super, seconds){
		$super(new SignalHandler(this.show.bind(this)));
		this.window = '';
		if(!isNaN(Number(seconds))){
			this.seconds = seconds * 1000;
		} else {
			this.seconds = 5000;
		}
		this.interval = '';
	},

	load: function(){
		this.handler.load({});
	},

	reload: function(){
		debug('[SignalWindow].reload');
		if (!this.window.closed && this.window.location){
			this.load();
		} else {
			clearInterval(this.interval);
		}
	},

	show: function(html){
		debug('[SignalWindow].show');
		if (this.window.closed || !this.window.location){
			this.window = core.popup("SignalPanel", html, 220, 120);
			this.window.onbeforeunload = function(){
				clearInterval(this.interval);
			};

			var _this = this;
			clearInterval(_this.interval);
			this.interval = setInterval(_this.reload.bind(this), _this.seconds);
		} else if(!this.window.closed && this.window.location) {
			this.window.document.write(html);
			this.window.document.close();
		}
	}
});

var SimplePages = Class.create({
	PAGE_ABOUT : 'tplAbout',
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
		setContentHd(strings.about);
		this.show(this.PAGE_ABOUT);
	},

	loadMessage: function(){
		setContentHd(strings.send_message);
		this.show(this.PAGE_MESSAGE);
	},

	loadPower: function(){
		setContentHd(strings.powercontrol);
		this.show(this.PAGE_POWER);
	},

	loadSettings: function(){
		setContentHd(strings.settings);
		var debug = userprefs.data.debug;
		var debugChecked = "";
		if(debug){
			debugChecked = 'checked';
		}

		var updateCurrentInterval = userprefs.data.updateCurrentInterval / 1000;
		var updateBouquetInterval = userprefs.data.updateBouquetInterval / 1000;
		var style = userprefs.data.style;
		data = {'debug' : debugChecked,
				'updateCurrentInterval' : updateCurrentInterval,
				'updateBouquetInterval' : updateBouquetInterval,
				'style' : style
			};
		this.show(this.PAGE_SETTINGS, data);
	},

	loadTools: function(){
		setContentHd(strings.tools);
		this.show(this.PAGE_TOOLS);
	},

	loadDeviceInfo: function(){
		setContentHd(strings.deviceinfo);
		this.deviceInfoHandler.load({});
	},

	getDeviceInfo: function(callback){
		this.deviceInfoHandler.get({}, callback);
	}
});

var Timers = Class.create({
	initialize: function(target){
		this.listHandler = new TimerListHandler(target);
		this.timerHandler = new TimerHandler(target, this.loadList.bind(this), [this.onTimerEditLoadFinished.bind(this)]);
	},

	loadList: function(){
		this.listHandler.load({});
	},

	cleanupList: function(){
		this.listHandler.cleanup();
	},

	create: function(){
		this.timerHandler.load({}, false, true);
	},

	edit: function(element){
		this.timerHandler.load(element, true);
	},

	editFromEvent: function(element){
		this.timerHandler.load(element, false, false, true);
	},

	save: function(element){
		this.timerHandler.commitForm(element);
	},

	onBouquetChanged: function(bRef){
		this.timerHandler.onBouquetChanged(bRef, this.onUpdatedServiceListReady.bind(this));
	},

	onUpdatedServiceListReady: function(data, timer){
		var serviceSel = $('service');
		var options = serviceSel.options;
		options.length = 0;

		var i = 0;
		data.services.each(function(s){
			var selected = false;
			if(timer.servicereference == unescape(s.servicereference)){
				selected = true;
			}
			options.add ( new Option(s.servicename, s.servicereference, false, selected) );
			i++;
		});
	},

	recordNow: function(type, callback){
		this.timerHandler.recordNow(type, callback);
	},

	addByEventId: function(element, justplay){
		var parent = element.up('.epgListItem');
		var sRef = unescape(parent.readAttribute('data-servicereference'));
		var eventId = unescape(parent.readAttribute('data-eventid'));
		this.timerHandler.addByEventId(sRef, eventId, justplay);
	},

	toggleDisabled: function(element){
		this.timerHandler.toggleDisabled(element);
	},

	del: function(element){
		this.timerHandler.del(element);
	},

	onTimerEditLoadFinished: function(){
		debug("[Timers].onTimerEditLoadFinished");
		datePickerController.destroyDatePicker('sdate');
		datePickerController.destroyDatePicker('edate');
		var today = new Date();
		var pad = function(value, length) {
			length = length || 2;
			return "0000".substr(0,length - Math.min(String(value).length, length)) + value;
		};
		var opts = {
				showWeeks: true,
				noFadeEffect: true,
				rangeLow: today.getFullYear() + "" + pad(today.getMonth()+1) + pad(today.getDate())
			};


		opts['formElements'] = { 'sdate' : 'Y-ds-m-ds-d'};
		datePickerController.createDatePicker(opts);

		opts['formElements'] = { 'edate' : 'Y-ds-m-ds-d'};
		datePickerController.createDatePicker(opts);

	}
});

var Volume = Class.create(Controller, {
	initialize: function($super, target){
		$super(new VolumeHandler(target));
	},

	load: function(){
		this.handler.load({});
	},

	set: function(value){
		this.handler.load({'set' : value});
	}
});

var BaseCore = Class.create({
	initialize: function(){
		this.popUpBlockerHinted = false;
		this.hideNotifierTimeout = '';
		this.sessionProvider = new SessionProvider( this.onSessionAvailable.bind(this) );
		if(userprefs.data.style != "merlin_dark" && userprefs.data.style != "modern"){
			userprefs.data.style = "modern";
			userprefs.save();
		}
	},

	run: function(){
		debug("[BaseCore].run");
		this.sessionProvider.load({});
	},

	onSessionAvailable: function(sid){
		debug("[BaseCore].onSessionAvailable, " + sid);
		global_sessionid = sid;
		RequestCounter.addChangedCallback(this.onAjaxRequestCountChanged.bind(this));
	},

	onSessionFailed: function(transport){
		this.notify("FATAL ERROR! NO SESSION!", true);
	},

	onAjaxRequestCountChanged: function(count){
		debug("Active Request count: " + RequestCounter.count);
		var ajaxload = $('ajaxLoad');
		if(ajaxload){
			if(count > 0)
				$('ajaxLoad').show();
			else
				$('ajaxLoad').hide();
		}
	},

	hideNotifier: function(){
		debug("[BaseCore].hideNotifier");
		$('notification').fadeOut(500);
	},

	notify: function(text, state){
		debug("[BaseCore].notify");
		var notif = $('notification');
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
		var target = $(targetElement);
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
			var popup = window.open('about:blank',title,'scrollbars=yes, width='+width+',height='+height+',resizable=yes');
			this.setWindowContent(popup, html);
			return popup;
		} catch(e){
			this.popUpBlockerHint();
			return "";
		}
	},

	styleChanged: function(){
		switch(userprefs.data.style){
			case 'merlin_dark':
				$('style_merlin_dark').disabled = false;
				$('style_modern').disabled = true;
				break;
			default:
				$('style_merlin_dark').disabled = true;
				$('style_modern').disabled = false;
				break;
		}
	}
});

var E2WebCore = Class.create(BaseCore, {
	initialize: function($super){
		$super();
		this.mediaPlayerStarted = false;
		this.settings = null;
		this.parentControlList = null;

		this.currentBouquet = bouquetsTv;

		this.updateBouquetItemsPoller = '';
		this.updateCurrentPoller = '';
		this.signalPanelUpdatePoller = '';

		this.isActive = {};
		this.isActive.getCurrent = false;

		this.mode = "";
		this.subMode = "";

		//create required Instances
		this.bouquets = new Bouquets('contentBouquets', 'contentMain');
		this.current = new Current('currentContent', 'volContent');
		this.externals = new Externals('navExternalsContainer');
		this.epg = new EPG(new EpgListHandler());
		this.lt = new LocationsAndTags();
		this.mediaplayer = new MediaPlayer('contentMain');
		this.messages = new Messages();
		this.movies = new Movies('contentMain', 'navContent', 'contentHdExt');
		this.multiepg = new MultiEpg();
		this.power = new Power();
		this.remote = new RemoteControl();
		this.screenshots = new Screenshots('contentMain');
		this.services = new Services('contentServices', this.epg);
		this.signal = new SignalWindow(3);
		this.simplepages = new SimplePages('contentMain');
		this.timers = new Timers('contentMain');
		this.volume = new Volume('volContent');

		this.currentData = {};
		this.currentLocation = "";
		this.currentTag = "";
		this.deviceInfo = "";

		this.navlut = {
			'tv': {
				'bouquets' : this.bouquets.loadBouquetsTv.bind(this.bouquets),
				'providers' : this.bouquets.loadProviderTv.bind(this.bouquets),
				'all' : this.services.loadAllTv.bind(this.services)
				},
			'radio': {
				'bouquets' : this.bouquets.loadBouquetsRadio.bind(this.bouquets),
				'providers' : this.bouquets.loadProviderRadio.bind(this.bouquets),
				'all' : this.services.loadAllRadio.bind(this.services)
			},
			'movies':{
				'list' : function(){}
			},
			'timer': {
				'create' : this.timers.create.bind(this.timers),
				'edit' : false,
				'list' : function() { this.loadContentDynamic(this.timers.loadList.bind(this.timers), strings.timers); }.bind(this)
			},
			'control': {
				'message' : this.simplepages.loadMessage.bind(this.simplepages),
				'power' : this.simplepages.loadPower.bind(this.simplepages),
				'osdshot' : this.screenshots.shootOsd.bind(this.screenshots),
				'screenshot' : this.screenshots.shootAll.bind(this.screenshots),
				'videoshot' : this.screenshots.shootVideo.bind(this.screenshots)
			},
			'extras': {
				'about' : this.simplepages.loadAbout.bind(this.simplepages),
				'deviceinfo' : this.simplepages.loadDeviceInfo.bind(this.simplepages),
				'mediaplayer' : function() { this.loadContentDynamic(this.mediaplayer.load.bind(this.mediaplayer), strings.mediaplayer); }.bind(this),
				'settings' : this.simplepages.loadSettings.bind(this.simplepages),
				'tools' : this.simplepages.loadTools.bind(this.simplepages)
			}
		};
	},

	delayedUpdateItems: function(){
		var _this = this;
		setTimeout(_this.updateItems.bind(this), 2000);
	},

	updateItems: function(){
		debug("[E2WebCore].updateItems");
		this.current.load();
		this.power.inStandby(this.onPowerStateAvailable.bind(this));
	},

	onPowerStateAvailable: function(isStandby){
		var signal = $('openSignalPanelImg');
		if(isStandby){
			if(signal.hasClassName("item_enabled"))
				signal.removeClassName("item_enabled")
		} else {
			if(!signal.hasClassName("item_enabled"))
				signal.addClassName("item_enabled")
		}
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

	setNavHighlight: function(){
		var navitems = $$(".navmenu");
		navitems.each(function(element){
			var mode = element.readAttribute("data-mode");
			var navselected = "navselected";
			if(mode == this.mode){
				element.addClassName(navselected);
			} else {
				element.removeClassName(navselected);
			}
		}.bind(this));
	},

	onHashChanged: function(isReload){
		var hash = hashListener.getHash();
		var parts = hash.split("/");

		var len = parts.length;
		if(len >= 2){
			var mode = parts[1];
			if(mode != this.mode || isReload || ( len <= 2 && this.subMode != '') ){
				this.switchMode(mode, len == 2);
				this.subMode = '';
			}
			this.mode = mode;

			this.setNavHighlight();

			if(len > 2){
				var subMode = parts[2];
				if(subMode != this.subMode || isReload){
					this.subMode = subMode;
					if(!this.navlut[this.mode][this.subMode]){
						return;
					} else {
						if(this.mode != "movies")
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
						var location = decodeURIComponent(parts[4]);
						var tag = decodeURIComponent(parts[5]);

						this.currentLocation = location;
						this.currentTag = tag;
						this.loadContentDynamic(
							function(){
								this.movies.load(location, tag);
							}.bind(this),
							strings.movies,
							true
						);

						break;
					case 'extras':
						if(subMode == 'mediaplayer'){
							this.mediaplayer.load(decodeURIComponent(parts[3]));
						}
						break;
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

	onSessionAvailable: function($super, sid){
		debug("[E2WebCore].onSessionAvailable, " + sid);
		$super(sid);

		this.currentLocation = this.lt.getCurrentLocation(function(location){this.currentLocation = location;}.bind(this));
		this.deviceInfo = this.simplepages.getDeviceInfo(function(info){this.deviceInfo = info;}.bind(this));
		
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

		this.setAjaxLoad('navContent');
		this.setAjaxLoad('contentMain');
		
		templateEngine.fetch('tplServiceListEPGItem');
		templateEngine.fetch('tplBouquetsAndServices');
		templateEngine.fetch('tplCurrent');
		if(!hashListener.getHash().length >= 1){
			this.loadDefault();
		}
		this.updateItems();
		this.startUpdateCurrentPoller();
	},

	toggleBullet: function(bullet, isOpen) {
		var open_class = getBulletToggleClass(true);
		var closed_class = getBulletToggleClass(false);
		if(isOpen) {
			if(bullet.hasClassName(closed_class))
				bullet.removeClassName(closed_class);
			if(!bullet.hasClassName(open_class))
				bullet.addClassName(open_class);
			bullet.alt = "-";
		} else {
			if(bullet.hasClassName(open_class))
				bullet.removeClassName(open_class);
			if(!bullet.hasClassName(closed_class))
				bullet.addClassName(closed_class);
			bullet.alt = "+";
		}
	},

	registerEvents: function(){
		debug("[E2WebCore].registerEvents");
		//Header
		$('openSignalPanel').on(
			'click',
			function(event, element){
				this.signal.load();
				event.stop();
			}.bind(this)
		);
		$('instantRecord').on(
			'click',
			function(event, element){
				var menu = $('instantRecordMenu');
				if(menu.visible()){
					menu.hide();
				} else {
					menu.show();
				}
				event.stop();
			}
		);
		document.on(
			'click',
			'.doInstantRecord',
			function(event, element){
				var menu = $('instantRecordMenu');
				this.timers.recordNow(
					element.readAttribute('data-type'),
					function(result){
						var toggle = menu.up('.group').down('.dropdown-toggle');
						toggle.removeClassName("active");
						menu.removeClassName("open");
						menu.hide();
					}
				);
			}.bind(this)
		);
		//Current
		$('current').on(
			'click',
			'.currentExtShowHide',
			function(event, element){
				this.current.toggleVisibility(element);
				event.stop();
			}.bind(this)
		);
		$('current').on(
				'click',
				'.currentEpg',
				function(event, element){
					var ref = unescape( element.readAttribute('data-servicereference') );
					this.epg.load(ref);
					event.stop();
				}.bind(this)
			);
		//EPG-Search
		$('epgSearchForm').on(
			'submit',
			function(event, element){
				this.epg.search($F('epgSearch'));
				event.stop();
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
		var changeevt = Prototype.Browser.IE ? "click" : "change";
		var nav = $('navContent');
		nav.on(
			changeevt,
			'.mNavLocTag',
			function(event, element){
				var l = $('locations');
				var t = $('tags');
				var location = l.options[l.selectedIndex].value;
				var tag = t.options[t.selectedIndex].value;
				var hash = [this.getBaseHash(), "filter", encodeURIComponent(location), encodeURIComponent(tag)].join("/");
				if(hash != '#'+hashListener.getHash() || !Prototype.Browser.IE)
					hashListener.setHash(hash);
			}.bind(this)
		);
		$('contentHdExt').on(
			changeevt,
			'.mNavLocTag',
			function(event, element){
				var l = $('locations');
				var t = $('tags');
				var location = l.options[l.selectedIndex].value;
				var tag = t.options[t.selectedIndex].value;
				var hash = [this.getBaseHash(), "filter", encodeURIComponent(location), encodeURIComponent(tag)].join("/");
				if(hash != '#'+hashListener.getHash() || !Prototype.Browser.IE)
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
		//MediaPlayer
		content.on(
			'click',
			'.mpCmd',
			function(event, element){
				this.mediaplayer.command(element.readAttribute('data-command'));
			}.bind(this)
		);
		content.on(
			'click',
			'.mpPlayFile',
			function(event, element){
				var parent = element.up('.mpListItem');
				var ref = decodeURIComponent( parent.readAttribute('data-servicereference') );
				this.mediaplayer.playFile(ref);
				event.stop();
			}.bind(this)
		);
		content.on(
				'click',
				'.mpAddFile',
				function(event, element){
					var parent = element.up('.mpListItem');
					var ref = decodeURIComponent( parent.readAttribute('data-servicereference') );
					this.mediaplayer.addFile(ref);
					event.stop();
				}.bind(this)
			);
		content.on(
			'click',
			'.mpRemoveFile',
			function(event, element){
				var parent = element.up('.mpListItem');
				var ref = decodeURIComponent( parent.readAttribute('data-servicereference') );
				this.mediaplayer.removeFile(ref);
				event.stop();
			}.bind(this)
		);
		content.on(
				'click',
				'.mpSavePlaylist',
				function(event, element){
					var filename = prompt('Please enter a filename for the playlist', 'playlist');
					if(filename != null && filename != ""){
						this.mediaplayer.savePlaylist(filename);
					}
				}.bind(this)
			);
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
				this.movies.del(element);
				event.stop();
			}.bind(this)
		);
		//Powerstate
		document.on(
			'click',
			'.powerState',
			function(event, element){
				var newState = element.readAttribute("data-state");
				var cb = function(isStandby){
					var text = "Device is now Running";
					switch(this.power.STATES[newState]){
					case this.power.STATES.toggle:
						if(isStandby)
							text = "Device is now in Soft-Standby";
						break;
					case this.power.STATES.deep:
						if(isStandby)
							text = "Device will go into deep standby (if possible, check OSD for messages)";
						else
							text = "Cannot shutdown!";
						break;
					case this.power.STATES.reboot:
						if(isStandby)
							text = "Device will reboot now (if possible, check OSD for messages)";
						else
							text = "Cannot reboot!";
						break;
					case this.power.STATES.gui:
						if(isStandby)
							text = "GUI will restart now (if possible, check OSD for messages)";
						else
							text = "Cannot restart GUI!";
						break;
					}
					this.notify(text, true);
					this.onPowerStateAvailable(isStandby);
				}.bind(this);
				this.power.set(newState, cb);
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
		//Bouquets
		content.on(
			'click',
			'a.bListSLink',
			function(event, element){
				setContentHd(element.readAttribute("data-servicename"));
			}
		);
		content.on(
			'click',
			'a.bListEpg',
			function(event, element){
				var sref = decodeURIComponent( element.readAttribute("data-servicereference") );
				this.multiepg.load(sref);
				event.stop();
			}.bind(this)
		);

		//Servicelist
		content.on(
			'click',
			'a.sListSLink',
			function(event, element){
				var root = unescape( element.readAttribute('data-bouquetreference') );
				var ref = decodeURIComponent( element.id );
				this.services.zap(ref, root, this.delayedUpdateItems.bind(this));
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'a.sListServiceEpg',
			function(event, element){
				var ref = unescape( element.readAttribute('data-servicereference') );
				this.epg.load(ref);
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'a.sListExtEpg',
			function(event, element){
				var target = element.up('.sListEPGItem').down('.sListExtEpgLong');
				if(target){
					var bullet = element.down('.sListBulletToggle');
					var visible = target.visible();
					this.toggleBullet(bullet, !visible);
					if(visible)
						target.hide();
					else
						target.show();
				}
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'.sListAddTimer',
			function(event, element){
				core.timers.addByEventId(element, 0);
				event.stop();
			}
		);
		content.on(
			'click',
			'.sListZapTimer',
			function(event, element){
				core.timers.addByEventId(element, 1);
				event.stop();
			}
		);
		content.on(
			'click',
			'.sListEditTimer',
			function(event, element){
				var hash = ["#!/timer", "edit"].join("/");
				hashListener.setHash(hash);
				core.timers.editFromEvent(element);
				event.stop();
			}
		);

		//Timerlist
		content.on(
			'click',
			'.tListDelete',
			function(event, element){
				this.timers.del(element);
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'.tListToggleDisabled',
			function(event, element){
				this.timers.toggleDisabled(element);
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'.tListEdit',
			function(event, element){
				var hash = ["#!/timer", "edit"].join("/");
				hashListener.setHash(hash);
				this.timers.edit(element);
				return false;
			}.bind(this)
		);
		content.on(
			'click',
			'.tListCleanup',
			function(event, element){
				this.timers.cleanupList();
				return false;
			}.bind(this)
		);
		//Timer Editing
		content.on(
			'change',
			'.tEditRepeated',
			function(event, element){
				var days = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'];
				var weekdays = days.slice(0,5);

				switch(element.id){
				case 'mf':
					var checked = element.checked;
					weekdays.each(function(day){
						$(day).checked = checked;
					});
					if(checked){
						var others = ['sa', 'su', 'ms'];
						others.each(function(item){
							$(item).checked = false;
						});
					}
					break;
				case 'ms':
					var checked = element.checked;
					days.each(function(day){
						$(day).checked = checked;
					});
					if(checked){
						$('mf').checked = false;
					}
					break;
				default:
					var weekdays = true;
					var alldays = true;
					days.each(function(day){
						day = $(day);
						if(day.value <= 64){
							if(!day.checked){
								alldays = false;
								if(day.value <= 16){
									weekdays = false;
									return
								}
							} else {
								if(day.value > 16){
									weekdays = false;
								}
							}
						}
					});
					if(alldays){
						$('mf').checked = false;
						$('ms').checked = true;
					} else if (weekdays) {
						$('mf').checked = true;
						$('ms').checked = false;
					} else {
						$('mf').checked = false;
						$('ms').checked = false;
					}
				}
			}
		);
		content.on(
			'change',
			'.tEditBouquet',
			function(event, element){
				var value = unescape( element.options[element.selectedIndex].value );
				core.timers.onBouquetChanged(value);
			}.bind(this)
		);
		content.on(
			'click',
			'.tEditTag',
			function(event, element){
				var selected = 'selected';
				var attr = 'data-selected';
				if(element.hasClassName(selected)){
					element.removeClassName(selected);
					element.writeAttribute(attr, '');
				} else {
					element.addClassName(selected);
					element.writeAttribute(attr, selected);
				}
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'.tEditSave',
			function(event, element){
				this.timers.save($('timerEditForm'));
			}.bind(this)
		);

		$('webTv').on(
			'click',
			function(event, element){
				window.open('/web-data/tpl/default/streaminterface/index.html', 'WebTV', 'scrollbars=no, width=800, height=740, resizable=yes');
				event.stop();
			}.bind(this)
		);
		//Hash-Reload-Fix
		//HACK :: THIS IS EVIL VOODOO, DON'T TRY THIS AT HOME!
		document.on(
			'click',
			'a',
			function(event, element){
				if(event.stopped)
					return;
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
						return;
					}
				}
			}.bind(this)
		);
	},

	/*
	 * Loads another navigation template and sets the navigation header
	 * @param template - The name of the template
	 * @param title - The title to set for the navigation
	 */
	reloadNav: function(template, title, callback){
		this.setAjaxLoad('navContent');
		templateEngine.process(template, null, 'navContent', callback);
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
	loadContentDynamic: function(fnc, title, keepHdExt){
		setContentHd(title, keepHdExt);
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

	setEmptyContent: function(id, text){
		$(id).update('<div class="block center fullwidth oneliner">' + text + '</div>');
	},

	switchMode: function(mode, initContent){
		if(initContent){
			this.setEmptyContent('contentMain', strings.select_submenu);
			setContentHd('...');
		}

		switch(mode){
		case "tv":
			if(this.mode != 'tv' && this.mode != 'radio'){
				this.services.registerEvents();
			}
			this.reloadNav('tplNavTv', strings.television);
			break;

		case "radio":
			if(this.mode != 'tv' && this.mode != 'radio'){
				this.services.registerEvents();
			}
			this.reloadNav('tplNavRadio', strings.radio);
			break;

		case "movies":
			this.reloadNavDynamic(this.movies.loadNav.bind(this.movies), strings.movies);
			break;

		case "timer":
			this.reloadNav('tplNavTimer', strings.timers);
			break;

		case "control":
			this.reloadNav('tplNavBoxControl', strings.boxcontrol);
			break;

		case "extras":
			this.reloadNav('tplNavExtras', strings.extras, this.externals.load.bind(this.externals));
			break;

		default:
			break;
		}
	},

	saveSettings: function(){
		userprefs.load();
		var changed = false;


		var l = $('interfaceStyle');
		var style = l.options[l.selectedIndex].value;
		if(style != userprefs.data.style){
			userprefs.data.style = style;
			changed = true;
			this.styleChanged();
		}

		var debug = $('enableDebug').checked;
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

		var updateBouquetInterval = parseNr( $F('updateBouquetInterval') ) * 1000;
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

DropDownHandler = Class.create({
	initialize: function(){
		this.registerEvents();
	},

	show: function(toggle, menu){
		toggle.addClassName("active");
		menu.addClassName("open");
		menu.show();
	},

	hide: function(toggle, menu){
		toggle.removeClassName("active");
		menu.removeClassName("open");
		menu.hide();
	},

	onClick: function(event, toggle){
		event.stop();
		var menu = toggle.up('.group').down('.dropdown-menu');
		if(menu.visible()){
			this.hide(toggle, menu);
		} else {
			this.show(toggle, menu)
		}
	},

	registerEvents: function(){
		document.on(
			'click',
			'.dropdown-toggle',
			this.onClick.bind(this)
		);
		document.on(
			'click',
			function(event, element){
				if(event.stopped)
					return;
				$$('.open').each(function(menu){
					if(element != menu && element.up('.open') != menu){
						var toggle = menu.up('.group').down('.dropdown-toggle');
						this.hide(toggle, menu);
					}
				}.bind(this));
			}.bind(this)
		);
	}
});

var dropDownHandler = new DropDownHandler();

var core = new E2WebCore();
