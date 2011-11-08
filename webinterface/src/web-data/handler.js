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
	},
	
	load: function(parms, fnc){
		this.requestStarted();
		this.provider.load(parms, fnc);
	},	
	
	
	/**
	 * requestStarted
	 * if this.ajaxload is true setAjaxLoad(this.target) will be called
	 **/
	requestStarted: function(){
		if(this.ajaxload){
			setAjaxLoad(this.target);
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
		notif = $('notification');

		if(notif !== null){
			//clear possibly existing hideNotifier timeout of a previous notfication
			clearTimeout(hideNotifierTimeout);
			if(state === false){
				notif.style.background = "#C00";
			} else {
				notif.style.background = "#85C247";
			}				

			notif.update("<div>"+text+"</div>");
			notif.appear({duration : 0.5, to: 0.9 });
			hideNotifierTimeout = setTimeout(hideNotifier, 10000);
		}
	},
	
	/**
	 * simpleResultCallback
	 * Callback for @ onSuccess of this.simpleResultQuery()
	 * if this.refresh == true this.reload is being called
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

var BouquetListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplBouquetList', target);
		this.provider = new BouquetListProvider(this.show.bind(this));	
		this.ajaxload = false;
		this.serviceController = null;
		this.initServiceList = false;
	},
	
	init: function(params, controller){
		this.serviceController = controller;
		this.initServiceList = true;
		this.load(params);
	},
	
	show : function(data){
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
					'contentMain',
					function(){
						this.show(data);
					}.bind(this)
			);
		}
	},
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
	zap: function(ref){
		this.provider.simpleResultQuery(URL.zap, {sRef : ref}, this.simpleResultCallback.bind(this));
	
		//TODO replace this
		setTimeout(updateItemsLazy, 7000); //reload epg and subservices
		setTimeout(updateItems, 3000);
	},
});

var EpgListHandler = Class.create(AbstractContentHandler,{
	initialize: function($super){
		$super('tplEpgList');
		this.provider = new ServiceEpgListProvider(this.show.bind(this));
		this.window = '';
		this.data = '';
	},
	
	show : function(data){
		this.data = data;
		fetchTpl(this.tpl, this.showEpg.bind(this));		
	},
	
	showEpg: function(){
		var html = templates[this.tpl].process(this.data);

		if (!this.window.closed && this.window.location) {
			setWindowContent(this.window, html);
		} else {
			this.window = openPopup("EPG", html, 900, 500);
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
	
	/**
	 * del
	 * Deletes a movie
	 * Parameters:
	 * @servicereference - the servicereference of the movie that should be deleted
	 * @servicename - the name of the service the movie was recorded from
	 * @title - the title of the movie
	 * @description - the description of the movie
	 */
	del: function(servicereference, servicename, title, description){		
		var result = confirm( "Are you sure want to delete the Movie?\n" +
				"Servicename: " + servicename + "\n" +
				"Title: " + unescape(title) + "\n" + 
				"Description: " + description + "\n");
		
		if(result){
			debug("[MovieListProvider.del] ok confirm panel"); 
			this.provider.simpleResultQuery(URL.moviedelete, {sRef : servicereference}, this.simpleResultCallback.bind(this));			
		}
		else{
			debug("[MovieListProvider.del] cancel confirm panel");
			result = false;
		}
		
		this.refresh = result;
		return result;
	}	
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
	getData: function(tListItem){
		var parent = tListItem.up('.tListItem');
		
		var t = {
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


//create required Instances
var serviceListHandler = new ServiceListHandler('contentServices');
var epgListHandler = new EpgListHandler();
var movieListHandler = new MovieListHandler('contentMain');
var timerListHandler = new TimerListHandler('contentMain');
var timerHandler = new TimerHandler('contentMain');