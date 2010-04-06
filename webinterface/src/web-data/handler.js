/**
 * AbstractContentHandler
 * 
 * Abstract Class for "AbstractContentHandler" Classes 
 * A Content handler is a class that provides content for the webpage 
 * e.g. a list of channels, or a list of recordings and/or is able of
 * doing the handling of all events for that content (e.g. deleting a recording)
 */

var AbstractContentHandler = Class.create({
	/**
	 * initialize
	 * Default constructor
	 * Parameters:
	 * @tpl - Name of the template to use
	 * @url - name of the url to use for requests
	 * @target - target html id for the content
	 * @onFinished - an array of functions that should be called after "this.show()" has finished
	 */
	initialize: function(tpl, url, target, onFinished){
		this.tpl = tpl;
		this.url = url;
		this.target = target;
		this.request = '';
		this.onFinished = onFinished;
		this.ajaxload = false;
		this.parms = {};
		this.refresh = false;
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
	
	//TODO insert renderTpl, processTpl & Co. here or somewhere else... (maybe a separate class?)
	
	/**
	 * getXML
	 * Converts the incoming transport result into a DOM object
	 * Parameters:
	 * @transport - the xmlhttp transport object
	 * 
	 **/
	getXML: function(transport){
		var xmlDoc = "";

		if(window.ActiveXObject){ // we're on IE
			xmlDoc = new ActiveXObject("Microsoft.XMLDOM");
			xmlDoc.async="false";
			xmlDoc.loadXML(transport.responseText);
		} else { //we're not on IE
			if (!window.google || !google.gears){
				xmlDoc = transport.responseXML;
			} else { //no responseXML on gears
				xmlDoc = (new DOMParser()).parseFromString(transport.responseText, "text/xml");
			}
		}

		return xmlDoc;
	},
	
	/**
	 * renderXML
	 * renders the XML and returns what's required by this.show();
	 */
	renderXML: function(xml){
		debug('[AbstractContentHandler] ERROR: renderXML not implemented in derived class!');
		return {};
	},
	
	/**
	 * callback
	 * The default function that is being called for the onSuccess event of this.load();
	 * Parameters:
	 * @transport - the xmlhttp transport object
	 **/
	callback: function(transport){
		var data = this.renderXML(this.getXML(transport));
		this.show(data);
	},
	
	/**
	 * errorback
	 * The default function that is being called for the onError event of this.load();
	 * Parameters
	 * @transport - the xmlhttp transport object
	 */
	errorback: function(transport){
		var notif = "Request failed for:  " + transport.request.url + "<br>Status: " + transport.status + " " + transport.statusText;
		notify(notif, false);
	},
	
	/**
	 * load
	 * Calls this.getURL 
	 * Parameters
	 * @parms - an json object containing  {parameter : value} pairs for the request
	 * @fnc - function to replace this.callback (which is being called @ onSuccess)
	 */
	load: function(parms, fnc){
		// gears or not that's the question here
		this.requestStarted();
		
		this.parms = parms;
		if(fnc !== undefined){
			this.callback = fnc;
		}
		
		this.getUrl(this.url, parms, this.callback.bind(this), this.errorback.bind(this));
	},
	
	/**
	 * getUrl
	 * creates a new Ajax.Request
	 * Parameters:
	 * @url - the url to fetch
	 * @parms - an json object containing  {parameter : value} pairs for the request
	 * @callback - function to call @ onSuccess;
	 * @errorback - function to call @ onError;
	 */
	getUrl: function(url, parms, callback, errorback){
		if (!window.google || !google.gears){ //no gears
			try{
				new Ajax.Request(url,
						{
							parameters: parms,
							asynchronous: true,
							method: 'GET',
							requestHeaders: ['Cache-Control', 'no-cache,no-store', 'Expires', '-1'],
							onException: function(o,e){ throw(e); },				
							onSuccess: function (transport, json) {						
								if(callback !== undefined){
									callback(transport);
								}
							}.bind(this),
							onFailure: function(transport){
								if(errorback !== undefined){
									errorback(transport);
								}
							}.bind(this),
							onComplete: this.requestFinished.bind(this)
						});
			} catch(e) {
				debug('[AbstractContentHandler.getUrl] Exception: '+ e);
			}
		} else { //we're on gears!
			try{
				url = url + "?" + $H(parms).toQueryString();
				
				var request = google.gears.factory.create('beta.httprequest');
				request.open('GET', url);
	
	
				request.onreadystatechange = function(){				
					if(request.readyState == 4){
						if(request.status == 200){
							if( callback !== undefined ){
								callback(request);
							}
						} else {
							this.errorback(request);
						}
					}
				}.bind(this);
				request.send();
			} catch(e) {
				debug('[AbstractContentHandler.getUrl] Exception: '+ e);
			}
		}
	},
	
	registerEvents : function(){
		debug('[AbstractContentHandler] WARNING: registerEvents not implemented in derived class!');
	},
	
	/**
	 * finished
	 * Calls all functions this.onFinished contains PLUS this.registerEvents
	 * Is usually called after this.show() has finished
	 */
	finished : function(){
		
		this.registerEvents();
		
		if(this.onFinished !== undefined){
			for(var i = 0; i < this.onFinished.length; i++){
				var fnc = this.onFinished[i];
				if(typeof(fnc) === 'function'){
					fnc();
				}
			}
		}
	},
	
	/**
	 * show
	 * Show the data that has been fetched by a request (and prepared by renderXML)
	 * in this.target.
	 * Afterwards call this.finished()
	 */
	show : function(data){
		processTpl(this.tpl, data, this.target, this.finished.bind(this));		
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
	 * reload
	 * rexecute this.load() using this.parms and set this.refresh to false
	 * Parameters:
	 * @fnc - function to call @ onSuccess (passed through to this.load() )
	 */	
	reload: function(fnc){
		this.refresh = false;
		this.load(this.parms, fnc);
	},
	
	/**
	 * simpleResultQuery
	 * Call any URL that returns a SimpleXMLResult with this.simpleResultCallback for
	 * @onSuccess
	 * Parameters:
	 * @url - the url to call
	 * @parms - an json object containing  {parameter : value} pairs for the request
	 */
	simpleResultQuery: function(url, parms){
		this.getUrl(url, parms, this.simpleResultCallback.bind(this));		
	},
	
	/**
	 * simpleResultCallback
	 * Callback for @ onSuccess of this.simpleResultQuery()
	 * if this.refresh == true this.reload is being called
	 * Parameters:
	 * @transport - the xmlhttp transport object
	 */
	simpleResultCallback: function(transport){
		var result = this.simpleResultRenderXML(this.getXML(transport));
		this.notify(result.getStateText(), result.getState());
		
		if(this.refresh){
			this.reload();
		}
		
	},
	
	/**
	 * simpleResultRenderXML
	 * Renders the result of this.simpleResultQuery() and returns an SimpleXMLResult object for it
	 * Parameters:
	 * @xml - a DOM object containing the XML to render
	 */
	simpleResultRenderXML: function(xml){
		var result = new SimpleXMLResult(xml);
		return result;
	}

	
});

/**
 * ServiceListHandler
 * ContentHandler for service lists.
 */
var ServiceListHandler = Class.create(AbstractContentHandler, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 * @epgp: Instance of ServiceListEpgProvider to show epgnow/next information
	 * @subsp: Instance of ServiceListSubserviceProvider to show subservices 
	 */
	initialize: function($super, target, epgp, subsp){
		$super('tplServiceList', URL.getservices, 
				target, [this.getNowNext.bind(this),this.getSubservices.bind(this)] );
		
		this.epgProvider = epgp;
		this.subServiceProvider = subsp;
		this.ajaxload = true;
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentHandler
	 */
	renderXML: function(xml){
		var list = new ServiceList(xml).getArray();
		return {services : list};	
	},
	
	/**
	 * getNowNext
	 * calls this.epgProvider.getNowNext to show Now/Next epg information
	 * using this.parms.sRef as the servicereference of the bouquet 
	 */
	getNowNext: function(){
		this.epgProvider.getNowNext({bRef : this.parms.sRef});
	},
	
	/**
	 * getSubservices
	 * calls this.subServiceProvider.load() to show Now/Next epg information
	 */
	getSubservices: function(){
		this.subServiceProvider.load({});
	},
	
	
	registerEvents : function(){
		var parent = $(this.target);
		
		parent.on(
				'click', 
				'a.sListSLink', 
				function(event, element){
					this.zap(unescape(element.id));
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
		
		
	},
	
	/**
	 * call this to switch to a service
	 * Parameters:
	 * @servicereference - the (unescaped) reference to the service that should be shown
	 */
	zap: function(ref){
		this.simpleResultQuery(URL.zap, {sRef : ref});
	
		//TODO replace this
		setTimeout(updateItemsLazy, 7000); //reload epg and subservices
		setTimeout(updateItems, 3000);
	}
});

/**
 * ServiceListEpgProvider
 * Handles EPG now/next for a ServiceListHandler
 */
var ServiceListEpgProvider = Class.create(AbstractContentHandler, {
	//Constants
	NOW : 'NOW',
	NEXT : 'NEXT',
	
	/**
	 * initialize
	 * See the description in AbstractContentHandler
	 */	
	initialize: function($super){
		$super('tplServiceListEPGItem', URL.epgnow);
		this.type = this.NOW;
		this.url = URL.epgnow;
	},

	/**
	 * renderXML
	 * See the description in AbstractContentHandler
	 */
	renderXML: function(xml){
		var list = new EPGList(xml).getArray();
		return list;
	},
	
	/**
	 * show
	 * calls this.showItem for each item of @list
	 * @list - An array of EPGEvents
	 */
	show: function(list){
		for(var i = 0; i < list.length; i++){
			this.showItem(list[i]);
		}
		
		this.finished();
	},
	
	/**
	 * showItem
	 * Shows an EPGEvent item in the DOM
	 * templates.tplServiceListEPGItem needs to be present!
	 * Parameters:
	 * @item - The EPGEvent object
	 */
	showItem: function(item){
		if(item.eventid != ''){
			var data = { epg : item, nownext: this.type };
			var id = this.type + item.servicereference;
	
			if(templates.tplServiceListEPGItem !== undefined){
				//TODO move templates.* maybe?!?
				renderTpl(templates.tplServiceListEPGItem, data, id, true);
			} else {
				debug("[ServiceListEpgProvider.showItem] tplServiceListEPGItem N/A");
			}
			
			var element = $('tr' + id);
			if(element !== null){
				element.show();
			}
		}
	},
	
	/**
	 * callback
	 * custom callback
	 * Parameters:
	 * @transport - xmlhttp transport object
	 */
	callback: function(transport){
		var data = this.renderXML(this.getXML(transport));
		this.show(data);
		if(this.callbackType !== undefined){
			this.get(this.callbackType);
		}
	},	
	
	/**
	 * getNowNext
	 * call this.get to show epg-now and epg-next
	 * Parameters:
	 * @parms - an json object containing  {parameter : value} pairs for the request
	 */
	getNowNext: function(parms){
		this.parms = parms;
		this.get(this.NOW, this.NEXT);		
	},
	
	/**
	 * get
	 * Load epg information for type and - if set - callbackType 
	 * (ServiceListEpgProvider.NOW or ServiceListEpgProvider.NEXT)
	 * Parameters:
	 * @type - ServiceListEpgProvider.NOW or ServiceListEpgProvider.NEXT
	 * @callbackType - ServiceListEpgProvider.NOW or ServiceListEpgProvider.NEXT
	 */
	get: function(type, callbackType){		
		this.type = type;
		//just in case... don't do it twice...
		if(type != callbackType){
			this.callbackType = callbackType;
		}
		
		switch(this.type){
			case this.NOW:
				this.url = URL.epgnow;
				break;
			case this.NEXT:
				this.url = URL.epgnext;
				break;
		}
		
		this.load(this.parms);
	}	
});

/**
 * ServiceListSubserviceProvider
 * Handles EPG now/next for a ServiceListHandler
 */
var ServiceListSubserviceProvider = Class.create(AbstractContentHandler, {
	//constants
	PREFIX : 'SUB',

	/**
	 * initialize
	 * See the description in AbstractContentHandler
	 */		
	initialize: function($super){
		$super('tplSubServices', URL.subservices);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentHandler
	 */		
	renderXML: function(xml){
		var list = new ServiceList(xml).getArray();
		return list;
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
			processTpl(this.tpl, data, id);			
			parent.show();
		}
	}
});

/**
 * MovieListHandler
 * Handles a list of movies including deleting actions
 */
var MovieListHandler = Class.create(AbstractContentHandler, {		
	/**
	 * initialize
	 * See the description in AbstractContentHandler
	 */
	initialize: function($super, target){
		$super('tplMovieList', URL.movielist, target );
		
		this.ajaxload = true;
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentHandler
	 */	
	renderXML: function(xml){
		var list = new MovieList(xml).getArray();
		return {movies : list};
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
			debug("[MovieListHandler.del] ok confirm panel"); 
			this.simpleResultQuery(URL.moviedelete, {sRef : servicereference});			
		}
		else{
			debug("[MovieListHandler.del] cancel confirm panel");
			result = false;
		}
		
		this.refresh = result;
		return result;
	}	
});

var TimerListHandler = Class.create(AbstractContentHandler, {
	/**
	 * initialize
	 * See the description in AbstractContentHandler
	 */
	initialize: function($super, target){
		$super('tplTimerList', URL.timerlist, target );
		
		this.ajaxload = true;
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentHandler
	 */	
	renderXML: function(xml){
		var list = new TimerList(xml).getArray();
		return {timer : list};
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
	 * See the description in AbstractContentHandler
	 */
	initialize: function($super, target){
		$super('tplTimerEdit', URL.timerlist, target );
		
		this.ajaxload = true;
	},
	
	/**
	 * @override
	 * load
	 * When handling timers the whole loading-sequence is entirely off-standard.
	 * Most of the data is already there or has to be created.
	 * 
	 * Parameters:
	 * @element - the html element calling the load function ( onclick="TimerHandler.load(this)" )
	 */
	load : function(element){
		var parent = element.up('.tListItem');
		
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

			
		var begin = new Date(t.begin * 1000);
		var end = new Date(t.end * 1000);
		
		var bHours = this.numericalOptionList(1, 24, begin.getHours());		
		var bMinutes = this.numericalOptionList(1, 60, begin.getMinutes());
		var eHours = this.numericalOptionList(1, 24, end.getHours());		
		var eMinutes = this.numericalOptionList(1, 60, end.getMinutes());
		
		var now = new Date();
		var years = this.numericalOptionList(now.getFullYear(), now.getFullYear() + 10, begin.getFullYear());
		
		var actions = this.ACTIONS;
		actions[t.justplay].selected = this.SELECTED;
		
		var afterevents = this.AFTEREVENTS;
		afterevents[t.afterevent].selected = this.SELECTED;
		
		var repeated = this.repeatedDaysList(t.repeated);
		
		var data = { 
				year : years,
				month : [],
				day : [],
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
	numericalOptionList: function(lowerBound, upperBound, selectedValue){
		var list = [];
		var idx = 0;
		
		for(var i = lowerBound; i <= upperBound; i++){
			var txt = i < 10 ? "0" + i : i;
			var selected = "";
			if(i == selectedValue){
				selected = this.SELECTED;
			}
			list[idx] = {value : i, txt : txt, selected : selected};
			idx++;
		}
		return list;
	},
	
	
	commitForm : function(form){
		values = $F(form).serializeElements();
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentHandler
	 */	
	renderXML: function(xml){
		var list = new TimerList(xml).getArray();
		return {timer : list};
	}
});


//create required Instances
var serviceListHandler = new ServiceListHandler('contentServices',  new ServiceListEpgProvider(), new ServiceListSubserviceProvider());
var movieListHandler = new MovieListHandler('contentMain');
var timerListHandler = new TimerListHandler('contentMain');
var timerHandler = new TimerHandler('contentMain');