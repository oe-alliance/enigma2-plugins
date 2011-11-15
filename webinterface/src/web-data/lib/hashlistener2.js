/**
 * Hash Listener 2.0
 *
 * ************************************************************
 * Basic object to allow updating the hash part of the document location.
 * Mozilla always adds an entry to the history but for IE we add an optional
 * flag whether to add an entry to the history and if this is set an iframe is
 * used to support this behavior (this is on by default).
 *
 * When the hash value changes onHashChanged is called. Override this to do
 * your own callbacks.
 *
 * Usage:   Include script
 *          Override onHashChanged: hashListener.onHashChanged = fn
 *
 * Browser Support: FireFox 3, Opera 9+, IE 6+, Chrome, Safari 4
 * * Not tested: Konkeror, old Safari, old Firefox
 *
 * **********************************************************
 * @author Marcelo Eden
 * @coauthor Stephan Reichholf
 * @copyright (c) 2000 - 2009 OS!Schools
 * @license BSD
 * @created 18/03/2009
 * @updated 15/11/2011
 */

var hashListener = {
	browser: null,
	isOk: true,
	hash: "",
	
	/** 
	 * Check hash 
	 */
	check:	function () {
		var h = location.hash;
        if (h != this.hash) {
            this.updateHistory(h);
			this.onHashChanged();
		}
	},
	
	/**
	 * Start Action
	 */
	init:   function () {
		// Check if can go on
		this.loadBrowser();
		if (!this.isOk) {
			return false;
		}
		
		// Self
		var self = this;
		
		// Dynamical Changes
		if ("onpropertychange" in document && "attachEvent" in document) {
			document.attachEvent("onpropertychange", function () {
				if (event.propertyName == "location") {
					self.check();
				}
			});
		}
		
		// poll for changes of the hash
		setInterval(function () { self.check(); }, 150);
        return true;
    },
	
	/**
	 * Set Hash
	 */
	setHash: function (s) {
		location.hash = s;
	},
	
	/**
	 * Get Hash
	 */
	getHash: function () {
		//firefox escapes the hash when we read it, so we have to extract it from location.href ourselves
		var parts = location.href.split("#");
		if(parts.length > 1)
			return parts[1];
		return "";
	},
		
    /** Important!
	 * trigger onHashChanged Event
	 * Need to be overwriten
	 */ 	
	onHashChanged: function () {	},
    
    /* *******************************************
     * CrossBrowser
     * ***************************************** */
	loadBrowser: function () {
		var nav = navigator.userAgent.toLowerCase();
        this.isOk = true;
       
		// IE
		if (/msie/.test(nav)) {
			this.browser = 'ie';
            
            // IE need a frame trick
            this.createFrame();
		} 
		// Firefox
		else if (/firefox/.test(nav)) {
			this.browser = 'firefox';
		}
        // Genko
		else if (/safari/.test(nav)) {
			this.browser = 'gecko';
		}
        // Genko
		else if (/chrome/.test(nav)) {
			this.browser = 'chrome';
		}
        // Genko
		else if (/opera\/9/.test(nav)) {
			this.browser = 'opera9';
		}
        // Genko
		else if (/gecko/.test(nav)) {
			this.browser = 'gecko';
		}
        // Else other Element
        else{
            this.browser = '???';
            this.isOk = false;
        }

        return this.isOk;
	},

    updateHistory: function(h){
        // IE
        if (this.browser == 'ie') {
            this.writeFrame(h);
		}

        // All Browser
        this.hash = h;
    },

    /* *************************************
     * IE Hacks
     * *********************************** */
    createFrame: function () {
        var frame = document.createElement("iframe");
        frame.id = "state-frame";
        frame.style.display = "none";
        document.body.appendChild(frame);
        this.writeFrame( location.hash );
    },

	/** 
	 * Write content to IFrame
	 */
	writeFrame:	function (s) {
		var f = document.getElementById("state-frame");
		var d = f.contentDocument || f.contentWindow.document;
		d.open();
		d.write('<script>window.hash2 = "'+ s +'";window.onload = parent.hashListener.syncFrameHash;</script>');
		d.close();
	},

    /**
	 * Syncronise Document Hash with IFrame Hash
	 */ 
	syncFrameHash:	function () {
		var s = this.hash2;
		if (s != location.hash) {
			location.hash = s;
		}
	}
};
