===========================================================
FanControl2 by joergm6                           Help V.2.7
Support forum: IHAD
Acknowledgments: diddsen, _marv_, DreamKK, Lukasz S.
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

   for 4pin (PID) Fan type -- by Lukasz S.
Voltage and PWM is controlled automatically by a PI controller, that
tries to follow the Target RPM calculated by the built-in algorithm,
and minimize the difference between target RPM and current.

Control theory explanation en.wikipedia.org/wiki/PID_controller;
In this implementation, only Proportional and Integral section is used 
(no Derivative).

   Features: 
Built-in input deadband will ensure controller won't act unless the
Target RPM differs from Current RPM by more than 1% either way, to
filter out spikes and fluctuations in actual fan speed measurements.

In this mode PID Ctl Err (its percentage) is showing why the controller
thinks it should speed fan up (or slow down).

Fan is controlled by means of PWM first (keeping voltage at minimum setting),
only progressing to change voltage if PWM would be larger than 255;
If calculated PWM would go below 255 again, voltage is set back to min.
(in effect, voltage is treated as overspill for PWM, with different coefficient
to prevent too large changes in voltage)

   Setup:

Initial Voltage and Initial PWM shall be set so that fan has exactly min 
speed that you require, and that shall be set as 'min speed RPM' setting.
(to avoid 'battling' with the PI controller over the pwm and voltage settings, 
change to the traditional 4pin to determine this - or use the Check feature)

(On Authors' box, setting Initial Voltage and PWM to zero didn't stop the fan
my minimum fan speed on 0 volt and 0 PWM was about 850 RPM)

'max speed RPM' should be set to maximum fan speed you ever want the fan to 
achieve AND is achievable by available setting of voltage and PWM. 
Setting this to an unreachable value may lead to improper behavior.

   Known Problems: 
   * crossing the PWM - VLT control boundary, can look like it's unstable,
because of different reaction of the fan to controlling it with voltage, 
vs what it does on PWM solely. Workaround: set your Static Temp so that 
PWM won't reach 255 in normal conditions, or so that Voltage won't need 
to fall below minimum setting in normal conditions. 
(Example procedure : launch the FanControl2 interface when your box is 
in what you think is its normal working temperature, and if the PWM displayed 
is close to 255, but on the PWM side, set the static temperature to a degree 
or two higher than current setting; if the voltage is being controlled already 
and is near the min vlt setting, set the static temp to a degree or two MORE 
than current static temp setting - to ensure controller output is considerably 
under 255 for PWM, and considerably more than min Volt for Voltage). 
Unfortunately there is not much that can be done here unless some automation 
is employed to tune this as it can differ from fan to fan, and even from box 
to box, and also fan response to controlling will get worse as it ages, due to
bearings getting old. Plan is to work on recognizing failing fan bearings situation.
   
   * If static temp setting is changed, controllers' integrator is reset, starts from 0,
to prevent long-time of unwinding, but it has the effect of setting minimum PWM and Voltage,
slowing the fan down to minimum first. This is actually a feature, not a problem, 
but it probably should be made configurable.
   
   * PID Ctl Err displaying the error, can be misleading when displaying negative value;
This is being explored to find a widget which can handle showing 0 in the middle and then the 
signed value either way.

-- by Lukasz S.

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

