// EPG Templates

var tplEPGListHeader = '<table width="100%" border="0" cellspacing="1" cellpadding="0">';

var tplEPGListItem  = '<tr style="background-color: #DDDDDD;">';
	tplEPGListItem += '<td width="10%">%(date)</td>';
	tplEPGListItem += '<td width="30%">%(servicename)</td>';
	tplEPGListItem += '<td>%(title)</td>';
	tplEPGListItem += '</tr>';
	
	tplEPGListItem += '<tr style="background-color: #DDDDDD;">';
	tplEPGListItem += '<td>%(starttime)</td>';
	tplEPGListItem += '<td>%(duration) min.</td>';
	tplEPGListItem += '<td>%(description)</td>';
	tplEPGListItem += '</tr>';
	
	tplEPGListItem += '<tr style="background-color: #DDDDDD;">';
	tplEPGListItem += '<td valign="top">%(endtime)</td>';
	tplEPGListItem += '<td colspan="2"rowspan="2">%(extdescription)</td>';
	tplEPGListItem += '</tr>';
	
	tplEPGListItem +='<tr style="background-color: #DDDDDD;"><td>';
	tplEPGListItem +='<a target="_blank" ><img src="/webdata/gfx/timer.png" title="add to Timers" border="0"></a><br/>';
	tplEPGListItem +='<a target="_blank" href="/web/epgsearch.rss?search=%(title)" ><img src="/webdata/gfx/feed.png" title="RSS-Feed for this Title" border="0"></a><br/>';
	tplEPGListItem +='<a target="_blank" href="http://www.imdb.com/find?s=all&amp;q=%(titleESC)" ><img src="/webdata/gfx/world.png" title="search IMDb" border="0"></a><br/>';
	tplEPGListItem +='</td></tr>';
	
	tplEPGListItem += '<tr style="background-color: #AAAAAA;">';
	tplEPGListItem += '<td colspan="3">&nbsp;</td>';
	tplEPGListItem += '</tr>';
	
var tplEPGListFooter = "</table>";
	
// ServiceList Templates
var tplServiceListHeader  = '<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
	tplServiceListHeader += '<thead class="fixedHeader">\n';
	tplServiceListHeader += '<tr>\n';
	tplServiceListHeader += '<th><div class="sListHeader" style="color: #FFFFFF;">ServiceList</div>\n';
	tplServiceListHeader += '<div class="sListSearch">';
	tplServiceListHeader += '<form onSubmit="new EPGList().getBySearchString(document.getElementById(\'searchText\').value); return false;">';
	tplServiceListHeader += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="EPG suchen"/>';
	tplServiceListHeader += '</form></div></th>';
	tplServiceListHeader += '</tr>\n';
	tplServiceListHeader += '</thead>\n';
	tplServiceListHeader += '<tbody class="scrollContent">\n';

var tplServiceListItem  = '<tr>\n';
	tplServiceListItem += '<td><div class="sListSName"><a id="%(serviceref)" onclick="zap(this)" class="sListSLink" href="#">%(servicename)</a></div>';
	tplServiceListItem += '<div class="sListExt"><a href="#"><img onclick="new EPGList().getByServiceReference(this.id);" id="%(serviceref)" src="/webdata/gfx/epg.png" border="0"/></a>\n';
	tplServiceListItem += '<a target="_blank" href="stream.m3u?ref=%(servicerefESC)"><img src="/webdata/gfx/screen.png" title="stream Service" border="0"></a></div>\n';
	tplServiceListItem += '</tr>\n';
	
var tplServiceListFooter = "</tbody></table>\n";

//Volume Template
var tplVolumePanel  = "<img onclick='volumeUp()' src='/webdata/gfx/arrow_up.png'>"; 
	tplVolumePanel += "<img onclick='volumeDown()' src='/webdata/gfx/arrow_down.png'>"; 
	tplVolumePanel += "<img id='volume1' onclick='volumeSet(10)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume2' onclick='volumeSet(20)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume3' onclick='volumeSet(30)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume4' onclick='volumeSet(40)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume5' onclick='volumeSet(50)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume6' onclick='volumeSet(60)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume7' onclick='volumeSet(70)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume8' onclick='volumeSet(80)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume9' onclick='volumeSet(90)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='volume10' onclick='volumeSet(100)' src='/webdata/gfx/led_off.png'>"; 
	tplVolumePanel += "<img id='speaker' onclick='volumeMute()' src='/webdata/gfx/speak_on.png'>";