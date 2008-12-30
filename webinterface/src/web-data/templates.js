Version = '$Header$';
// EPG Templates
var tplUpdateStreamReaderIE = '<iframe id="UpdateStreamReaderIEFixIFrame" src="%(url_updates)" height="0" width="0" scrolling="none" frameborder="0">no iframe support!</iframe>';


var tplEPGListItemExtend  = '%(shortTxt) ...<a nohref onclick="setComplete(\'extdescription%(number)\',\'%(txt)\');">more</a>';

var tplRecordingFooter   = '<hr><br><table style="text-align: left; width: 100%; height: 178px;" border="0" cellpadding="2" cellspacing="2"><tbody>';
    tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
    tplRecordingFooter  += '<input type="radio" id="recordNowNothing" name="recordNow" value="nothing" checked>';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += 'Do nothing';
    tplRecordingFooter  += '</td></tr>';
    tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
    tplRecordingFooter  += '<input type="radio" id="recordNowUndefinitely" name="recordNow" value="undefinitely">';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += 'record current playing undefinitely';
    tplRecordingFooter  += '</td></tr>';
    tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
    tplRecordingFooter  += '<input type="radio" id="recordNowCurrent" name="recordNow" value="recordCurrentEvent">';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += 'record current event';
    tplRecordingFooter  += '</td></tr>';
	tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
	tplRecordingFooter  += '&nbsp;';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += '<img src="/webdata/gfx/ok.jpg" title="OK" border="0" onclick="recordingPushedDecision(ifChecked($(\'recordNowNothing\')), ifChecked($(\'recordNowUndefinitely\')), ifChecked($(\'recordNowCurrent\')) );window.close()">';
    tplRecordingFooter  += '</td></tr>';
    tplRecordingFooter  += '</tbody></table>';

//Signal Template
var tplSignalPanel  = '<table width="100%" id="SignalPanelTable">';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">dB</td><td style="background-color: #DDDDDD;"><div id="SNRdB">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">SNR</td><td style="background-color: #DDDDDD;"><div id="SNR">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">AGC</td><td style="background-color: #DDDDDD;"><div id="AGC">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">BER</td><td style="background-color: #DDDDDD;"><div id="BER">N/A</div></td></tr>';
	tplSignalPanel += '</table>';


var tplExtraHiddenFunctions  = '<ul style="list-style-type:disc">';
	tplExtraHiddenFunctions += '<li><div onclick="restartTwisted()">Restart Twisted</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="clearInterval(UpdateStreamReaderPollTimer);">Stop Time/Signal/Current-Channel -Updates</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="restartUpdateStream();">Restart Time/Signal/Current-Channel -Updates</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="startDebugWindow();">Start Debug-Window</div></li>';
	tplExtraHiddenFunctions += '</ul>'

var tplMediaPlayerHeader  = '<div class="BodyContentChannellist">\n<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
	tplMediaPlayerHeader += '<thead class="fixedHeader">\n';
	tplMediaPlayerHeader += '<tr>\n';
	tplMediaPlayerHeader += '<th><div class="sListHeader">MediaPlayer %(root)';
	tplMediaPlayerHeader += '<map name="mpcontrols">';
	tplMediaPlayerHeader += '<area shape="circle" coords="17, 17, 14" nohref onclick="sendMediaPlayer(0)" alt="jump back">';
	tplMediaPlayerHeader += '<area shape="circle" coords="54, 17, 14" nohref onclick="sendMediaPlayer(1)" alt="play">';
	tplMediaPlayerHeader += '<area shape="circle" coords="88, 17, 14" nohref onclick="sendMediaPlayer(2)" alt="pause">';
	tplMediaPlayerHeader += '<area shape="circle" coords="125, 17, 14" nohref onclick="sendMediaPlayer(3)" alt="jump forward">';
	tplMediaPlayerHeader += '<area shape="circle" coords="161, 17, 14" nohref onclick="sendMediaPlayer(4)" alt="stop">';
	tplMediaPlayerHeader += '</map><img src="/webdata/gfx/dvr-buttons-small-fs8.png" align="top" title="Control MediaPlayer" border="0" usemap="#mpcontrols">\n'
//	tplMediaPlayerHeader += '<img src="/webdata/gfx/edit.gif" onclick="openMediaPlayerPlaylist()">';
// still need some work for editing.
	tplMediaPlayerHeader += '</div>\n';
	tplMediaPlayerHeader += '<div class="sListSearch">';
	tplMediaPlayerHeader += '<img src="/webdata/gfx/nok.png" align="top" title="close MediaPlayer" border="0" onclick="sendMediaPlayer(5)"></div></th>';
	tplMediaPlayerHeader += '</tr>\n';
	tplMediaPlayerHeader += '</thead>\n';
	tplMediaPlayerHeader += '<tbody class="scrollContent">\n';

var tplMediaPlayerItemHead = '<tr>\n';
var tplMediaPlayerItemBody = '<td><div style="color: #%(color);" onclick="%(exec)(\'%(servicereference)\',\'%(root)\');" class="sListSName" title="%(servicereference)">%(name)</div>';
var	tplMediaPlayerItemIMG  = '<div class="sListExt">\n';
	tplMediaPlayerItemIMG += '<img src="/webdata/gfx/play.png" onclick="%(exec)(\'%(servicereference)\',\'%(root)\');" title="%(exec_description)" border="0">\n';
	tplMediaPlayerItemIMG += '<a target="_blank" href="/file/?file=%(name)&root=%(root)"><img src="/webdata/gfx/save.png" title="download File" border="0"></a>\n';
	tplMediaPlayerItemIMG += '</div>\n';
var tplMediaPlayerItemFooter = '</tr>\n';

var tplMediaPlayerFooterPlaylist  = '<tr><td colspan="7"><button onclick="writePlaylist()">Write Playlist</button></td></tr>\n';
var tplMediaPlayerFooter = "</tbody></table>\n";


var tplFileBrowserHeader  = '<div class="BodyContentChannellist">\n<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
    tplFileBrowserHeader += '<thead class="fixedHeader">\n';
    tplFileBrowserHeader += '<tr>\n';
    tplFileBrowserHeader += '<th><div class="sListHeader">FileBrowser %(root)</div></th>\n';
    tplFileBrowserHeader += '<th><div class="sListSearch">';
	tplFileBrowserHeader += '<form onSubmit="loadFileBrowser(\'%(root)\', document.getElementById(\'searchText\').value); return false;">';
	tplFileBrowserHeader += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="Search Pattern"/>';
	tplFileBrowserHeader += '<input style="vertical-align:middle" type="image" src="/webdata/gfx/search.png" alt="search...">';
	tplFileBrowserHeader += '</form></div></th>';
    tplFileBrowserHeader += '</tr>\n';
    tplFileBrowserHeader += '</thead>\n';
    tplFileBrowserHeader += '<tbody class="scrollContent">\n';
    tplFileBrowserHeader += '<tr width="80%"><td>File/Directory</td>\n';
    tplFileBrowserHeader += '<td>Action</td>\n</tr>\n';

var tplFileBrowserItemHead = '<tr width="80%">\n';
var tplFileBrowserItemBody = '<td><div style="color: #%(color);" onclick="%(exec)(\'%(servicereference)\',\'%(root)\');" class="sListSName" title="%(servicereference)">%(name)</div></td>';
var tplFileBrowserItemIMG  = '<td><div class="sListExt">\n';
    tplFileBrowserItemIMG += '<img src="/webdata/gfx/trash.gif" onclick="delFile(\'%(name)\',\'%(root)\');" title="delete File" border="0">\n';
    tplFileBrowserItemIMG += '<a target="_blank" href="/file/?file=%(name)&root=%(root)"><img src="/webdata/gfx/save.png" title="download File" border="0"></a>\n';
    tplFileBrowserItemIMG += '</div></td>\n';
var tplFileBrowserItemFooter = '</tr>\n';

var tplFileBrowserFooter  = '</tbody></table>\n';
	tplFileBrowserFooter += '<form action="/upload" method="POST" target="_blank" enctype="multipart/form-data">';
	tplFileBrowserFooter += '<input type="hidden" id="path" value="%(root)" name="path">';
	tplFileBrowserFooter += '<input name="file" type="file">';
	tplFileBrowserFooter += '<input type="image" style="vertical-align:middle" src="/webdata/gfx/save.png" alt="upload">';
