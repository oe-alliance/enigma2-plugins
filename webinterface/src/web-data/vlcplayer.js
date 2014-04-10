var VlcBouquetListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('streaminterface/tplBouquetList', target);
		this.provider = new SimpleServiceListProvider(this.show.bind(this));
	}
});

var VlcServiceListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target, zapCallback){
		$super('streaminterface/tplServiceList', target, [this.getSubservices.bind(this)]);
		this.zapCallback = zapCallback;
		this.provider = new ServiceListProvider(this.show.bind(this));
//		this.subServiceHandler = new ServiceListSubserviceHandler();
	},

	/**
	 * getSubservices
	 * calls this.subServiceHandler.load() to show Now/Next epg information
	 */
	getSubservices: function(){
//		this.subServiceHandler.load({});
	},

	/**
	 * call this to switch to a service
	 * Parameters:
	 * @servicereference - the (unescaped) reference to the service that should be shown
	 */
	zap: function(parms){
		this.provider.simpleResultQuery(URL.zap, parms, this.simpleResultCallback.bind(this));
	},

	showSimpleResult: function($super, result){
		if(result.getState()){
			if(this.zapCallback)
				this.zapCallback();
			core.updateItemsLazy();
		}
		$super(result);
	}
});

var WebTv = Class.create(BaseCore, {
	initialize: function($super, vlcObjectTarget){
		$super();
		this.target = vlcObjectTarget;
		this.instance = null;
		this.bouquetHandler = new VlcBouquetListHandler('bouquetList');
		this.serviceHandler = new VlcServiceListHandler('serviceList', this.setStreamTarget.bind(this));
		this.bouquetHandler.onFinished.push(this.onLoadBouquetFinished.bind(this));
		this.sessionProvider = new SessionProvider( this.onSessionAvailable.bind(this) );
	},

	onSessionAvailable: function($super, sid){
		debug("[WebTv].onSessionAvailable, " + sid);
		$super(sid);
		this.instance = $(this.target);

		try {
			$('vlcVolume').update(this.instance.audio.volume);
		} catch (e) {
			debug('[WebTv].run Error on initializing WebTv');
		}
		this.registerEvents();
		this.bouquetHandler.load({'bRef' : bouquetsTv});
	},

	onLoadBouquetFinished: function(){
		var bref = decodeURIComponent( this.bouquetHandler.data.services[0].servicereference );
		this.serviceHandler.load({'bRef' : bref});
	},

	registerEvents: function(){
		$('bouquetList').on(
			'change',
			'.bouquets',
			function(event, element){
				var bref = decodeURIComponent ( $('bouquets').options[$('bouquets').selectedIndex].id );
				this.serviceHandler.load({ 'bRef' : bref });
			}.bind(this)
		);

		$('deinterlace').on(
			'change',
			function(event, element){
				this.setDeinterlace(element);
			}.bind(this)
		);

		$('serviceList').on(
			'change',
			'.services',
			function(event, element){
				this.onServiceChanged();
			}.bind(this)
		);

		var buttons = $('vlcButtons');
		buttons.on(
			'click',
			'.vlcPrev',
			function(event, element){
				this.prev();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcPlay',
			function(event, element){
				this.play();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcNext',
			function(event, element){
				this.next();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcStop',
			function(event, element){
				this.stop();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcFullscreen',
			function(event, element){
				this.fullscreen();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcTeletext',
			function(event, element){
				this.teletext();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcVolumeDown',
			function(event, element){
				this.volumeDown();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcVolumeUp',
			function(event, element){
				this.volumeUp();
			}.bind(this)
		);
		buttons.on(
			'click',
			'.vlcToggleMute',
			function(event, element){
				this.toggleMute();
			}.bind(this)
		);
	},

	onServiceChanged: function(){
		if($('vlcZap').checked){
			var sref = decodeURIComponent ( $('services').options[$('services').selectedIndex].id );
			this.serviceHandler.zap({'sRef': sref});
		} else {
			this.setStreamTarget();
		}
		this.setDeinterlace($('deinterlace'));
	},

	setDeinterlace: function(element){
		var modes = ["blend", "bob", "discard", "linear", "mean", "x", "yadif", "yadif2x"];
		var value = element.value;
		if(value != "off" && modes.indexOf(value) >= 0){
			this.instance.video.deinterlace.enable(value);
		} else {
			this.instance.video.deinterlace.disable();
		}
	},

	play: function() {
		try {
			this.onServiceChanged();
		} catch (e) {
			notify("Nothing to play", false);
		}
	},

	prev: function() {
		if ($('services').selectedIndex > 0) {
			$('services').selectedIndex -= 1;
			this.onServiceChanged();
		}
	},

	next: function() {
		if ($('services').selectedIndex < $('services').length - 1) {
			$('services').selectedIndex += 1;
			this.onServiceChanged();
		}
	},

	pause: function() {
		this.instance.playlist.togglePause();
	},

	stop: function() {
		try {
			this.instance.playlist.stop();
		} catch (e) {
			notify("Nothing to stop", false);
		}
	},

	volumeUp: function() {
		if (this.instance.audio.volume < 200) {
			if (this.instance.audio.volume + 10 > 200) {
				this.instance.audio.volume = 200;
			} else {
				this.instance.audio.volume += 10;
			}
		}

		$('vlcVolume').update(this.instance.audio.volume);
	},

	volumeDown: function() {
		if (this.instance.audio.volume > 0) {
			if (this.instance.audio.volume < 10) {
				this.instance.audio.volume = 0;
			} else {
				this.instance.audio.volume -= 10;
			}
		}

		$('vlcVolume').update(this.instance.audio.volume);
	},

	toggleMute: function() {
		this.instance.audio.mute = !this.instance.audio.mute;
		if (this.instance.audio.mute) {
			$('vlcVolume').update('Muted');
		} else {
			$('vlcVolume').update(this.instance.audio.volume);
		}
	},

	fullscreen: function() {
		if (this.instance.playlist.isPlaying) {
			if (this.instance.input.hasVout) {
				this.instance.video.fullscreen = true;
				return;
			}
		}

		notify("Cannot enable fullscreen mode when no Video is being played!",
				false);
	},

	teletext: function() {
		try {
			this.instance.video.teletext = 100;
		} catch (e) {
			debug("Error - Could not set teletext");
		}
		debug("Current Teletext Page:" + this.instance.video.teletext);
	},

	playUrl: function(url) {
		current = this.instance.playlist.add(url);
		this.instance.playlist.playItem(current);
		$('vlcVolume').update(this.instance.audio.volume);
	},

	setStreamTarget: function() {
		var sref = decodeURIComponent (  $('services').options[$('services').selectedIndex].id );
		host = top.location.host;
		url = 'http://' + host + ':8001/' + decodeURIComponent(sref);

		debug("setStreamTarget " + url);
		this.instance.playlist.clear();
		this.playUrl(url);
	},

	notify: function(text, state){
		debug("[E2WebCore].notify");
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
			notif.fadeIn({'delay' : 500, 'to' : 90});
			var _this = this;
			this.hideNotifierTimeout = setTimeout(_this.hideNotifier.bind(this), 5000);
		}
	},

	getBaseHash: function(){
		return '#';
	}
});

core = new WebTv('vlc');