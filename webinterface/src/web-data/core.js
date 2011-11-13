//General Helpers
function debug(text){}

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
	
	onFinished: function(){},
});

var Bouquets = Class.create(Controller, {
	init: function(serviceController){
		this.model.init({ 'sRef' : bouquetsTv }, serviceController);
	},

	load: function(sRef){
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
		if(bouquet)
			setContentHd(bouquet.servicename);
	}
});

var Current = Class.create(Controller, {
	initialize: function($super, model){
		$super(model);
		this.display = 'none';
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
	load: function(sRef){
		this.model.load({'sRef' : sRef});
	},

	search: function(needle){
		this.model.search({'search' : needle});
	},
});

var Movies = Class.create(Controller, {
	load: function(){
		this.model.load({});
	},
	
	del: function(element){
		this.model.del(element);
	},
});

var Screenshots = Class.create(Controller, {
	TYPE_OSD : 'o',
	TYPE_VIDEO : 'v',
	TYPE_ALL : '',
	
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
	},
});

var Services = Class.create(Controller, {
	initialize: function($super, model, epg){
		$super(model);
		this.epg = epg;
		this.cachedServiceElements = null;
	},
	
	load: function(sRef){
		this.model.load({'sRef' : sRef});
	},
	
	getNowNext: function(){
		this.model.getNowNext();
	},
	
	getSubServices: function(){
		this.model.getSubServices();
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
	}
});

var SimplePages = Class.create({
	PAGE_ABOUT : 'tplAbout',
	PAGE_GEARS : 'tplGears',
	PAGE_MESSAGE : 'tplSendMessage',
	PAGE_POWER : 'tplPower',
	PAGE_SETTINGS: 'tplSettings',
	PAGE_TOOLS: 'tplTools',
	
	initialize: function(simpleHandler, deviceInfoHandler){
		this.simpleHandler = simpleHandler;
		this.deviceInfoHandler = deviceInfoHandler;
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
	}
});

var Timers = Class.create({
	initialize: function(listHandler, timerHandler){
		this.listHandler = listHandler;
		this.timerHandler = timerHandler;
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
		//TODO toggleDisabled
	},
	
	del: function(element){
		//TODO delete
	},
});

var Volume = Class.create(Controller, {
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

		this.currentLocation = "/hdd/movie";
		this.locationsList = [];
		this.tagList = [];

		this.boxtype = "dm8000";
		this.mode = "";
		this.subMode = "";
		
		//create required Instances
		this.epg = new EPG(new EpgListHandler());
		this.services = new Services(new ServiceListHandler('contentServices'), this.epg);
		this.bouquets = new Bouquets(new BouquetListHandler('contentBouquets', 'contentMain'));
		this.timers = new Timers(
				new TimerListHandler('contentMain'), 
				new TimerHandler('contentMain')
			);
		this.current = new Current(new CurrentHandler('currentContent'));
		this.volume = new Volume(new VolumeHandler('navVolume'));
		this.movies = new Movies(new MovieListHandler('contentMain'));
		this.screenshots = new Screenshots(new ScreenshotHandler('contentMain'));
		this.simplepages = new SimplePages(
				new SimplePageHandler('contentMain'),
				new DeviceInfoHandler('contentMain')
			);
		
		this.navlut = {
			'tv': {
				'bouquets' : this.bouquets.loadBouquetsTv.bind(this.bouquets), 
				'provider' : this.bouquets.loadProviderTv.bind(this.bouquets),
				'all' : this.services.loadAllTv.bind(this.services),
				},
			'radio': {
				'bouquets' : this.bouquets.loadBouquetsRadio.bind(this.bouquets),
				'provider' : this.bouquets.loadProviderRadio.bind(this.bouquets),
				'all' : this.services.loadAllRadio.bind(this.services),
			},
			'timer': {
				//TODO add & use controller für timer-stuff
				'create' : this.timers.create.bind(this.timers), //TODO create Timer
				'edit' : false,
				'delete' : false,
				'toggle' : false,
			},
			'control': {
				//TODO add & use controller for Boxcontrols
				'message' : this.simplepages.loadMessage.bind(this.simplepages),
				'power' : this.simplepages.loadPower.bind(this.simplepages),
				'remote' : function(){}, //TODO loadControl
				'osdshot' : this.screenshots.shootOsd.bind(this.screenshots),
				'screenshot' : this.screenshots.shootAll.bind(this.screenshots),
				'videoshot' : this.screenshots.shootVideo.bind(this.screenshots),
				
			},
			'extras': {
				//TODO add & use controller for Extras
				'about' : this.simplepages.loadAbout.bind(this.simplepages),
				'deviceinfo' : this.simplepages.loadDeviceInfo.bind(this.simplepages),
				'gears' : this.simplepages.loadGears.bind(this.simplepages),
				'settings' : this.simplepages.loadSettings.bind(this.simplepages),
				'tools' : this.simplepages.loadTools.bind(this.simplepages),
			}
		};
	},
	
	hideNotifier: function(){
		$('notification').fade({duration : 0.5 });
	},

	notify: function(text, state){
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
			notif.appear({duration : 0.5, to: 0.9 });
			this.hideNotifierTimeout = setTimeout(hideNotifier, 10000);
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
	
	updateItems: function(){
		this.volume.load();
		this.current.load();
	},

	updateItemsLazy: function(){	
		this.services.getNowNext();
		this.services.getSubservices();
	},
	
	startUpdateCurrentPoller: function(){
		clearInterval(this.updateCurrentPoller);
		var me = this;
		this.updateCurrentPoller = setInterval(me.updateItems.bind(this), userprefs.data.updateCurrentInterval);
	},
	
	stopUpdateCurrentPoller: function(){
		clearInterval(this.updateCurrentPoller);
	},
	
	startUpdateBouquetItemsPoller: function(){
		debug("[startUpdateBouquetItemsPoller] called");
		clearInterval(updateBouquetItemsPoller);
		updateBouquetItemsPoller = setInterval(this.updateItemsLazy, userprefs.data.updateBouquetInterval);
	},
	
	stopUpdateBouquetItemsPoller: function(){
		debug("[stopUpdateBouquetItemsPoller] called");
		clearInterval(this.updateBouquetItemsPoller);
	},
	
	onHashChanged: function(isReload){
		var hash = hashListener.getHash();		
		var parts = hash.split("/");
	
		var len = parts.length;
		if(len >= 2){
			var mode = parts[1];
			if(mode != this.mode || isReload || ( len <= 2 && this.submode != '') ){
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
					default:
						return;
					}
				}
			}
		}
	},
	
	getBaseHash: function(){
		return '#!/' + this.mode + '/' + this.subMode;
	},
	
	loadDefault: function(){
		this.reloadNav('tplNavTv', 'TeleVision');
		this.bouquets.init(this.services);
		this.mode = 'tv';
		this.subMode = 'bouquets';
	},

	run: function(){
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
//		TODO initMovieList();

	},
	
	registerEvents: function(){
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
						} else if(curHost == newHost){
							element.href = window.location;
						}
					}
				}
			}.bind(this)
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
				}.bind(this)
		);
		
		//Volume
		$('navVolume').on(
			'click',
			'a.volume',
			function(event, element){
				this.volume.set(element.readAttribute('data-volume'));
			}.bind(this)
		);
		
		//Content
		var content = $('contentMain');
		
		//Servicelist
		content.on(
			'click', 
			'a.sListSLink', 
			function(event, element){
				this.services.zap(unescape(element.id));
			}.bind(this)
		);
		content.on(
			'click', 
			'a.sListServiceEpg', 
			function(event, element){
				var ref = unescape( element.readAttribute('data-servicereference') );
				this.epg.load(ref);
			}.bind(this)
		);
		content.on(
			'click', 
			'a.sListEPG',
			function(event, element){
				var target = $(element.readAttribute('data-target_id'));
				if(target){
					if(target.visible()){
						target.hide();
					} else {
						target.show();
					}
				}
			}
		);
		//Movielist
		content.on(
			'click', 
			'a.mListDelete', 
			function(event, element){
				this.movies.del(element);
			}.bind(this)
		);
		//Timerlist
		content.on(
			'click', 
			'a.tListDelete', 
			function(event, element){
				this.timers.del(element);
			}.bind(this)
		);
		content.on(
			'click', 
			'a.tListToggleDisabled', 
			function(event, element){
				this.timers.toggleDisabled(element);
			}.bind(this)
		);
		content.on(
			'click', 
			'a.tListEdit', 
			function(event, element){
				this.timers.edit(element);
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
	
	loadMovieNav: function(){
		console.log("Not implemented");
	},
	
	loadMovieList: function(){
		
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
			//The Navigation
			this.reloadNavDynamic(this.loadMovieNav, 'Movies');
			// The Movie list
			this.loadContentDynamic(this.movies.load.bind(this.movies), 'Movies');
			break;
	
		case "timer":
			//The Navigation
			this.reloadNav('tplNavTimer', 'Timer');
			// The Timerlist
			this.loadContentDynamic(this.timers.loadList.bind(this.timers), 'Timer');
			break;
	
		case "mediaplayer":
			//TODO this.loadContentDynamic(loadMediaPlayer, 'MediaPlayer');
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
	
	navigate: function(){
		
	}
});
core = new E2WebCore();