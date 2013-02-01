// admin.js by emanuel 2012

/**
 * PkgConfs Controller
 * 
 */
var PkgConfs = Class.create(Controller, {
	initialize: function($super, listTarget){
		$super(new PkgConfListHandler(listTarget));
	},

	loadSettings: function(){
		setContentHd('Settings');
		this.handler.load();
	},
});

/**
 * Scripts Controller
 * 
 */
var Scripts = Class.create(Controller, {
	initialize: function($super, listTarget){
		$super(new ScriptListHandler(listTarget));
	},

	loadScripts: function(){
		setContentHd('User Scripts');
		this.handler.load();
	},
});

/**
 * Pkg Controller
 * 
 */

var Pkgs = Class.create(Controller, {
	initialize: function($super, listTarget, navTarget){
		$super(new PkgListHandler(listTarget));
		this.navHandler = new PkgNavHandler(navTarget);
	},

	loadAll: function(){
		setContentHd('Packages (ipk) - all');
		this.handler.loadAll();
		this.addFilterInput();
	},

	loadInstalled: function(){
		setContentHd('Packages (ipk) - installed');
		this.handler.loadInstalled();
		this.addFilterInput();
	},

	loadUpgradable: function(){
		setContentHd('Packages (ipk) - upgradable');
		this.handler.loadUpgradable();
		this.addFilterInput();
	},

	loadNav: function(){
		setNavHd('WebAdmin');
		this.navHandler.load();
	},
						
	onFilterFocus: function (event){
		event.element().value = '';
	},

	filter: function (event){
		var needle = event.element().value;
		if (event.keyCode == Event.KEY_RETURN) {
			setContentHd('Packages (ipk) - Filter: \''+ needle +'\'');
			window.location.href = '/webadmin/#!/ipk/search?filter=' + needle.replace(' ', '%20');
		};
	},

	addFilterInput: function(){
		var input = new Element('input');
		input.id = 'pkgFilter';
		input.value = 'Filter Packages';
		$('contentHdExt').update(input);
		input.on('focus', this.onFilterFocus.bind(this));
		input.on('keyup', this.filter.bind(this));
	},
	
	search: function (needle){
		setContentHd('Packages (ipk) - Filter: \''+ unescape(needle) +'\'');
		window.location.href = '/webadmin/#!/ipk/search?filter=' + needle.replace(' ', '%20');
		this.handler.loadFilter(needle);
		this.addFilterInput();
	},
		
});

/**
 * SettingPage Class
 * 
 */

var SimpleWebAdminPages = Class.create({
	PAGE_TERMINAL: 'tplTerminal',

	initialize: function(target){
		this.simpleHandler = new SimplePageHandler(target);
	},

	show: function(tpl, data){
		if(!data)
			data = {};
		this.simpleHandler.show(tpl, data);
	},
					   
	loadTerminal: function(){
		setContentHd('Terminal');
		var data = { 'host' : document.location.host }
		this.show(this.PAGE_TERMINAL, data);
	}
});

/**
 * WebAdmin Core Class
 * 
 */
var WebAdminCore = Class.create(E2WebCore, {
	initialize: function(){
		this.mode = "";
		this.subMode = "";
		this.bouquets = new Bouquets('contentBouquets', 'contentMain');
		this.current = new Current('currentContent', 'volContent');
		this.volume = new Volume('volContent');
		this.pkgs = new Pkgs('contentMain', 'navContent');
		this.settings = new PkgConfs('contentMain');
		this.scripts = new Scripts('contentMain');
		this.epg = new EPG(new EpgListHandler());
		this.power = new Power();
		this.switchfeed = new SwitchFeedHandler();
		this.memory = new MemoryHandler();
		this.simples = new SimpleWebAdminPages('contentMain');
		this.sessionProvider = new SessionProvider( this.onSessionAvailable.bind(this) );

		//create required Instances
		this.navlut = {
			'ipk': {
				'all' : this.pkgs.loadAll.bind(this.pkgs),
				'installed' : this.pkgs.loadInstalled.bind(this.pkgs),
				'upgradable' : this.pkgs.loadUpgradable.bind(this.pkgs),
				'settings' : this.settings.loadSettings.bind(this.settings),
				'search' : this.searchPkg.bind(this),
				'scripts' : this.scripts.loadScripts.bind(this.scripts),
				'term' : this.simples.loadTerminal.bind(this.simples)
			}
		};
	},

	searchPkg: function(){
		var needle = hashListener.getHash().replace(/.+filter\=/,'');
		if(needle != '')
			this.pkgs.search(needle);
	},
	
	getMem: function(){
		this.memory.getMem();
	},

	switchFeed: function(file){
		this.switchfeed.load('/webadmin/web/feedonline', {'file' : file});
	},

	onHashChanged: function(isReload){
		var hash = hashListener.getHash();
		var parts = hash.split("/");

		var len = parts.length;
		debug('[onHashChanged:hash]' + hash);
		debug('[onHashChanged:parts]' + parts);
		debug('[onHashChanged:len]' + len);
		if(len >= 2){
			var mode = parts[1];
			if(mode != this.mode || isReload || ( len <= 2 && this.subMode != '') ){
				this.switchMode(mode, len == 2);
				this.subMode = '';
			}
			this.mode = mode;
			if(len > 2){
				var subMode = parts[2];
				if(subMode != this.subMode || isReload){
					this.subMode = subMode.replace(/\?.+/,'');
					if(!this.navlut[this.mode][this.subMode]){
						return;
					} else {
						//if(this.mode != 'installed')
						this.navlut[this.mode][this.subMode]();
					}
				}
				if(len > 3){
					switch(this.mode){
					case 'ipk':
						event.stop();
						break;
					default:
						return;
					}
				}
				debug("[onHashChanged:this.mode"+this.mode);
				debug("[onHashChanged:subMode"+subMode)
			}
		}
	},

	getBaseHash: function(){
		var hash = ['#!', this.mode].join("/");
		if(this.subMode != ''){
			hash = [hash, this.subMode].join("/");
		}
		debug("[getBaseHash:hash] "+hash);
		return hash;
	},

	loadDefault: function(){
		debug("[WebAdminCore].loadDefault");
		window.location.href='/webadmin/#!/ipk/installed';
	},

	run: function(){
		debug("[WebAdminCore].run");
		this.sessionProvider.load({});
	},

	onSessionAvailable: function(sid){
		debug("[WebAdminCore].onSessionAvailable, " + sid)
		global_sessionid = sid;

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
		
		this.getMem();
		this.registerEvents();

		templateEngine.fetch('tplCurrent');
		if(!hashListener.getHash().length >= 1){
			this.loadDefault();
		}

		this.updateItems();
		this.startUpdateCurrentPoller();
	},

	registerEvents: function(){
		debug("[WebAdminCore].registerEvents");
		//Hash-Reload-Fix
		//HACK :: THIS IS EVIL VOODOO, DON'T TRY THIS AT HOME! => I HAD TO TOOK THAT EVIL, I HAD HAVE NEEDED ;-)
		document.on(
			'click',
			'a',
			function(event, element){
				var parts = element.href.split('#');
				var curHost = window.location.href.split('#')[0];
				debug("parts, curHost "+parts+ " "+curHost);
				//Don't do this crazy stuff when the target is another host!
				if(curHost == parts[0]){
					debug("curHost == parts[0]"+parts[0]+ " "+curHost);
					if (parts.length > 1){
						if(parts[1] != ''){
							if(window.location == element.href){
								this.onHashChanged(true);
								debug("[if window.location == element.href]" + window.location);
								return;
							}else{
								window.location == element.href;
								debug("[else window.location element.href]" +  window.location + " " + element.href);
								return;
							}
						} else {
							debug("[parts[1] != ''else-> element.href window.location]" + element.href + " " + window.location);
							element.href = window.location;
						}
						debug("[parts.length > 1, return false;");
						return false;
					}
				}
			}.bind(this)
		);
		//Header
		$('openSignalPanel').on(
			'click',
			function(event, element){
				this.signal.load();
				event.stop();
			}.bind(this)
		);
		$('instantRecord').on(
			'click',
			function(event, element){
				var menu = $('instantRecordMenu');
				if(menu.visible()){
					menu.hide();
				} else {
					menu.show();
				}
				event.stop();
			}
		);
		document.on(
			'click',
			'.doInstantRecord',
			function(event, element){
				var menu = $('instantRecordMenu');
				this.timers.recordNow(
					element.readAttribute('data-type'),
					function(result){
						menu.hide();
					}
				);
			}.bind(this)
		);
		//Current
		$('current').on(
			'click',
			'.currentExtShowHide',
			function(event, element){
				this.current.toggleVisibility(element);
				event.stop();
			}.bind(this)
		);
		$('current').on(
				'click',
				'.currentEpg',
				function(event, element){
					var ref = unescape( element.readAttribute('data-servicereference') );
					this.epg.load(ref);
					event.stop();
				}.bind(this)
			);
		//EPG-Search
		$('epgSearchForm').on(
			'submit',
			function(event, element){
				this.epg.search($F('epgSearch'));
				event.stop();
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
					return false;
				}.bind(this)
		);
		//Volume
		$('navVolume').on(
			'click',
			'a.volume',
			function(event, element){
				this.volume.set(element.readAttribute('data-volume'));
				event.stop();
				return false;
				
			}.bind(this)
		);
		//WebTv
		$('webTv').on(
			'click',
			function(event, element){
				window.open('/web-data/tpl/default/streaminterface/index.html', 'WebTV', 'scrollbars=no, width=800, height=740');
				event.stop();
			}.bind(this)
		);
		//Content
		var content = $('contentMain');
		//Pkglist
		content.on(
			'click',
			'a.sPkgInstallSLink',
			function(event, element){
				var pkgname = element.readAttribute('data-pkgname');
				var check = confirm("Install "+pkgname+"?");
				if(check == true) 
					window.open('pkg?command=install&package='+pkgname);
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'a.sPkgRemoveSLink',
			function(event, element){
				var pkgname = element.readAttribute('data-pkgname');
				var check = confirm("Remove "+pkgname+"?");
				if(check == true) 
					window.open('pkg?command=remove&package='+pkgname);
				event.stop();
			}.bind(this)
		);
		content.on(
			'click',
			'a.sPkgConfsLinkExt',
			function(event, element){
				var target = element.up('.sPkgConfItem').down('.trExtPkgConf');
				if(target){
					var bullet = element.down('.sPkgConfBulletToggle');
					if(target.visible()){
						target.hide();
						bullet.src = "/web-data/img/toggle_expand.png";
						bullet.alt = "+";
					} else {
						target.show();
						bullet.src = "/web-data/img/toggle_collapse.png";
						bullet.alt = "-";
					}
				}
				event.stop();
			}.bind(this)
		);
		
		content.on(
			'click',
			'a.sPkgConfFeedsLink',
			function(event, element){
				this.switchFeed(element.getAttribute("data-name"));
				event.stop();
			}.bind(this)
		);
		
	},

	switchMode: function(mode, initContent){
		if(initContent){
			this.setEmptyContent('contentMain', 'please select a submenu on the left...');
			setContentHd('...');
		}

		switch(mode){
		case "ipk":
			debug('[switchMode] mod=ipk');
			this.pkgs.loadNav();
			break;
			
		case "settings":
			window.location.href='/webadmin/#!/ipk/settings';
			break;
			
		default:
			break;
		}
	}

});

var admincore = new WebAdminCore();
