Description: MSNWeather Converter and Renderer to display MSN-Weather in Skin... you need enigma2-plugin-extensions-weatherplugin to define a weather location, this components uses the first entry. The weather data are updating every 30 minutes...

Usage example:
	<widget alphatest="blend" render="MSNWeatherPixmap" position="850,30" size="128,128" source="session.MSNWeather" transparent="1" zPosition="5" >
		<convert type="MSNWeather">weathericon,current</convert>
	</widget>
	<widget alphatest="blend" render="MSNWeatherPixmap" position="910,203" size="62,62" source="session.MSNWeather" transparent="1" zPosition="5" >
		<convert type="MSNWeather">weathericon,day2</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;22" foregroundColor="black" render="Label" position="855,40" size="385,24" source="session.MSNWeather" zPosition="3" halign="right">
		<convert type="MSNWeather">temperature_current</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;18" foregroundColor="black" render="Label" position="855,70" size="385,24" source="session.MSNWeather" zPosition="3" halign="right">
		<convert type="MSNWeather">temperature_text,current</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;18" foregroundColor="black" render="Label" position="855,100" size="385,24" source="session.MSNWeather" zPosition="3" halign="right">
		<convert type="MSNWeather">temperature_heigh_low,current</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;16" foregroundColor="black" render="Label" position="855,120" size="385,24" source="session.MSNWeather" zPosition="3" halign="right">
		<convert type="MSNWeather">observationtime</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;20" foregroundColor="black" render="Label" position="855,140" size="385,24" source="session.MSNWeather" zPosition="3" halign="right">
		<convert type="MSNWeather">city</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;16" foregroundColor="black" render="Label" position="855,176" size="120,20" source="session.MSNWeather" zPosition="3" halign="center">
		<convert type="MSNWeather">weekday,day2</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;16" foregroundColor="black" render="Label" position="865,210" size="40,20" source="session.MSNWeather" zPosition="3" halign="left">
		<convert type="MSNWeather">temperature_high,day2</convert>
	</widget>
	<widget noWrap="1" backgroundColor="#1273B7" font="Regular;16" foregroundColor="black" render="Label" position="865,235" size="40,20" source="session.MSNWeather" zPosition="3" halign="left">
		<convert type="MSNWeather">temperature_low,day2</convert>
	</widget>


Description:

Displaying icons with MSNWeatherPixmap Renderer:

"weathericon,current" --> current weather icon
"weathericon,dayX" --> X = 1 to 5, 1 = current day

Displaying Info-data with Label Renderer:

observationtime
city
observationpoint
temperature_current
feelslike
humidity
winddisplay

--> this arguments do not need any further arguments


These arguments are depending of the day argument:

temperature_high
temperature_low
temperature_heigh_low
temperature_text
weekday
weekshortday
date

--> use with in combination with current or dayX (X = 1 to 5) (look for the examples)


usage example 2:

	<widget alphatest="blend" render="MSNWeatherPixmap" position="20,553" size="200,122" source="session.MSNWeather" transparent="1" zPosition="5" >
		<convert type="MSNWeather">weathericon,current,/etc/enigma2/weather_icons_special/,png</convert>
	</widget>

--> weathericon, current --> current weather icon
--> /etc/enigma2/weather_icons_special/ --> folder for weather icons
--> png --> file extensions


If you want to use this converter/renderer set a depends in the control file of your skin to: enigma2-plugin-systemplugins-weathercomponenthandler


If you have any questions visit www.dreambox-tools.info
Dr.Best
