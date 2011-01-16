== E.I.B.ox setup how-to ==

* install and setup linknx server
  (cf. http://sourceforge.net/apps/mediawiki/linknx/)

either
 * install knxweb
 * create visualization using knxweb ajax frontend
 * save as design.xml
or
 * modify design.sample.xml from the plugin directory
or
 * create visualization layout xml by hand

* add or adapt this line in the <config> section of design.xml:
	<settings host="yourlinknxhost" port="1028" refresh="0" debug="true"/>
  refresh time is in ms. intervals below 500 will disable auto refresh.
  it is recommended to disable refresh and enable debug during setup phase and then 
  enable autorefresh and disable debug for performance reasons during normal operation

* copy design.xml into plugin directory on your dreambox
   
* quantize your custom images (must be in PNG format)
	pngquant 256 inputfilename.png 
  (cf. http://www.libpng.org/pub/png/apps/pngquant.html)

* rename quantized images back to original names and copy them to the images subdirectory

* restart enigma2 and have fun testing

* usage is pretty much self-explanatory:
  navigate with up and down keys,
  switch or change values with OK or left and right keys
  thermostat values can directly be entered with number keys
  navigation order is defined by the order of control nodes in the design.xml

* please report bugs at http://www.dream-multimedia-tv.de/board/



== known issues ==

so far the following "widgets" of knxweb have been implemented in E.I.B.ox:
* switches for light, blinds, outlet, fan, pump
* multiswitch
* light dimmer
* thermostat (actual temperature and set point)
* text
* zone goto

still to be implemented are
* thermostat KONNEX mode switching
* value input
* camera link



== constraints ==

* for right now, screens are not optimized for FULL HD yet, so they will work on a regular SD screen
* have background images, use only PNG files with dimensions of exactly 550x400
* for icons, use 32x32 PNGs
* don't have dots ('.') in your object IDs or dimmer progress bars won't work

