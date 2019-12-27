var AbstractContentHandler = Class.create({
	initialize: function(tpl, target, onFinished){
		this.tpl = tpl;
		this.target = target;
		this.onFinished = onFinished;
		if(this.onFinished === undefined || this.onFinished == null){
			this.onFinished = [];
		}
		this.eventsRegistered = false;
		this.provider = null;
		this.ajaxload = false;
		this.data = {};
	},

	load: function(parms, fnc){
		this.requestStarted();
		this.parms = parms;
		this.provider.load(parms, fnc);
	},

	reload: function(){
		this.requestStarted();
		this.provider.reload();
	},

	/**
	 * requestStarted
	 * if this.ajaxload is true setAjaxLoad(this.target) will be called
	 **/
	requestStarted: function(){
		if(this.ajaxload){
			core.setAjaxLoad(this.target);
		}
	},

	/**
	 *requestFinished
	 * What to do when a request has finished. Does nothing in the Abstract class definition
	 **/
	requestFinished: function(){
//		TODO requestFinished actions
	},

	/**
	 * show
	 * Show the data that has been fetched by a request (and prepared by renderXML)
	 * in this.target.
	 * Afterwards call this.finished()
	 */
	show: function(data){
		this.data = data;
		templateEngine.process(this.tpl, data, this.target, this.finished.bind(this));
	},

	/**
	 * notify
	 * fade in to show text in the $('notification') area and fade out afterwards
	 * Parameters:
	 * @text - the text of the notification
	 * @state - false == error (bgcolor red), true == success (bgcolor green)
	 */
	notify: function(text, state){
		core.notify(text, state);
	},

	/**
	 * simpleResultCallback
	 * Callback for @ onSuccess of this.simpleResultQuery()
	 * Parameters:
	 * @transport - the xmlhttp transport object
	 */
	simpleResultCallback: function(transport){
		this.provider.simpleResultCallback(transport, this.showSimpleResult.bind(this));
	},

	showSimpleResult: function(result){
		this.notify(result.getStateText(), result.getState());
	},

	registerEvents : function(){},

	/**
	 * finished
	 * Calls all functions this.onFinished contains this.registerEvents
	 * Is usually called after this.show() has finished
	 */
	finished : function(){
		if(!this.eventsRegistered){
			try{
				this.registerEvents();
			} catch (e){
				debug(e);
			}
			this.eventsRegistered = true;
		}

		if(this.onFinished !== undefined){
			for(var i = 0; i < this.onFinished.length; i++){
				var fnc = this.onFinished[i];
				if(typeof(fnc) === 'function'){
					fnc();
				}
			}
		}
	}
});

var DeviceInfoHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, target, cached){
		$super('tplDeviceInfo', target);
		this.provider = new DeviceInfoProvider(this.show.bind(this));
		this.isCached = true;
		if(cached === false)
			this.isCached = false;
		this.data = null;
	},

	load: function($super, parms, callback){
		if(this.data == null)
			$super(parms, callback);
		else
			this.show(this.data);
	},

	get: function(parms, callback){
		this.requestStarted();
		if(this.data == null){
			this.provider.load(parms,
					function(transport){
						var data = this.provider.renderXML(this.provider.getXML(transport));
						this.data = data;
						callback(data);
					}.bind(this));
		} else {
			callback(this.data);
		}
	}
});

var ExternalsHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplNavExtrasExternals', target);
		this.provider = new ExternalsProvider(this.show.bind(this));
		this.ajaxload = false;
	}
});

var SimplePageHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, target){
		$super(null, target);
	},

	show: function(tpl, data){
		templateEngine.process(tpl, data, this.target, this.finished.bind(this));
	}
});

var BouquetListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target, targetMain){
		$super('tplBouquetList', target);
		this.provider = new SimpleServiceListProvider(this.show.bind(this));
		this.ajaxload = false;
		this.targetMain = targetMain;
	},

	show : function(data){
		this.data = data;
		if($(this.target)){
			templateEngine.process(this.tpl, data, this.target, this.finished.bind(this));
		} else {
			templateEngine.process(
					'tplBouquetsAndServices',
					null,
					this.targetMain,
					function(){
						this.show(data);
					}.bind(this)
			);
		}
	}
});

var CurrentHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, curTarget, volTarget){
		$super('tplCurrent', curTarget);
		this.provider = new CurrentProvider(this.show.bind(this));
		this.volTpl = 'tplVolume';
		this.volTarget = volTarget;
	},

	show : function(data){
		this.data = data;
		templateEngine.process(this.volTpl, data, this.volTarget);
		templateEngine.process(this.tpl, data, this.target, this.finished.bind(this));
	}
});

var ServiceListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplServiceList', target, [this.getSubservices.bind(this)]);

		this.provider = new ServiceListProvider(this.show.bind(this));
		this.epgHandler = new ServiceListEpgHandler();
		this.subServiceHandler = new ServiceListSubserviceHandler();

		this.ajaxload = true;
	},

	/**
	 * getNowNext
	 * calls this.epgHandler.getNowNext to show Now/Next epg information
	 * using this.parms.sRef as the servicereference of the bouquet
	 */
	getNowNext: function(){
		this.epgHandler.load({bRef : this.provider.parms.bRef});
	},

	/**
	 * getSubservices
	 * calls this.subServiceHandler.load() to show Now/Next epg information
	 */
	getSubservices: function(){
		this.subServiceHandler.load({});
	},

	/**
	 * call this to switch to a service
	 * Parameters:
	 * @servicereference - the (unescaped) reference to the service that should be shown
	 */
	zap: function(parms, callback){
		this.provider.simpleResultQuery(
				URL.zap,
				parms,
				function(transport){
					this.simpleResultCallback.bind(this);
					if(callback)
						callback();
				}.bind(this));
	},

	showSimpleResult: function($super, result){
		if(result.getState()){
			core.updateItemsLazy();
		}
		$super(result);
	}
});

var EpgListHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, showEpgFnc){
		$super('tplEpgList');
		this.provider = new ServiceEpgListProvider(this.show.bind(this));
		this.showEpg = showEpgFnc;
		this.data = '';
	},

	search : function(parms, fnc){
		this.requestStarted();
		this.provider.search(parms, fnc);
	},

	show : function(data){
		this.data = data;
		templateEngine.fetch(
				this.tpl,
				function(){
					var html = templateEngine.templates[this.tpl].process(this.data);
					this.showEpg(html);
				}.bind(this)
			);
	}
});

var ServiceListEpgHandler  = Class.create(AbstractContentHandler, {
	EPG_NOW : 'NOW',
	EPG_NEXT : 'NEXT',
	PROGRESS : 'PROGRESS',

	initialize: function($super){
		$super('tplServiceListEPGItem');
		this.provider = new ServiceListProvider(this.show.bind(this));
	},

	/**
	 * show
	 * calls this.showItem for each item of @list
	 * @list - An array of EPGEvents
	 */
	show: function(list){
		var len = list.items.length;
		for(var i = 0; i < len; i++){
			this.updateEpg(list.items[i]);
		}
		this.finished();
	},

	/**
	 * Shows an EPGEvent item in the DOM
	 * templates.tplServiceListEPGItem needs to be present!
	 * Parameters:
	 * @item - The EPGEvent object
	 */
	//TODO: move showItem outta here
	updateEpg: function(item){
		if(item.now.eventid != ''){
			var progress = $(this.PROGRESS + item.now.servicereference);
			if(progress){
				progress.down('.sListSProgress').title = item.now.progress + "%";
				progress.down('.sListSProgressBar').style.width = item.now.progress + "%";
			}
		}
		this.showItem(this.EPG_NOW, item.now,'.sListEPGNow');
		this.showItem(this.EPG_NEXT, item.next,'.sListEPGNext');
	},

	showItem: function(type, epgItem, parent){
		var id = type + epgItem.servicereference;
		var epgElement = $(id);
		if(epgElement){ //Markers don't have any EPG
			var isVisible = false;
			var target = epgElement.down('.sListExtEpgLong');
			if(target){
				isVisible = target.visible();
			}

			templateEngine.process('tplServiceListEPGItem', {'item' : epgItem, 'isVisible' : isVisible}, id, true);
			var element = $(id).up(parent);
			if(element){
				element.show();
			}
		}
	}
});

var ServiceListSubserviceHandler  = Class.create(AbstractContentHandler, {
	//constants
	PREFIX : 'SUB',

	initialize: function($super){
		$super('tplSubServices');
		this.provider = new ServiceListSubserviceProvider(this.show.bind(this));
	},

	/**
	 * show
	 * Show all subervices of a service (if there are any)
	 * Overrides default show
	 */
	show: function(list){
		var id = this.PREFIX + list[0].servicereference;
		var parent = $('tr' + id);

		if(parent !== null && list.length > 1){
			list.shift();

			var data = { subservices : list };
			templateEngine.process(this.tpl, data, id);
			parent.show();
		}
	}
});

var SignalHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, showSignalFnc){
		$super('tplSignalPanel');
		this.provider = new SignalProvider(this.show.bind(this));
		this.showSignal = showSignalFnc;
	},

	show : function(data){
		this.data = data;
		templateEngine.fetch(
				this.tpl,
				function(){
					var html = templateEngine.templates[this.tpl].process(this.data);
					this.showSignal(html);
				}.bind(this)
			);
	}
});

var MediaPlayerHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplMediaPlayer', target);
		this.provider = new MediaPlayerProvider(this.show.bind(this));
	},

	command: function(command){
		this.provider.simpleResultQuery(
				URL.mediaplayercmd,
				{'command' : command},
				this.simpleResultCallback.bind(this)
			);
	},

	playFile: function(file){
		this.provider.simpleResultQuery(
				URL.mediaplayerplay,
				{'file' : file},
				this.simpleResultCallback.bind(this)
			);
	},

	addFile: function(file){
		this.provider.simpleResultQuery(
				URL.mediaplayeradd,
				{'file' : file},
				this.simpleResultCallback.bind(this)
			);
	},

	removeFile: function(file){
		this.provider.simpleResultQuery(
				URL.mediaplayerremove,
				{'file' : file},
				function(data){
					this.simpleResultCallback(data);
					this.reload();
				}.bind(this)
			);
	},

	savePlaylist: function(filename){
		this.provider.simpleResultQuery(
				URL.mediaplayerwrite,
				{'filename' : filename},
				this.simpleResultCallback.bind(this)
			);
	}

});

var MovieListHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplMovieList', target);
		this.provider = new MovieListProvider(this.show.bind(this));
		this.ajaxload = true;
	},

	getData: function(element){
		/*<table
			class="mListItem"
			data-servicereference="${movie.servicereference}"
			data-servicename="${movie.servicename}"
			data-title="${movie.title}"
			data-description="${movie.description}">
		*/
		var parent = element.up('.mListItem');
		var m = {
				servicereference : decodeURIComponent(parent.readAttribute('data-servicereference')),
				servicename : unescape(parent.readAttribute('data-servicename')),
				title : unescape(parent.readAttribute('data-title')),
				description : unescape(parent.readAttribute('data-description'))
		};

		return m;
	},

	/**
	 * del
	 * Deletes a movie
	 * Parameters:
	 * @servicereference - the servicereference of the movie that should be deleted
	 * @servicename - the name of the service the movie was recorded from
	 * @title - the title of the movie
	 * @description - the description of the movie
	 */
	del: function(element){
		var movie = this.getData(element);
		var result = confirm( "Are you sure want to delete the Movie?\n" +
				"Servicename: " + movie.servicename + "\n" +
				"Title: " + movie.title + "\n" +
				"Description: " + movie.description + "\n");

		if(result){
			debug("[MovieListProvider.del] ok confirm panel");
			this.provider.simpleResultQuery(URL.moviedelete, {sRef : movie.servicereference}, this.onDeleted.bind(this));
		}
		else{
			debug("[MovieListProvider.del] cancel confirm panel");
			result = false;
		}

		this.refresh = result;
		return result;
	},

	/**
	 * del
	 * Display the del result and reloads the movielist
	 */
	onDeleted: function(transport){
		this.simpleResultCallback(transport);
		this.reload();
	}
});

var MovieNavHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, tagTarget, locTarget){
		$super('tplMovieTags', tagTarget);
		this.targetLocations = locTarget;
		this.tplLocations = 'tplMovieLocations';
	},

	load: function(locations, tags){
		var data = { 'locations' : locations, 'tags' : tags};
		this.show(data);
		this.showLocations(data);
	},

	showLocations: function(data){
		templateEngine.process(this.tplLocations, data, this.targetLocations);
	}
});

var MultiEpgHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, showMultiEpgFnc){
		$super('tplMultiEpg', null);
		this.provider = new MultiEpgProvider(this.show.bind(this));
		this.ajaxload = false;
		this.showEpg = showMultiEpgFnc;
	},

	show : function(data){
		this.data = data;
		templateEngine.fetch(
			this.tpl,
			function(){
				var html = templateEngine.templates[this.tpl].process(this.data);
				this.showEpg(html);
			}.bind(this)
		);
	}
});

var ScreenshotHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplGrab', target);
		this.provider = new ScreenshotProvider(this.show.bind(this));
		this.ajaxload = true;
	}
});

var SimpleRequestHandler = Class.create(AbstractContentHandler,{
	initialize: function($super){
		$super();
		this.provider = new SimpleRequestProvider();
	},

	load: function(url, parms){
		this.provider.simpleResultQuery(
				url,
				parms,
				this.simpleResultCallback.bind(this)
			);
	}
});

var RemoteControlHandler = Class.create(SimpleRequestHandler,{
	sendKey: function(parms){
		this.load(URL.remotecontrol, parms);
	},

	showSimpleResult: function(result){
		this.finished();
		if(!result.getState())
			this.notify(result.getStateText(), result.getState());
	}
});

var TimerListHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplTimerList', target);
		this.provider = new TimerListProvider(this.show.bind(this));
		this.ajaxload = true;
	},

	cleanup: function(){
		this.provider.simpleResultQuery(
				URL.timercleanup, {},
				function(transport, callback){
					this.simpleResultCallback(transport, callback);
					this.reload();
				}.bind(this));
	}
});

var TimerHandler = Class.create(AbstractContentHandler, {
	ACTIONS: [{value : 0, txt : strings.record},
			{value : 1, txt : strings.zap}],

	AFTEREVENTS: [{value : 0, txt : strings.do_nothing},
				{value : 1, txt : strings.standby},
				{value : 2, txt : strings.shutdown},
				{value : 3, txt : strings.auto}],

	SELECTED : "selected",
	CHECKED: "checked",

	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, target, reloadCallback, onFinished){
		$super('tplTimerEdit', target, onFinished);
		this.t = {};
		this.provider = new SimpleRequestProvider();
		this.bouquetListProvider = new SimpleServiceListProvider(this.onBouquetsReady.bind(this));
		this.serviceListProvider = new SimpleServiceListProvider(this.onServicesReady.bind(this));
		this.ajaxload = true;
		this.reloadCallback = reloadCallback;
		this.data = {};
	},

	simpleResultCallback: function(transport, callback){
		this.provider.simpleResultCallback(
				transport,
				function(result){
					this.showSimpleResult(result, callback);
				}.bind(this)
			);
	},

	showSimpleResult: function($super, result, callback){
		$super(result);
		if(callback){
			callback(result);
			return;
		} else if(this.reloadCallback){
			this.reloadCallback();
		}
	},

	toReadableDate: function(date){
		var dateString = "";
		dateString += date.getFullYear();
		dateString += "-" + addLeadingZero(date.getMonth()+1);
		dateString += "-" + addLeadingZero(date.getDate());

		return dateString;
	},

	/**
	 * getData
	 *
	 * Extracts the data of a timer from the .tListItem elements data-* attributes
	 *
	 * <tr class="tListItem"
	 * 	data-servicereference="${t.servicereference}"
	 * 	data-servicename="${t.servicename}"
	 * 	data-description="${t.description}"
	 * 	data-name="${t.name}"
	 * 	data-eventid="${t.eventid}"
	 * 	data-begin="${t.begin}"
	 * 	data-end="${t.end}"
	 * 	data-repeated="${t.repeated}"
	 * 	data-justplay="${t.justplay}"
	 * 	data-dirname="${t.dirname}"
	 * 	data-tags="${t.tags}"
	 * 	data-afterevent="${t.afterevent}"
	 * 	data-disabled="${t.disabled}"
	 * >
	 *
	 * Parameters:
	 * @element - the html element calling the load function ( onclick="TimerProvider.load(this)" )
	 */
	getData: function(element, setOld){
		var parent = element.up('.tListItem');
		var t = {};

		if(parent){
			var begin = unescape(parent.readAttribute('data-begin'));
			var end = unescape(parent.readAttribute('data-end'));
			var beginD = new Date(begin * 1000);
			var endD = new Date(end * 1000);
			t = {
				servicereference : decodeURIComponent(parent.readAttribute('data-servicereference')),
				servicename : unescape(parent.readAttribute('data-servicename')),
				description : unescape(parent.readAttribute('data-description')),
				name : unescape(parent.readAttribute('data-name')),
				eventid : unescape(parent.readAttribute('data-eventid')),
				begin : begin,
				beginDate : this.toReadableDate(beginD),
				end : end,
				endDate : this.toReadableDate(endD),
				repeated : unescape(parent.readAttribute('data-repeated')),
				justplay : unescape(parent.readAttribute('data-justplay')),
				dirname : unescape(parent.readAttribute('data-dirname')),
				tags : unescape(parent.readAttribute('data-tags')),
				afterevent : unescape(parent.readAttribute('data-afterevent')),
				disabled : unescape(parent.readAttribute('data-disabled'))
			};

			if(setOld){
				t['servicereferenceOld'] = decodeURIComponent(parent.readAttribute('data-servicereference'));
				t['beginOld'] = t.begin;
				t['endOld'] = t.end;
				t['deleteOldOnSave'] = 1;
			} else {
				t['deleteOldOnSave'] = 0;
			}
		}
		return t;
	},

	getDataFromEvent: function(element){
		var parent = element.up('.epgListItem');
		var t = {};

		if(parent){
			var begin = unescape(parent.readAttribute('data-start'));
			var end = unescape(parent.readAttribute('data-end'));
			var beginD = new Date(begin * 1000);
			var endD = new Date(end * 1000);
			t = {
				servicereference : decodeURIComponent(parent.readAttribute('data-servicereference')),
				servicename : unescape(parent.readAttribute('data-servicename')),
				description : unescape(parent.readAttribute('data-description')),
				name : unescape(parent.readAttribute('data-title')),
				eventid : unescape(parent.readAttribute('data-eventid')),
				begin : begin,
				beginDate : this.toReadableDate(beginD),
				end : end,
				endDate : this.toReadableDate(endD),
				repeated : "0",
				justplay : "0",
				dirname : "",
				tags : "",
				afterevent : "3",
				disabled : "0",
				deleteOldOnSave : "0"
			};
		}
		return t;
	},


	/**
	 * @override
	 * load
	 * When handling timers the whole loading-sequence is entirely different.
	 * Most of the data is already there or has to be created.
	 *
	 * Parameters:
	 * @element - the html element calling the load function ( onclick="TimerProvider.load(this)" )
	 */
	load: function(element, setOld, initial, fromEvent){
		var t = {};
		var begin = new Date();
		var end = new Date();

		if(initial){
			end.setHours(end.getHours() + 1);
			t = {
				servicereference : "",
				servicename : "",
				description : "",
				name : "",
				eventid : "0",
				begin : "0",
				beginDate : this.toReadableDate(begin),
				end : "0",
				endDate : this.toReadableDate(end),
				repeated : "0",
				justplay : "0",
				dirname : "",
				tags : "",
				afterevent : "3",
				disabled : "0"
			};
		} else {
			if(fromEvent){
				t = this.getDataFromEvent(element);
			} else {
				t = this.getData(element, setOld);
			}
			begin = new Date(t.begin * 1000);
			end = new Date(t.end * 1000);
		}


		var bHours = this.numericalOptionList(0, 23, begin.getHours());
		var bMinutes = this.numericalOptionList(0, 59, begin.getMinutes());
		var eHours = this.numericalOptionList(0, 23, end.getHours());
		var eMinutes = this.numericalOptionList(0, 59, end.getMinutes());

		var actions = this.ACTIONS;
		for (var i = 0; i < actions.length; i++) {
			delete actions[i].selected;
		}
		actions[t.justplay].selected = this.SELECTED;

		var afterevents = this.AFTEREVENTS;
		for (var i = 0; i < afterevents.length; i++) {
			delete afterevents[i].selected;
		}
		afterevents[t.afterevent].selected = this.SELECTED;

		var repeated = this.repeatedDaysList(t.repeated);

		var data = {
				shour : bHours,
				smin : bMinutes,
				ehour : eHours,
				emin : eMinutes,
				action : actions,
				channel : [],
				afterEvent : afterevents,
				repeated : repeated,
				timer : t };
		var _this = this;
		core.lt.getLocationsAndTags(function(currentLocation, locations, tags){
			_this.onLocationsAndTagsReady(data, currentLocation, locations, tags, initial);
		});
	},

	onLocationsAndTagsReady: function(data, currentLocation, locations, tags, initial){
		var dirname = data.timer.dirname;
		if(dirname == "")
			dirname = currentLocation;
		var l = toOptionList(locations, dirname);
		var t = toOptionList(tags, data.timer.tags, " ");
		t.shift();
		l.shift();

		data['dirname'] = l;
		data['tags'] = t;
		if(initial){
			data.timer.dirname = currentLocation;
		}
		this.data = data;
		this.bouquetListProvider.load({'sRef' : bouquetsTv});
	},

	onBouquetsReady: function(data){
		this.data['bouquets'] = data.services;
		this.serviceListProvider.load({'sRef' : unescape(data.services[0].servicereference)});
	},

	onServicesReady: function(data){
		var services = data.services;
		var serviceFound = false;
		var timer = this.data.timer;
		services.each(function(service){
			if(decodeURIComponent(service.servicereference) == timer.servicereference){
				service['selected'] = 'selected';
				serviceFound = true;
			} else if (decodeURIComponent(service.servicereference)
				   .startsWith("1:64:")) {
				service['selected'] = 'disabled';
			} else {
				service['selected'] = '';
			}
		}.bind(this));
		if ((timer.servicereference != "") && !serviceFound) {
			services.push( {'servicereference' : timer.servicereference, 'servicename' : timer.servicename, 'selected' : 'selected'});
		}

		this.data['services'] = services;
		this.show(this.data);
	},

	onBouquetChanged: function(bRef, callback){
		var _this = this;
		var fnc = function(data){
			callback(data, _this.data.timer);
		};
		var prov = new SimpleServiceListProvider(fnc);
		prov.load({'sRef' : bRef});
	},

	recordNow: function(type, callback){
		this.provider.simpleResultQuery(
			URL.recordnow,
			{
				'recordnow' : type
			},
			function(result){
				if(!callback)
					callback = function(){}; //Avoid automatic reload
				this.simpleResultCallback(result, callback);
			}.bind(this));
	},

	addByEventId: function(sRef, id, justplay){
		this.provider.simpleResultQuery(
			URL.timeraddbyeventid,
			{
				'sRef' : sRef,
				'eventid' : id,
				'justplay' : justplay
			},
			this.simpleResultCallback.bind(this));
	},

	change: function(t, old){
		var parms = {
			'sRef' : t.servicereference,
			'begin' : t.begin,
			'end' : t.end,
			'name' : t.name,
			'description' : t.description,
			'dirname' : t.dirname,
			'tags' : t.tags,
			'afterevent' : t.afterevent,
			'eit' : t.eventid,
			'disabled' : t.disabled,
			'justplay' : t.justplay,
			'repeated' : t.repeated
		};

		if(old){
			Object.extend(parms, {
				'channelOld' : old.servicereference,
				'beginOld' : old.begin,
				'endOld' : old.end,
				'deleteOldOnSave' : old.deleteOldOnSave
			});
		} else {
			parms['deleteOldOnSave'] = 0;
		}

		this.provider.simpleResultQuery(
			URL.timerchange,
			parms,
			this.simpleResultCallback.bind(this)
		);
	},

	del: function(element){
		var t = this.getData(element);
		var result = confirm("Selected timer:\n" + "Channel: " + t.servicename + "\n" +
				"Name: " + t.name + "\n" + "Description: " + t.description + "\n" +
				"Are you sure that you want to delete the Timer?");
		if (result) {
			debug("[TimerListProvider].del ok confirm panel");
			this.refresh = true;
			this.provider.simpleResultQuery(
					URL.timerdelete,
					{'sRef' : t.servicereference, 'begin' : t.begin, 'end' : t.end},
					this.simpleResultCallback.bind(this)
				);
		}
		return result;
	},

	toggleDisabled: function(element){
		var t = this.getData(element, true);
		var old = t;
		if(t.disabled == '0')
			t.disabled = '1';
		else
			t.disabled = '0';
		this.change(t, old);
	},

	/**
	 * repeatedDaysList
	 *
	 * Parameters:
	 * @num - the decimal value to apply as bitmask
	 * @return - a list of {id : dayid, value : dayvalue, txt : daytext, long : daylong}
	 **/
	repeatedDaysList: function(num){
		var days = [{id : 'mo', value : 1, txt : 'Mo', long : 'Monday'},
					{id : 'tu', value : 2, txt : 'Tu', long : 'Tuesday'},
					{id : 'we', value : 4, txt : 'We', long : 'Wednesday'},
					{id : 'th', value : 8, txt : 'Th', long : 'Thursday'},
					{id : 'fr', value : 16, txt : 'Fr', long : 'Friday'},
					{id : 'sa', value : 32, txt : 'Sa', long : 'Saturday'},
					{id : 'su', value : 64, txt : 'Su', long : 'Sunday'},
					{id : 'mf', value : 31, txt : 'Mo-Fr', long : 'Monday to Friday'},
					{id : 'ms', value : 127, txt : 'Mo-Su', long : 'Monday to Sunday'}
					];
		var orgNum = num;
		// num is the decimal value of the bitmask for checked days
		for(var i = 0; i < days.length; i++){
			days[i].checked = "";

			//set checked when most right bit is 1
			if(num &1 == 1){
				days[i].checked = this.CHECKED;
			}

			// shift one bit to the right
			num = num >> 1;
		}

		//check for special cases (Mo-Fr & Mo-Su)
		if(orgNum == 31){
			days[7].checked = this.CHECKED;
		} else if (orgNum == 127){
			days[8].checked = this.CHECKED;
		}

		return days;
	},

	/**
	 * numericalOptionList
	 * Create a List of numerical-based options
	 * Entry.value is being extended to at least 2 digits (9 => 09)
	 *
	 * Parameters:
	 * @lowerBound - Number to start at
	 * @upperBound - Number to stop at
	 * @selectedValue - entry.selected is set to this.SELECTED if number == selectedValue ("" else)
	 **/
	numericalOptionList: function(lowerBound, upperBound, selectedValue, offset){
		var list = [];
		var idx = 0;
		if(offset == undefined){
			offset = 0;
		}

		for(var i = lowerBound; i <= upperBound; i++){
			var t = i + offset;
			var txt = t < 10 ? "0" + t : t;
			var selected = "";
			if(i == selectedValue){
				selected = this.SELECTED;
			}
			list[idx] = {value : i, txt : txt, selected : selected};
			idx++;
		}
		return list;
	},

	/**
	 * daysOptionList
	 *
	 * Determines how many Days a month has an builds an
	 * numericalOptionsList for that number of Days
	 */
	daysOptionList: function(date){
		var days = 32 - new Date(date.getYear(), date.getMonth(), 32).getDate();
		return this.numericalOptionList(1, days, date.getDate());
	},

	/**
	 * commitForm
	 *
	 * Commit the Timer Form by serializing it, generating the correct paramteters and then executing the change Method
	 * @id - id of the Form
	 */
	commitForm : function(id){
		debug("TimerHandler.commitForm");
		var values = $(id).serialize(true);

		var tags = [];
		$$('.tEditTag').each(function(element){
			var selected = element.readAttribute('data-selected');
			if(selected == "selected"){
				var value = element.readAttribute('data-value');
				tags.push(value);
			}
		});

		var repeated = 0;
		$$('.tEditRepeated').each(function(element){
			if(element.checked){
				if(element.value != 31 && element.value != 127){
					repeated += Number(element.value);
				}
			}
		});

		var begin = 0;
		var end = 0;

		var startDate = $('sdate').value.split('-');
		var sDate = new Date();
		sDate.setFullYear(startDate[0], startDate[1] - 1, startDate[2]);
		sDate.setHours( $('shour').value );
		sDate.setMinutes( $('smin').value );
		sDate.setSeconds(0);
		begin = Math.floor(sDate.getTime() / 1000);

		var endDate = $('edate').value.split('-');
		var eDate = new Date();
		eDate.setFullYear(endDate[0], endDate[1] - 1, endDate[2]);
		eDate.setHours( $('ehour').value );
		eDate.setMinutes( $('emin').value );
		eDate.setSeconds(0);
		end = Math.floor(eDate.getTime() / 1000);

		timer = {
			'servicereference' : decodeURIComponent(values.service),
			'begin' : begin,
			'end' : end,
			'name' : values.name,
			'eventid' : values.eventid,
			'description' : values.description,
			'dirname' : values.dirname,
			'tags' : tags.join(" "),
			'afterevent' : values.afterevent,
			'eit' : 0,
			'disabled' : values.disabled,
			'justplay' : values.justplay,
			'repeated' : repeated
		};
		var old = null;
		if(values.deleteOldOnSave == "1"){
			old = {
				'servicereference' : decodeURIComponent(values.servicereferenceOld),
				'begin' : values.beginOld,
				'end' : values.endOld,
				'deleteOldOnSave' : values.deleteOldOnSave
			};
		}

		debug(timer);
		debug(old);
		this.change(timer, old);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new TimerList(xml).getArray();
		return {timer : list};
	}
});


var VolumeHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplVolume', target);
		this.provider = new VolumeProvider(this.show.bind(this));
		this.ajaxload = false;
	}
});
