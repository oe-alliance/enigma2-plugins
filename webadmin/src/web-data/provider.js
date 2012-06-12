
/**
 * ScriptListProvider
 * 
 */

var ScriptListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super('/webadmin/web/scriptlist', showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	
	renderXML: function(xml){
		var list = new ScriptList(xml).getArray();
		return {files : list};
	},
	
});


/**
 * PkgListConfProvider
 * 
 */

var PkgConfListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super('/webadmin/web/pkgconflist', showFnc);
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */
	renderXML: function(xml){
		var list = new PkgConfList(xml).getArray();
		return {files : list};
	},
	
});

/**
 * PkgListProvider
 * 
 */

var PkgListProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super('/webadmin/web/pkglist', showFnc);
		this.ALL=0;
		this.INST=1;
		this.UPGRADE=2;
		this.SEARCH=3;
		this.selection=this.ALL;
		this.needle="";
		this.packages =[];
	},

	/**
	 * renderXML
	 * See the description in AbstractContentProvider
	 */

	setSelection: function(sel, needle){
		this.selection = sel;
		if (needle)
			this.needle = needle.toUpperCase();
	},
		
	getSelected: function(){
		var data=[]
		if (this.packages.length != 0) {
			var len = this.packages.length;
			switch(this.selection){
				case this.ALL:
 				data = this.packages;
				break;

			case this.INST:
				for(var i=0;i<len;i++){
					var pkg = this.packages[i];
					if (pkg.state == "1")
						data.push(pkg);
				}
				break;

			case this.UPGRADE:
				for(var i=0;i<len;i++){
					var pkg = this.packages[i];
					if (pkg.update == "1")
						data.push(pkg);
				}
				break;

			case this.SEARCH:
				for(var i=0;i<len;i++){
					var pkg = this.packages[i];
					if (pkg.name.toUpperCase().indexOf(this.needle) != -1
						|| pkg.description.toUpperCase().indexOf(this.needle) != -1)
						data.push(pkg);
				}
				break;

			default:
				alert('[getSelected] packages.length = 0!');
			}
		}
		return data;
	},

	renderXML: function(xml){
		this.packages = new PkgList(xml).getArray();
		var data = this.packages;
		return {pkgs : this.getSelected(data) };
	},
	
});

/**
 *MemoryProvider
 * 
 */

var MemoryProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc) {
		$super('/webadmin/web/getmemory', showFnc);
	}
	
});


var PkgFakeProvider = Class.create(AbstractContentProvider, {
	/**
	 * initialize
	 * See the description in AbstractContentProvider
	 */
	initialize: function($super, showFnc){
		$super('/webadmin/web/fake', showFnc);
		this.packages = [];
	},

	setList: function(list){
		this.packages = list;
	},
								   
	renderXML: function(xml){
		var data = this.packages;
		return { pkgs : data };
	}
});