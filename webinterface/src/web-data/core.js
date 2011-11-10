var Controller = Class.create({
	initialize: function(model){
		this.model = model;
		this.model.onFinished[this.model.onFinished.length] = this.registerEvents.bind(this);
		this.eventsregistered = false;
	},

	registerEvents: function(){
		this.eventsregistered = true;
		debug('[Controller] INFO: registerEvents not implemented in derived class');
	}
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
});

var Current = Class.create(Controller, {
	initialize: function($super, model){
		$super(model);
		this.display = 'none';
		this.model.onFinished[this.model.onFinished.length] = this.restoreDisplayStyle.bind(this);
	},
	
	load: function(){
		try{
			this.display = $('trExtCurrent').style.display;
		} catch(e){}
		this.model.load({});
	},
	
	restoreDisplayStyle: function(){
		$('trExtCurrent').style.display = this.display;
	}
});

var Services = Class.create(Controller, {
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
	},

	loadAllRadio: function(){
		this.load(allRadio);
	},
	
	registerEvents: function(){
		if(!this.eventsRegistered){
			this.eventsRegistered = true;
			
			var parent = $(this.model.target);
			parent.on(
				'click', 
				'a.sListSLink', 
				function(event, element){
					this.model.zap(unescape(element.id));
				}.bind(this)
			);
			
			parent.on(
				'click', 
				'a.sListServiceEpg', 
				function(event, element){
					var ref = unescape( element.readAttribute('data-servicereference') );
					
					//TODO replace with EPG-Handler call
					loadEPGByServiceReference( ref );
				}.bind(this)
			);
			
			parent.on(
				'click', 
				'a.sListEPG',
				function(event, element){
					var target = $(element.readAttribute('data-target_id'));
					
					if(target.visible()){
						target.hide();
					} else {
						target.show();
					}
				}
			);
		}
	},
});

var Timers = Class.create(Controller, {
	load: function(){
		this.model.load({});
	}
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
		
		//create required Instances
		this.services = new Services(new ServiceListHandler('contentServices'));
		this.bouquets = new Bouquets(new BouquetListHandler('contentBouquets', 'contentMain'));
		this.timers = new Timers(new TimerListHandler('contentMain'));
		this.current = new Current(new CurrentHandler('currentContent'));
		this.volume = new Volume(new VolumeHandler('navVolume'));
		
		this.epgListHandler = new EpgListHandler();
		this.movieListHandler = new MovieListHandler('contentMain');
		this.timerHandler = new TimerHandler('contentMain');
	},
	
	hideNotifier: function(){
		$('notification').fade({duration : 0.5 });
	},

	notify: function(text, state){
		notif = $('notification');

		if(notif !== null){
			//clear possibly existing hideNotifier timeout of a previous notfication
			clearTimeout(hideNotifierTimeout);
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
		$(targetElement).update( getAjaxLoad() );
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
		this.registerEvents();
		
//		TODO getBoxtype();

		this.setAjaxLoad('navContent');
		this.setAjaxLoad('contentMain');

		templateEngine.fetch('tplServiceListEPGItem');
		templateEngine.fetch('tplBouquetsAndServices');
		templateEngine.fetch('tplCurrent');

		this.reloadNav('tplNavTv', 'TeleVision');
		this.updateItems();
		this.bouquets.init(this.services);
		
//		TODO initMovieList();
		this.startUpdateCurrentPoller();
	},
	
	registerEvents: function(){	
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
	
		nav = $('navContent');
		nav.on(
			'click',
			'#loadBouquetsTv',
			function(event, element){
				this.bouquets.loadBouquetsTv();
			}.bind(this)
		);
		nav.on(
			'click',
			'#loadProviderTv',
			function(event, element){
				this.bouquets.loadProviderTv();
			}.bind(this)
		);
		nav.on(
			'click',
			'#loadAllTv',
			function(event, element){
				this.services.loadAllTv();
			}.bind(this)
		);
		nav.on(
			'click',
			'#loadBouquetsRadio',
			function(event, element){
				this.bouquets.loadBouquetsRadio();
			}.bind(this)
		);
		nav.on(
			'click',
			'#loadProviderRadio',
			function(event, element){
				this.bouquets.loadProviderRadio();
			}.bind(this)
		);
		nav.on(
			'click',
			'#loadAllRadio',
			function(event, element){
				this.services.loadAllRadio();
			}.bind(this)
		);
		
		mainMenu = $('mainMenu');
		mainMenu.on(
			'click',
			'a.switchMode',
			function(event, element){
				this.switchMode(element.readAttribute('data-mode'));
			}.bind(this)
		);
		
		$('navVolume').on(
			'click',
			'a.volume',
			function(event, element){
				this.volume.set(element.readAttribute('data-volume'));
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
	loadContentDynamic: function(fnc, title, domid){
		if(domid !== undefined && $(domid) != null){
			this.setAjaxLoad(domid);
		} else {
			this.setAjaxLoad('contentMain');
		}
		setContentHd(title);
		this.stopUpdateBouquetItemsPoller();

		fnc();
	},

	/*
	 * like loadContentDynamic but without the AjaxLoaderAnimation being shown
	 */
	reloadContentDynamic: function(fnc, title){
		setContentHd(title);
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
		case "TV":
			if(currentMode != 'TV' && currentMode != 'Radio'){
				this.services.registerEvents();
			}
			this.reloadNav('tplNavTv', 'TeleVision');
			break;
	
		case "Radio":
			if(currentMode != 'TV' && currentMode != 'Radio'){
				this.services.registerEvents();
			}		
			this.reloadNav('tplNavRadio', 'Radio');
			break;
	
		case "Movies":	
			//The Navigation
			this.reloadNavDynamic(this.loadMovieNav, 'Movies');
			// The Movie list
			this.loadContentDynamic(this.loadMovieList, 'Movies');
			break;
	
		case "Timer":
			//The Navigation
			this.reloadNav('tplNavTimer', 'Timer');
			// The Timerlist
			fnc = this.timers.load.bind(this.timers);
			this.loadContentDynamic(fnc, 'Timer');
			break;
	
		case "MediaPlayer":
			this.loadContentDynamic(loadMediaPlayer, 'MediaPlayer');
			break;
	
		case "BoxControl":
			this.reloadNav('tplNavBoxControl', 'BoxControl');
			break;
	
		case "Extras":
			this.reloadNav('tplNavExtras', 'Extras');
			break;
			
		default:
			break;
		}
	},
});
core = new E2WebCore();