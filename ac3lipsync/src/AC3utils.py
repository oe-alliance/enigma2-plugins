AC3 = "AC3"
PCM = "PCM"
AC3GLOB = "AC3GLOB"
PCMGLOB = "PCMGLOB"
AC3PCM = (AC3,PCM,AC3GLOB,PCMGLOB)

PLUGIN_BASE = "AudioSync"
PLUGIN_VERSION = "1.0b2"

MOVEPOSITIONSTEP = 10

SKIN = """
        <screen flags="wfNoBorder" position="center,30" size="600,100" title="Audio Sync" zPosition="1" backgroundColor="#ff000000">
            <ePixmap pixmap="~/img/BGTable.png" zPosition="1" position="5,20" size="590,80" alphatest="on" transparent="1" />
            <widget name="AC3TableTabLabel" zPosition="2" position="10,0" size="140,26" font="Regular;14" halign="center" valign="center" transparent="1" backgroundColor="#232323" foregroundColors="#dddddd,#ffffff"/>
            <widget name="AC3TableTab" pixmaps="~/img/BGTableTabLight.png,~/img/BGTableTabDark.png" position="10,0" zPosition="1" size="140,26" transparent="1" alphatest="on" />
            <widget name="AC3GLOBTableTabLabel" zPosition="2" position="150,0" size="140,26" font="Regular;14" halign="center" valign="center" transparent="1" backgroundColor="#232323" foregroundColors="#dddddd,#ffffff"/>
            <widget name="AC3GLOBTableTab" pixmaps="~/img/BGTableTabLight.png,~/img/BGTableTabDark.png" position="150,0" zPosition="1" size="140,26" transparent="1" alphatest="on" />
            <widget name="PCMTableTabLabel" zPosition="2" position="290,0" size="140,26" font="Regular;14" halign="center" valign="center" transparent="1" backgroundColor="#232323" foregroundColors="#dddddd,#ffffff"/>
            <widget name="PCMTableTab" pixmaps="~/img/BGTableTabLight.png,~/img/BGTableTabDark.png" position="290,0" zPosition="1" size="140,26" transparent="1" alphatest="on" />
            <widget name="PCMGLOBTableTabLabel" zPosition="2" position="430,0" size="140,26" font="Regular;14" halign="center" valign="center" transparent="1" backgroundColor="#232323" foregroundColors="#dddddd,#ffffff"/>
            <widget name="PCMGLOBTableTab" pixmaps="~/img/BGTableTabLight.png,~/img/BGTableTabDark.png" position="430,0" zPosition="1" size="140,26" transparent="1" alphatest="on" />
            <ePixmap pixmap="~/img/AC3LipSyncBarBG.png" zPosition="2" position="180,26" size="370,21" alphatest="on" transparent="1" />
            <widget name="AudioSliderLabel" zPosition="2" position="12,26" size="150,21" font="Regular;18" backgroundColor="#232323" foregroundColor="#cccccc" transparent="1" />
            <widget name="AudioSliderBar" pixmap="~/img/AC3LipSyncBar.png" zPosition="3" position="180,26" size="370,21" transparent="1" />
            <widget name="AudioSlider" zPosition="4" position="180,26" size="370,21" font="Regular;18" halign="center" valign="center" transparent="1"/>
            <widget name="ServiceInfoLabel" zPosition="4" position="12,51" size="180,21" font="Regular;18" backgroundColor="#232323" foregroundColor="#cccccc" transparent="1" />
            <widget name="ServiceInfo" zPosition="4" position="197,51" size="180,21" font="Regular;18" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1" />
            <widget name="AC3DelayInfoLabel" zPosition="4" position="387,51" size="48,21" font="Regular;18" backgroundColor="#232323" foregroundColor="#cccccc" transparent="1" />
            <widget name="AC3DelayInfo" zPosition="4" position="437,51" size="50,21" font="Regular;18" foregroundColor="#ffffff" transparent="1" />
            <widget name="PCMDelayInfoLabel" zPosition="4" position="497,51" size="48,21" font="Regular;18" backgroundColor="#232323" foregroundColor="#cccccc" transparent="1" />
            <widget name="PCMDelayInfo" zPosition="4" position="547,51" size="50,21" font="Regular;18" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1" />
            <ePixmap pixmap="~/img/key-red.png" position="25,77" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="~/img/key-green.png" position="160,77" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="~/img/key-yellow.png" position="295,77" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="~/img/key-blue.png" position="430,77" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <widget name="key_red" position="50,77" zPosition="4" size="110,21"
                font="Regular;16" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1"/>
            <widget name="key_green" position="185,77" zPosition="4" size="110,21"
                font="Regular;16" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1"/>
            <widget name="key_yellow" position="320,77" zPosition="4" size="110,21"
                font="Regular;16" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1" />
            <widget name="key_blue" position="455,77" zPosition="4" size="110,21"
                font="Regular;16" valign="center" halign="left" backgroundColor="#232323" foregroundColor="#ffffff" transparent="1" />
        </screen>"""