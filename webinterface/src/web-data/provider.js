/**
 * AbstractContentProvider
 *
 * Abstract Class for "AbstractContentProvider" Classes
 * A Content handler is a class that provides content for the webpage
 * e.g. a list of channels, or a list of recordings and/or is able of
 * doing the handling of all events for that content (e.g. deleting a recording)
 */

var AbstractContentProvider = Class.create(AjaxThing, {
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
		core.notify(notif, false);
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
			callback = fnc;
		} else {
			callback = this.callback.bind(this);
		}

		this.getUrl(this.url, parms, callback, this.errorback.bind(this));
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
 * Content provider for service lists.
 */
var ServiceListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 */
	initialize: function($super, showFnc){
		$super(URL.epgnownext, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new EPGListNowNext(xml).getArray();
		return {items : list};
	}
});

/**
 * SimpleServiceListProvider
 * Content provider for service lists wihtout epg (e.g. bouquets).
 */
var SimpleServiceListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 */
	initialize: function($super, showFnc){
		$super(URL.getservices, showFnc);
	},
	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new ServiceList(xml).getArray();
		return {services : list, hash : core.getBaseHash()};
	}
});

/**
 * Current
 * Content provider for current state
 */
var CurrentProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 */
	initialize: function($super, showFnc){
		$super(URL.getcurrent, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var epg = new EPGList(xml).getArray()[0];
		var service = new Service(xml).toJSON();
		var volume = new Vol(xml).toJSON();

		var data = {
					'current' : epg,
					'service' : service,
					'volume' : volume
				};
		return data;
	}
});

var DeviceInfoProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.deviceinfo, showFnc);
	},

	renderXML: function(xml){
		var data = new DeviceInfo(xml);
		return data;
	}
});

var ExternalsProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.external, showFnc);
	},

	renderXML: function(xml){
		var ext = new ExternalList(xml);
		var data = {
				'externals' : ext.getArray(),
				'anyGui' : ext.anyGui
			};
		return data;
	}
});

var MultiEpgProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.epgmulti, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new MultiEPGList(xml).getArray();
		return {items : list};
	}
});


var LocationProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.getlocations, showFnc);
	},

	renderXML: function(xml){
		var data = new SimpleXMLList(xml, 'e2location');
		return data;
	}
});

var CurrentLocationProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.getcurrlocation, showFnc);
	},

	renderXML: function(xml){
		var data = new SimpleXMLList(xml, 'e2location').getList()[0];
		return data;
	}
});

var MediaPlayerProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.mediaplayerlist, showFnc);
	},

	renderXML: function(xml){
		var files = new FileList(xml).getArray();
		debug("[MediaPlayerProvider].renderXML :: " + files.length + " entries in mediaplayer filelist");

		var mp = { 'hasparent' : false};

		var root = files[0].getRoot();
		if (root != "playlist" && root != '') {
			mp = {
					'root': root,
					'hasparent' : false
			};
			if(root != '/') {
				var re = new RegExp(/(.*)\/(.*)\/$/);
				re.exec(root);
				var newroot = RegExp.$1+'/';
				if(newroot == '//') {
					newroot = '/';
				}
				mp = {
						'hasparent' : true,
						'root': root,
						'servicereference': encodeURIComponent(newroot),
						'name': '..'
				};
				files.shift();
			}
		}

		var items = Array();
		files.each(function(file){
			if(file.getNameOnly() == '') {
				return;
			}

			var isdir = true;

			if (file.getIsDirectory() == "False") {
				isdir = false;
			}

			items.push({
					'isdir' : isdir,
					'servicereference': encodeURIComponent(file.getServiceReference()),
					'root': file.getRoot(),
					'name': file.getNameOnly()
			});
		});

		var data = {
			'mp' : mp,
			'items': items
		};

		return data;

	}


});

var PowerstateProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.powerstate, showFnc);
	},

	renderXML: function(xml){
		var data = new Powerstate(xml).isStandby();
		return data;
	}
});

var TagProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.gettags, showFnc);
	},

	renderXML: function(xml){
		var data = new SimpleXMLList(xml, 'e2tag');
		return data;
	}
});

var ServiceEpgListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 */
	initialize: function($super, showFnc){
		$super(URL.epgservice, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new EPGList(xml).getArray();
		return {epg : list};
	},

	search: function(parms, fnc){
		this.parms = parms;
		if(fnc !== undefined){
			this.callback = fnc;
		}
		this.getUrl(URL.epgsearch, parms, this.callback.bind(this), this.errorback.bind(this));
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

/* this one is a little special! */
var ScreenshotProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.grab, showFnc);
		this.src = "";
	},

	load: function(parms, fnc){
		this.parms = parms;
		if(fnc !== undefined){
			this.callback = fnc;
		}
		var src = this.url + '?' + $H(parms).toQueryString()
		this.callback(src);
	},

	callback: function(src){
		var data = { img : { 'src' : src } };
		this.show(data);
	}
});

var SignalProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.signal, showFnc);
	},

	renderXML: function(xml){
		var signal = new Signal(xml).toJSON();
		return {'signal' : signal};
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

var SimpleRequestProvider = Class.create(AbstractContentProvider,{});

/**
 * Volume
 * Content provider for Volume setting/getting
 */
var VolumeProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * Parameters:
	 * @target: the html target id
	 */
	initialize: function($super, showFnc){
		$super(URL.volume, showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var vol = new Vol(xml).toJSON();
		var data = { 'volume' : vol};
		return data;
	}
});
