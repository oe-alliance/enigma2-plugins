var AbstractAdminContentHandler = Class.create(AbstractContentHandler,  {
	show: function(data){
		this.data = data;
		adminTemplateEngine.process(this.tpl, data, this.target, this.finished.bind(this));
	}
});

/**
 * PkgNavHandler
 */
var ScriptListHandler  = Class.create(AbstractAdminContentHandler, {
	initialize: function($super, target){
		$super('tplScriptList', target);
		this.provider = new ScriptListProvider(this.show.bind(this));
		this.ajaxload = true;
	}
});

/**
 * PkgNavHandler
 */
var PkgConfListHandler  = Class.create(AbstractAdminContentHandler, {
	initialize: function($super, target){
		$super('tplPkgSettings', target);
		this.provider = new PkgConfListProvider(this.show.bind(this));
		this.ajaxload = true;
	}
});

/**
 * PkgListHandler
 */
var PkgListHandler  = Class.create(AbstractAdminContentHandler, {
	initialize: function($super, target){
		$super('tplPkgList', target);
		this.provider = new PkgListProvider(this.show.bind(this));
		this.ajaxload = true;
		this.fakeprovider = new PkgFakeProvider(this.show.bind(this));
	},
								   
	loadPkg: function(sel, needle){
		this.provider.setSelection(sel, needle);
		if (this.provider.packages.length != 0) {
			this.requestStarted();
			this.fakeprovider.setList(this.provider.getSelected());
			this.fakeprovider.load();
		}
		else
			this.load();
		
	},
								   
	loadAll: function(){
		this.loadPkg(this.provider.ALL);
	},
								   
	loadUpgradable: function(){
		this.loadPkg(this.provider.UPGRADE);
	},
								   
	loadInstalled: function(){
		this.loadPkg(this.provider.INST);
	},

	loadFilter: function(needle){
		this.loadPkg(this.provider.SEARCH, needle);
	}
});

/**
 * PkgNavHandler
 */
var PkgNavHandler = Class.create(AbstractAdminContentHandler,{
	initialize: function($super, target){
		$super('tplNavPkgs', target);
	},

	load: function(){
		data = {};
		core.setAjaxLoad('navContent');
		this.show(data);
	}
});

/**
 * SwitchFeedHandler
 * 
 */
var SwitchFeedHandler  = Class.create(AbstractAdminContentHandler, {
	initialize: function(){
		this.provider = new SimpleRequestProvider();
	},
									  
	load: function(url, parms){
		this.provider.simpleResultQuery(
				url,
				parms,
				this.simpleResultCallback.bind(this)
			);
	},

	showSimpleResult: function(result){
		id = result.getStateText();
		element = document.getElementById(id.replace('.off','') + "-pic");
		hiddenInput  = document.getElementById(id.replace('.off','') + "-name");
		if (result.getState()) {
			if (id.endsWith('.conf')) {
				element.alt='disable';
				element.src = '/web-data/img/minus.png';
				var title = 'enable ' + id;
				element.up('.sPkgConfFeedsLink').title='disable ' + id;
				
			}	
			else {
				element.alt='enable';
				element.src = '/web-data/img/plus.png';
				var title = 'enable ' + id.replace('.off','');
				element.up('.sPkgConfFeedsLink').title='enable ' + id.replace('.off','');
			}
			hiddenInput.value=id;
		}
		else {
			alert(id);
		};
	},
});

/**
 * MemoryHandler
 * 
 */

var MemoryHandler  = Class.create(AbstractAdminContentHandler, {
	initialize: function(){
		this.provider = new MemoryProvider(this.show.bind(this));
	},
									  
	load: function(url, parms){
		this.provider.simpleResultQuery(
				url,
				parms,
				this.simpleResultCallback.bind(this)
			);
	},

	getMem: function(){
		this.load('/webadmin/web/getmemory');
	},

	showSimpleResult: function(result){
		str = result.getStateText();
		if (result.getState()) {
			document.getElementById('memContent').innerHTML=result.getStateText() + " MB free";
		}
		else {
			alert(str);
		};
	},
});

/**
 * SimpleWebAdminPageHandler
 * 
 */

var templateEngine2 = new TemplateEngine('/webadmin/tpl/');

var SimpleWebAdminPageHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, target){
		$super(null, target);
	},

	show: function(tpl, data){
		templateEngine2.process(tpl, data, this.target, this.finished.bind(this));
	}
});
