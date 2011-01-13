===========================================================
FanControl2 by joergm6                           Help V.2.4
Support forum: IHAD
Acknowledgments: diddsen, _marv_, DreamKK
                 Spaeleus(it), mimi74(fr), Bschaar(nl)
===========================================================
Apologies if the english translation is not always correct.

   Function
   --------
Control a 3pin or 4pin fan (PWM) depends from the average
of the 2 highest temperature values.
Slowly regulation, because temperatures are not too
change quickly and there should no unnecessary CPU load.

   Security Features
   -----------------
If 20min no reports of the fan speed, it is assumed that the
fan is defective. Regularly appears on the TV then an
appropriate message.
If standby mode the fan is off, the fan switched on, when the maximum
temperature is exceed. The temperature drops by more than 3C the fan
turns off again. The fan runs in the first 10 minutes with
minimum speed.
The overheat protection can be increased by up to 9C.
It can be set when shutting down the box, at which temperature and
fan failure.

   Preferences
   -----------
   Fan off in Standby
yes = Fan will be turned off if the box is in standby
yes, Except for recording or HDD= Fan is turned off in standby
if there is no recording and HDD is in Sleep-Mode

   Min speed
At Temperature "static-temperature" and below it is set this
speed.

   Max speed
At Temperature "end-temperature" it is set this speed.

   Static temperature
Until this temperature is not regulated, min speed is set.

   End Temperature
This is the maximum temperature may occur, is
this achieved, we will set the max speed.

   Initially, voltage and PWM
When changing the values the fan is immediately set with these
values. It can now be directly read off the speed. The controlling
is nevertheless once again active. So quick look or change the
values.
These values are set when the box boots up or if the fan was
switched off in standby.
  
   for 3pin Fan type
For regulation of voltage 3-pin fan with tachometer signal.
Is controlled only the voltage. Settings for PWM have no control.
Sets the initial voltage to a value of Rotation rate, 
with the fan at the start of the Box initially intended to run.
From this starting speed is regulated.

   for 4pin Fan type
For regulation PWM, 4-pin Fan. First is controlled the PWM value.
If the control range is no longer sufficient, if possible, also
regulate the voltage.
The voltage adjustment is required. Set the voltage on the
Maximum value (for DM500HD set 5-10). But also a lower voltage level
is useful. A lower voltage means a lower maximum speed and a lower
minimum speed. Set the voltage as possible so that the control
range with PWM enough.
There are also fans spin at PWM = 0 to be too high.
Reduce the voltage here, until the desired min Speed (including 0 is
possible) is achieved. Have also the max speed in mind.
PWM provides a value that corresponds to the speed, initially run
the fan at the start of the Box. From this speed is regulated.

   for Fan type Control disabled
The regulation is disabled. The fan runs with the last parameters
further. The fan is not turned off!

   Check
   -----
This attempts to determine the minimum speed of the fan
for the startup and the minimum before the fan speed goes
shutdown.
Similarly, the maximum speed for these settings is
determined. (OK) mean value matches the settings
(!!) values do not match. These details are for information
and do not affect the regulation, within the possible.
4Pin to be displayed in addition information on the wider
control range. That means it is on the PWM area also changed
the voltage.

   Temperature Monitor
   -------------------
With the "info key", can the individual values of the temperatures
are shown.
Press the Info button for single reading of HDD temperature.

   Special Setup
   -------------
With the "Menu key" special values can be defined.
Action in case of fan failure      [show info]
  Notification of defective fan, box shut down or do nothing.
Box shutdown at temperature (C)    [65]
  Upon reaching the specified temperature, the box switch off
  (DeepStandby).
Thermal protection increase at (C) [0]
  If the fan is off in standby the fan switched on at maximum
  temperature. This maximum temperature can be increased by 
  up to 9C
read HDD-Temperature in HDD-Standby-Mode [auto]
  yes = read HDD temperature in HDD-Standby
  no = read HDD temperature only when HDD is active
  Auto = at the start of FC2 once tested whether the HDD
         starts, and if so reading is disabled
  never = Temperature is never read
DMM fancontrol disabled            [No]
  Appears in the skins with temperature, the DMM-FanControl is active
  and also switch the fan. It caused unwanted on/off operations.
  Recommendation: Disable DMM-FanControl
See Monitor in extension menu      [Yes]
  Monitor shown in the extension menu (Long-Blue-Button).
WebIF number of log entries        [40]
  How many events should be show in WebIF.
  40-999
Logging directory
  Choose the "OK" the place to which directory the log files are written.
  Data is written only if least 10MByte are free.
Enable Data Logging
  There will be written every minute a record in the file FC2data.csv. 
  This can called directly in Excel. If this file does not exist and will
  Option enabled, a header is generated.
  about 4kBytes each hour
Auto-Delete Data older than (days) [No]
  Data-logging-Data older than this definition are
  deleted.
  Starting: daily at 00:00 and at Enigma2 start
Enable Event Logging
  There will be written all Events in the file FC2events.txt.
  about 30kByte each hour

   Web Interface
   -------------
Call: http://dreamboxip/fancontrol
Displays information about current fan-values and the last
Event logs. Per hour a value for temperature and Speed is appears.
With "FC2 Log", the log files are downloaded and the logging can be set.
"FC2 Chart" shows online diagrams of the last 48 hours. The Data
Logging must be enabled to do so. It must be present at least 2.5h data!
When using Firefox, it may happen that the diagram does not
display properly. Then, an additional Page refresh (F5) is necessary.

   Miscellaneous
   -------------
All important for the fan current readings
appears as a value and bar graph. The bar display
range is based on the individually set parameters.
FanControl2 is prepared for different languages.
POT file is in ipkg if anyone other languages
would make available.
The settings are stored in the normal Enigma2 settings and
are therefore included in the backup / restore.


===========================================================

