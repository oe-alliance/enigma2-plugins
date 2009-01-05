Version = '$Header$';
// EPG Templates

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


var tplExtraHiddenFunctions  = '<ul style="list-style-type:disc">';
	tplExtraHiddenFunctions += '<li><div onclick="restartTwisted()">Restart Twisted</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="clearInterval(UpdateStreamReaderPollTimer);">Stop Time/Signal/Current-Channel -Updates</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="restartUpdateStream();">Restart Time/Signal/Current-Channel -Updates</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="startDebugWindow();">Start Debug-Window</div></li>';
	tplExtraHiddenFunctions += '</ul>'
