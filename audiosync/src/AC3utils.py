AC3 = "AC3"
PCM = "PCM"
AC3GLOB = "AC3GLOB"
PCMGLOB = "PCMGLOB"
AC3PCM = (AC3, PCM, AC3GLOB, PCMGLOB)

PLUGIN_BASE = "AudioSync"
PLUGIN_VERSION = "1.2"

MOVEPOSITIONSTEP = 10

SKIN = """
        <screen flags="wfNoBorder" position="30,30" size="600,460" title="Audio Sync" zPosition="1" backgroundColor="#ff000000">
            <ePixmap pixmap="~/img/AudioSyncBG.png" zPosition="1" position="0,0" size="600,460" alphatest="on" transparent="1" />
            <widget name="ChannelLabel" zPosition="2" position="33,40" size="130,20" font="Regular;14" halign="center" valign="center" transparent="1" backgroundColor="#232323" foregroundColors="#ffffff,#fe6b1b"/>
            <widget name="ChannelImg" pixmaps="~/img/OptionButtonOff.png,~/img/OptionButtonOn.png" position="20,43" zPosition="2" size="11,11" transparent="1" alphatest="on"/>
            <widget name="GlobalLabel" zPosition="2" position="178,40" size="110,20" font="Regular;14" halign="center" valign="center" transparent="1" backgroundColor="#232323" foregroundColors="#ffffff,#fe6b1b"/>
            <widget name="GlobalImg" pixmaps="~/img/OptionButtonOff.png,~/img/OptionButtonOn.png" position="165,43" zPosition="2" size="11,11" transparent="1" alphatest="on"/>
            <ePixmap pixmap="~/img/AudioSyncBarBGVert.png" zPosition="2" position="30,70" size="21,370" alphatest="on" transparent="1" />
            <widget name="AudioSliderBar" pixmap="~/img/AudioSyncBarVert.png" zPosition="3" position="30,70" size="21,370" transparent="1" orientation="orBottomToTop"/>
            <widget name="AudioSlider" zPosition="4" position="5,245" size="70,20" font="Regular;14" halign="center" valign="center" backgroundColor="#232323" foregroundColor="#eeeeee" transparent="1"/>
            <widget name="ServiceInfoLabel" zPosition="4" position="20,15" size="65,20" font="Regular;14" backgroundColor="#232323" foregroundColor="#dddddd" transparent="1" />
            <widget name="ServiceInfo" zPosition="4" position="90,15" size="200,20" font="Regular;14" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1" />
            <ePixmap pixmap="~/img/key-green.png" position="290,15" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="~/img/key-red.png" position="290,40" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="~/img/key-blue.png" position="400,15" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <widget name="key_green" position="315,15" zPosition="4" size="85,20"
                font="Regular;14" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1"/>
            <widget name="key_red" position="315,40" zPosition="4" size="85,20"
                font="Regular;14" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1"/>
            <widget name="key_blue" position="425,15" zPosition="4" size="160,20"
                font="Regular;14" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1" />
        </screen>"""
