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
		this.provider.load(parms, fnc);
	},	
	
	reload: function(){
		this.load(this.parms);
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
	
	//TODO insert renderTpl, templateEngine.process & Co. here or somewhere else... (maybe a separate class?)
	
	/**
	 * show
	 * Show the data that has been fetched by a request (and prepared by renderXML)
	 * in this.target.
	 * Afterwards call this.finished()
	 */
	show : function(data){
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
	
	registerEvents : function(){
		debug('[AbstractContentHandler] WARNING: registerEvents not implemented in derived class!');
	},
	
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
	initialize: function($super, target){
		$super('tplDeviceInfo', target);
		this.provider = new DeviceInfoProvider(this.show.bind(this));
	},
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
		this.provider = new BouquetListProvider(this.show.bind(this));	
		this.ajaxload = false;
		this.serviceController = null;
		this.targetMain = targetMain;
		this.initServiceList = false;
	},
	
	init: function(params, controller){
		this.serviceController = controller;
		this.initServiceList = true;
		this.load(params);
	},
	
	show : function(data){
		this.data = data;
		if($(this.target) != null && $(this.target != undefined)){
			templateEngine.process(this.tpl, data, this.target,  this.finished.bind(this));
			if(this.initServiceList){
				this.serviceController.load(decodeURIComponent(data.bouquets[0].servicereference));
				this.initServiceList = false;
			}
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
	},
});

var CurrentHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplCurrent', target);
		this.provider = new CurrentProvider(this.show.bind(this));
	}	
});

var ServiceListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplServiceList', target, [this.getNowNext.bind(this),this.getSubservices.bind(this)]);

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
		this.epgHandler.provider.getNowNext({bRef : this.provider.parms.sRef});
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
	zap: function(parms){
		this.provider.simpleResultQuery(URL.zap, parms, this.simpleResultCallback.bind(this));
		core.updateItemsLazy();
	},
});

var EpgListHandler = Class.create(AbstractContentHandler,{
	initialize: function($super){
		$super('tplEpgList');
		this.provider = new ServiceEpgListProvider(this.show.bind(this));
		this.window = '';
		this.data = '';
	},
	
	search : function(parms, fnc){
		this.requestStarted();
		this.provider.search(parms, fnc);
	},
	
	show : function(data){
		this.data = data;
		templateEngine.fetch(this.tpl, this.showEpg.bind(this));		
	},
	
	showEpg: function(){
		var html = templateEngine.templates[this.tpl].process(this.data);

		if (!this.window.closed && this.window.location) {
			core.setWindowContent(this.window, html);
		} else {
			this.window = core.popup("EPG", html, 900, 500);
		}
	}
});

var ServiceListEpgHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super){
		$super('tplServiceListEPGItem');
		this.provider = new ServiceListEpgProvider(this.show.bind(this));
	},
	
	/**
	 * show
	 * calls this.showItem for each item of @list
	 * @list - An array of EPGEvents
	 */	
	show: function(list, type){
		for(var i = 0; i < list.length; i++){
			this.showItem(list[i], type);
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
	showItem: function(item, type){
		if(item.eventid != ''){
			var data = { epg : item, nownext: type };
			var id = type + item.servicereference;
	
			templateEngine.process('tplServiceListEPGItem', data, id, true);

			var element = $('tr' + id);
			if(element !== null){
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
				servicereference : unescape(parent.readAttribute('data-servicereference')),
				servicename : unescape(parent.readAttribute('data-servicename')),
				title : unescape(parent.readAttribute('data-title')),
				description : unescape(parent.readAttribute('data-description')),
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
		movie = this.getData(element);
		
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

var ScreenshotHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplGrab', target);
		this.provider = new ScreenshotProvider(this.show.bind(this));
		this.ajaxload = true;
	},
});

var TimerListHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplTimerList', target);
		this.provider = new TimerListProvider(this.show.bind(this));
		this.ajaxload = true;
	}	
});

var TimerHandler = Class.create(AbstractContentHandler, {	
	ACTIONS: [{value : 0, txt : 'Record'}, 
	          {value : 1, txt : 'Zap'}],
	
	AFTEREVENTS: [{value : 0, txt : 'Nothing'}, 
	              {value : 1, txt : 'Standby'}, 
	              {value : 2, txt : 'Deepstandby/Shutdown'}, 
	              {value : 3, txt : 'Auto'}],
	
	SELECTED : "selected",
	CHECKED: "checked",
	
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, target){
		$super('tplTimerEdit', target);
		this.t = {};
		this.ajaxload = true;
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
	 * 	data-title="${t.title}"
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
	getData: function(element){
		var parent = element.up('.tListItem');
		var t = {};
		if(parent){
			t = {
					servicereference : parent.readAttribute('data-servicereference'),
					servicename : parent.readAttribute('data-servicename'),
					description : parent.readAttribute('data-description'),
					title : parent.readAttribute('data-title'),
					begin : parent.readAttribute('data-begin'),
					end : parent.readAttribute('data-end'),
					repeated : parent.readAttribute('data-repeated'),
					justplay : parent.readAttribute('data-justplay'),
					dirname : parent.readAttribute('data-dirname'),
					tags : parent.readAttribute('data-tags'),
					afterevent : parent.readAttribute('data-afterevent'),
					disabled : parent.readAttribute('data-disabled')				
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
	load : function(element){
		var t = this.getData(element);
			
		var begin = new Date(t.begin * 1000);
		var end = new Date(t.end * 1000);	
		
		var bHours = this.numericalOptionList(1, 24, begin.getHours());		
		var bMinutes = this.numericalOptionList(1, 60, begin.getMinutes());
		var eHours = this.numericalOptionList(1, 24, end.getHours());		
		var eMinutes = this.numericalOptionList(1, 60, end.getMinutes());
		
		var now = new Date();
		var years = this.numericalOptionList(now.getFullYear(), now.getFullYear() + 10, begin.getFullYear());
		var months = this.numericalOptionList(0, 11, begin.getMonth(), 1);
		var days = this.daysOptionList(begin);
		
		var actions = this.ACTIONS;
		actions[t.justplay].selected = this.SELECTED;
		
		var afterevents = this.AFTEREVENTS;
		afterevents[t.afterevent].selected = this.SELECTED;
		
		var repeated = this.repeatedDaysList(t.repeated);
		
		var data = { 
				year : years,
				month : months,
				day : days,
				shour : bHours,
				smin : bMinutes,
				ehour : eHours,
				emin : eMinutes,
				action : actions,
				channel : [],
				afterEvent : afterevents,
				repeated : repeated,
				dirname : [],
				tags : [],
				timer : t };
		
		this.show(data);
	},
	
	toggleDisabled: function(element){
		//TODO implement toggleDisabled
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
		
		
		//check for special cases (Mo-Fr & Mo-Su)
		if(num == 31){
			days[7].checked = this.CHECKED;
		} else if (num == 127){
			days[8].checked == this.CHECKED;
		}

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
	 * Commit the Timer Form by serialing it and doing executing the request
	 * @id - id of the Form
	 */
	commitForm : function(id){		
		var values = $(id).serialize();
		debug(values);
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */	
	renderXML: function(xml){
		var list = new TimerList(xml).getArray();
		return {timer : list};
	},
	
	registerEvents: function(){
		$('saveTimer').on('click', function(event, element){
					this.commitForm('timerEditForm');
				}.bind(this)
			);
		
		$('month').on('change', function(event, element){			
				this.reloadDays();
			}.bind(this)
		);
		
		$('year').on('change', function(event, element){			
				this.reloadDays();
			}.bind(this)
		);
		
	},
	
	reloadDays : function(){
		var date = new Date($('year').value, $('month').value, $('day').value);
		var days = this.daysOptionList(date);
						
		$('day').update('');
		this.createOptions(days, $('day'));
	},
	
	createOptions: function(items, element){		
		for(var i = 0; i < items.length; i++){
			var item = items[i];
			
			var attrs = { value : item.value };
			if(item.selected == this.SELECTED){
				attrs = { value : item.value, selected : item.selected };
			}
			var option = new Element('option', attrs).update(item.txt);				
			
			element.appendChild(option);
		}
	}
});


var VolumeHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplVolume', target);
		this.provider = new VolumeProvider(this.show.bind(this));
		this.ajaxload = false;
	}	
});
//create required Instances
//var serviceListHandler = new ServiceListHandler('contentServices');
//var epgListHandler = new EpgListHandler();
//var movieListHandler = new MovieListHandler('contentMain');
//var timerListHandler = new TimerListHandler('contentMain');
//var timerHandler = new TimerHandler('contentMain');