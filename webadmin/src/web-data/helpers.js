var adminTemplateEngine = new TemplateEngine('/webadmin/tpl/');

/**
 * closeIf(el, sel)
 * 
 */

function closeIf(el, sel) {
if (el.value == sel || el.value == sel + ' stop' || el.value == sel + ' start')
	el.disabled=true;
else
	el.disabled=false;
}

/**
 * selectExec(name, val)
 * 
 */

function selectExec(name, val) {
	var element = document.getElementById('com-' + name);
	if (val == name + ' '){
		element.disabled=false;
	}
	else {
		element.disabled=true;
	}
	element.value=val;
}

/**
 * confirm_conf()
 * 
 */
function confirm_suffix(suffix){
	str=document.getElementById('finput').value;
	if(!str.endsWith(suffix)) {
		alert('File type not allowed,\nAllowed file: ' +suffix);
		document.getElementById('finput').value='';
		}
	else  {
		document.getElementById('fname').value = str.replace(/\\/g,'/').replace( /.*\//, '' );
	};
};

function uploadIkg(){
	var width  = 720;
	var height = 480;
	var left   = (screen.width  - width)/2;
	var top    = (screen.height - height)/2;
	var elementms = 'width='+width+', height='+height;
	elementms += ', top='+top+', left='+left;
	elementms += ', directories=no';
	elementms += ', location=no';
	elementms += ', menubar=no';
	elementms += ', resizable=no';
	elementms += ', scrollbars=yes';
	elementms += ', status=no';
	elementms += ', toolbar=no';
	upload=window.open('uploadpkg', 'uploadPkg', elementms);
	if (window.focus) {upload.focus()}
		return false;
};

/**
 * ScriptList
 * 
 */
function ScriptList(xml){
	this.xmlitems = getNamedChildren(xml, 'e2scriptlist', 'e2script');
	this.scriptlist = [];

	this.getArray = function(){
		if(this.scriptlist.length === 0){
			var len = this.xmlitems.length;
			for(var i=0; i<len; i++){
				var scr = new Script(this.xmlitems.item(i)).toJSON();
				this.scriptlist.push(scr);
			}
		}
		return this.scriptlist;
	};
}


/**
 * ScriptListList
 * 
 */
function Script(xml){
	this.name = getNodeContent(xml, 'e2name');
	this.text = getNodeContent(xml, 'e2text');

	this.json = {
			'name': this.name,
			'text': this.text,
	};

	this.toJSON = function(){
		return this.json;
	};
}

/**
 * PkgConf
 * 
 */

function PkgConf(xml){
	this.name = getNodeContent(xml, 'e2name');
	this.text = getNodeContent(xml, 'e2text');
	this.state = this.name.endsWith('conf') ? '1' : '0';

	this.getName = function () { return this.name.replace('.off',''); };

	this.json = {
			'name': this.getName(),
			'text': this.text,
			'state': this.state,
	};

	this.toJSON = function(){
		return this.json;
	};
}

/**
 * PkgConfList
 * 
 */
function PkgConfList(xml){
	this.xmlitems = getNamedChildren(xml, 'e2pkgconflist', 'e2pkgconf');
	this.pkgslist = [];

	this.getArray = function(){
		if(this.pkgslist.length === 0){
			var len = this.xmlitems.length;
			for(var i=0; i<len; i++){
				var pkg = new PkgConf(this.xmlitems.item(i)).toJSON();
				this.pkgslist.push(pkg);
			}
		}
		return this.pkgslist;
	};
}

/**
 * Pkg
 * 
 */
function Pkg(xml){
	this.name = getNodeContent(xml, 'e2name');
	this.release = getNodeContent(xml, 'e2release');
	this.description = getNodeContent(xml, 'e2info');
	this.state = getNodeContent(xml, 'e2state');
	this.update = getNodeContent(xml, 'e2update');

	this.json = {
			'name': this.name,
			'release': this.release,
			'description': this.description,
			'state': this.state,
			'update': this.update,
	};

	this.toJSON = function(){
		return this.json;
	};
}

/**
 * PkgList
 * 
 */
function PkgList(xml){
	this.xmlitems = getNamedChildren(xml, 'e2pkglist', 'e2pkg');
	this.pkgconflist = [];
	
	this.getArray = function(){
		if(this.pkgconflist.length === 0){
			var len = this.xmlitems.length;
			for(var i=0; i<len; i++){
				var file = new Pkg(this.xmlitems.item(i)).toJSON();
				this.pkgconflist.push(file);
			}
		}
		return this.pkgconflist;
	};
}

