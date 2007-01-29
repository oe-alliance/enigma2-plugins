// EPG Templates
var tplUpdateStreamReaderIE = '<iframe id="UpdateStreamReaderIEFixIFrame" src="%(url_updates)" height="0" width="0" scrolling="none" frameborder="0">no iframe support!</iframe>';
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
	tplEPGListItem +='<a target="_blank" ><img src="/webdata/gfx/timer.png" title="add to Timers" border="0" onclick="addTimerByID(\'%(servicereference)\',\'%(eventid)\');"></a><br/>';
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
	tplServiceListHeader += '<form onSubmit="loadEPGBySearchString(document.getElementById(\'searchText\').value); return false;">';
	tplServiceListHeader += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="Search EPG"/>';
	tplServiceListHeader += '<input style="vertical-align:middle" type="image" src="/webdata/gfx/search.png" alt="search...">';
	tplServiceListHeader += '</form></div></th>';
	tplServiceListHeader += '</tr>\n';
	tplServiceListHeader += '</thead>\n';
	tplServiceListHeader += '<tbody class="scrollContent">\n';

var tplServiceListItem  = '<tr>\n';
	tplServiceListItem += '<td style="border-top: 2px solid #AAA;" ><div class="sListSName"><a id="%(servicereference)" onclick="zap(this.id)" class="sListSLink">%(servicename)</a></div>';
	tplServiceListItem += '<div class="sListExt"><a onclick="loadEPGByServiceReference(this.id)" id="%(servicereference)"><img src="/webdata/gfx/epg.png" border="0"/></a>\n';
	tplServiceListItem += '<a target="_blank" href="/web/stream.m3u?ref=%(servicereference)"><img src="/webdata/gfx/screen.png" title="stream Service" border="0"></a></div>\n';
	tplServiceListItem += '</tr>\n';
    tplServiceListItem += '<tr>\n';
	tplServiceListItem += '<td colspan="2"><div id="%(servicereference)EPGNOW"></div></td>\n';
	tplServiceListItem += '</tr>\n';
	
var tplServiceListFooter = "</tbody></table>\n";
//

var	tplServiceListEPGItem  = '<div class="sListEPGTime">%(starttime)</div>\n';
	tplServiceListEPGItem += '<div class="sListEPGTitle">%(title)</div>\n';
	tplServiceListEPGItem += '<div class="sListEPGDuration">%(length) Min.</div>\n';

// MovieList Templates
var tplMovieListHeader  = '<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
	tplMovieListHeader += '<thead class="fixedHeader">\n';
	tplMovieListHeader += '<tr>\n';
	tplMovieListHeader += '<th><div class="sListHeader" style="color: #FFFFFF;">MovieList</div>\n';
	tplMovieListHeader += '<div class="sListSearch">';
	tplMovieListHeader += '<form onSubmit="loadEPGBySearchString(document.getElementById(\'searchText\').value); return false;">';
	tplMovieListHeader += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="Search EPG"/>';
	tplMovieListHeader += '<input style="vertical-align:middle" type="image" src="/webdata/gfx/search.png" alt="search...">';
	tplMovieListHeader += '</form></div></th>';
	tplMovieListHeader += '</tr>\n';
	tplMovieListHeader += '</thead>\n';
	tplMovieListHeader += '<tbody class="scrollContent">\n';

var tplMovieListItem  = '<tr>\n';
	tplMovieListItem += '<td><div class="sListSName" title="%(description), %(descriptionextended)">%(title) (%(servicename))</div>';
	tplMovieListItem += '<div class="sListExt">\n';
	tplMovieListItem += '%(tags)\n';
	tplMovieListItem += '</div>\n';
	tplMovieListItem += '</tr>\n';
	
var tplMovieListFooter = "</tbody></table>\n";

// TimerList Templates
var tplTimerListHeader  = '<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
	tplTimerListHeader += '<thead class="fixedHeader">\n';
	tplTimerListHeader += '<tr>\n';
	tplTimerListHeader += '<th><div class="sListHeader" style="color: #FFFFFF;">TimerList</div>\n';
	tplTimerListHeader += '<div class="sListSearch">';
	tplTimerListHeader += '<form onSubmit="loadEPGBySearchString(document.getElementById(\'searchText\').value); return false;">';
	tplTimerListHeader += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="Search EPG"/>';
	tplTimerListHeader += '<input style="vertical-align:middle" type="image" src="/webdata/gfx/search.png" alt="search...">';
	tplTimerListHeader += '</form></div></th>';
	tplTimerListHeader += '</tr>\n';
	tplTimerListHeader += '</thead>\n';
	tplTimerListHeader += '<tbody class="scrollContent">\n';

var tplTimerListItem  = '<tr>\n';
	tplTimerListItem += '<td><div class="sListSName" id="TimerColor%(state)" title="%(description), %(descriptionextended)">%(title) (%(servicename))</div>';
	tplTimerListItem += '<div class="sListExt" id="TimerColor%(state)">\n';
	tplTimerListItem += '%(duration)&nbsp;Min\n';
	tplTimerListItem += '<a target="_blank" ><img src="/webdata/gfx/trash.gif" title="delete timer entry" border="0" width="20" height="20" onclick="delTimer(\'%(servicereference)\',\'%(begin)\',\'%(end)\');"></a><br/>';
	tplTimerListItem += '</div>\n';
	tplTimerListItem += '</tr>\n';
	
var tplTimerListFooter = "</tbody></table>\n";

// Bouquetlist Template
var tplBouquetListHeader = '<table id="BouquetList" width="100%" border="0" cellspacing="1" cellpadding="0" border="0">';

var tplBouquetListItem  = '<tr>\n';
	tplBouquetListItem += '<td><div class="navMenuItem" id="%(servicereference)" onclick="loadBouquet(this.id);">%(bouquetname)</div></td>';
	tplBouquetListItem += '</tr>\n';

var tplBouquetListFooter = "</table>";

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
	
//Signal Template
var tplSignalPanel  = '<table width="100%" id="SignalPanelTable">';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">SNR</td><td width="50" style="background-color: #DDDDDD;"><div id="SNR">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">AGC</td><td width="50" style="background-color: #DDDDDD;"><div id="AGC">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">BER</td><td width="50" style="background-color: #DDDDDD;"><div id="BER">N/A</div></td></tr>';
	tplSignalPanel += '</table>';
	
var tplSignalPanelButton = '<img src="/webdata/gfx/signal.png" title="show SignalInfoPanel" onclick="openSignalDialog();" title="view Signal Info">';

// Message send
var tplMessageSendForm = ""
	tplMessageSendForm += '<table id="MessageSendForm" width="100%" border="0" cellspacing="1" cellpadding="0" border="0">';
	tplMessageSendForm += '<tr><td>Text</td><td><input type="text" id="MessageSendFormText" value=""></td></tr>\n';
	tplMessageSendForm += '<tr><td>Timeout</td><td><input type="text" id="MessageSendFormTimeout" value=""></td></tr>\n';
	tplMessageSendForm += '<tr><td>Typ</td><td><select id="MessageSendFormType">';
	tplMessageSendForm += '<option value="1">Info</option>';
	tplMessageSendForm += '<option value="0">YesNo</option>';
	tplMessageSendForm += '<option value="2">Warning</option>';
	tplMessageSendForm += '<option value="3">Error</option>';
	tplMessageSendForm += '</select></td></tr>\n';
	tplMessageSendForm += '<tr><td colspan="2"><button onclick="sendMessage()">send Message</button></td></tr>\n';
	tplMessageSendForm += "</table></form>\n";

//var tplPasswordSendForm = ""
//	tplPasswordSendForm += '<table id="PasswordSendForm" width="100%" border="0" cellspacing="1" cellpadding="0" border="0">';
//	tplPasswordSendForm += '<tr><td>Old password</td><td><input type="password" id="PasswordSendFormOldPassword" value=""></td></tr>\n';
//	tplPasswordSendForm += '<tr><td>New password</td><td><input type="password" id="PasswordSendFormNewPassword" value=""></td></tr>\n';
//	tplPasswordSendForm += '<tr><td>Repeat new password</td><td><input type="password" id="PasswordSendFormNewPasswordSecond" value=""></td></tr>\n';
//	tplPasswordSendForm += '<tr><td colspan="2"><button onclick="sendPasswords()">change password for user dreambox</button></td></tr>\n';
//	tplPasswordSendForm += "</table></form>\n";
	
var tplPowerStateSendForm = '';
    tplPowerStateSendForm += '<p><center><button onclick="sendPowerState(' + "'poweroff'" + ')">Poweroff Dreambox</button></center></p>';
    tplPowerStateSendForm += '<p><center><button onclick="sendPowerState(' + "'rebootdreambox'" + ')">Reboot Dreambox</button></center></p>';
    tplPowerStateSendForm += '<hr>';
    tplPowerStateSendForm += '<p><center><button onclick="sendPowerState(' + "'standby'" + ')">Standby Dreambox</button></center></p>';
    tplPowerStateSendForm += '<p><center><button onclick="sendPowerState(' + "'rebootenigma'" + ')">Reboot Enigma2</button></center></p>';
