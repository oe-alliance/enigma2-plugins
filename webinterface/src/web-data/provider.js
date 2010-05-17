/**
 * AbstractContentProvider
 * 
 * Abstract Class for "AbstractContentProvider" Classes 
 * A Content handler is a class that provides content for the webpage 
 * e.g. a list of channels, or a list of recordings and/or is able of
 * doing the handling of all events for that content (e.g. deleting a recording)
 */

var AbstractContentProvider = Class.create({
	/**
	 * initialize
	 * Default constructor
	 * Parameters:
	 * @tpl - Name of the template to use
	 * @url - name of the url to use for requests
	 * @target - target html id for the content
	 * @onFinished - an array of functions that should be called after "this.show()" has finished
	 */
	initialize: function(url, showFnc, onFinished){
		this.url = url;
		this.request = '';
		this.onFinished = onFinished;
		this.show = showFnc;
		this.parms = {};
		this.refresh = false;
		this.eventsRegistered = false;
	},
		
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
		debug('[AbstractContentProvider] ERROR: renderXML not implemented in derived class!');
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
							}.bind(this)
//							onComplete: this.requestFinished.bind(this)
						});
			} catch(e) {
				debug('[AbstractContentProvider.getUrl] Exception: '+ e);
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
				debug('[AbstractContentProvider.getUrl] Exception: '+ e);
			}
		}
	},
	
	registerEvents : function(){
		debug('[AbstractContentProvider] WARNING: registerEvents not implemented in derived class!');
	},
	
	/**
	 * finished
	 * Calls all functions this.onFinished contains this.registerEvents
	 * Is usually called after this.show() has finished
	 */
	finished : function(){
		if(!this.eventsRegistered){
			this.registerEvents();
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
	simpleResultQuery: function(url, parms, callback){
		this.getUrl(url, parms, callback);		
	},
	
	/**
	 * simpleResultCallback
	 * Callback for @ onSuccess of this.simpleResultQuery()
	 * if this.refresh == true this.reload is being called
	 * Parameters:
	 * @transport - the xmlhttp transport object
	 */
	simpleResultCallback: function(transport, callback){
		var result = this.simpleResultRenderXML(this.getXML(transport));
		if(typeof(callback) == "function"){
			callback(result);
		}
		
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
 * ServiceListProvider
 * ContentHandler for service lists.
 */
var ServiceListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 * @epgp: Instance of ServiceListEpgProvider to show epgnow/next information
	 * @subsp: Instance of ServiceListSubserviceProvider to show subservices 
	 */
	initialize: function($super, showFnc, epgp, subsp){
		$super(URL.getservices, showFnc );
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new ServiceList(xml).getArray();
		return {services : list};	
	}
});

/**
 * ServiceListEpgProvider
 * Handles EPG now/next for a ServiceListProvider
 */
var ServiceListEpgProvider = Class.create(AbstractContentProvider, {
	//Constants
	NOW : 'NOW',
	NEXT : 'NEXT',
	
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */	
	initialize: function($super, showFnc){
		$super(URL.epgnow, showFnc);
		this.type = this.NOW;
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new EPGList(xml).getArray();
		return list;
	},
	
	/**
	 * callback
	 * custom callback
	 * Parameters:
	 * @transport - xmlhttp transport object
	 */
	callback: function(transport){
		var data = this.renderXML(this.getXML(transport));
		this.show(data, this.type);
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
 * Handles EPG now/next for a ServiceListProvider
 */
var ServiceListSubserviceProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */		
	initialize: function($super, showFnc){
		$super(URL.subservices, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */		
	renderXML: function(xml){
		var list = new ServiceList(xml).getArray();
		return list;
	}
});

/**
 * MovieListProvider
 * Handles a list of movies including deleting actions
 */
var MovieListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super(URL.movielist, showFnc);		
	},
	
	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */	
	renderXML: function(xml){
		var list = new MovieList(xml).getArray();
		return {movies : list};
	}
});

var TimerListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super(URL.timerlist, showFnc);
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