====================================================
Elektro Power Save for Dreambox 
Version 1 & 2 by gutemine
Version 3 by Morty <morty@gmx.net>
Profiles, HDD, IP, NAS Mod by joergm6
====================================================
Release infos 
====================================================
1.0   first version, as usually completely 
      untested - have Fun !
1.1   now after boot the Dreambox will go 
      immediately to normal Standby
1.2   some bugfixes on Plugin Text and 
      make standby on boot configurable
2.0   make ipk kit, add info messages before standby 
      and prevent deepstandby if timer is running
2.1   bug fixes and support for new images with TryQuit
      mainloop (which is since mid January 2007 in CVS)
2.2   still alive 
2.3   make compatible with latest CVS changes
      probably last version by gutemine

3.0   Rewritten by Morty, lots of new features
3.0.2 It's now possible to adjust the how long to
      show the shutdown screen
3.0.4 Bugfix
3.0.5 Fixed problem where the box shuts down again
      when it boots up too fast
3.1.0 Removed unneeded dependencies
      Don't shut down if woken up manually
3.2.0 Recording detection should work now
      Holiday mode has been implemented
3.2.1 Fixed Bug not recognizing a wakeup by Elektro 
3.2.2 Added the Italian translation by Spaeleus     
3.2.3 Fixed problem with auto-Timers
3.3.0 Added an option to choose whether to go to 
      standby on manual boot
3.3.1 Fixed problem when the global session was not
      available
3.3.2 Fixed some problems shutting down on latest
	  versions of enigma2.
3.3.3 Added patch to installer to fix enigma2. It 
	  should now be possible to run Elektro and 
	  EPG refresh in parallel.
3.3.4 Added Turkish locale by MytHoLoG	  
3.4.0 no shutdown if HDD not Idle (joergm6)  
3.4.1 Fix: Multi-Language (locale) does not work 
3.4.2 Enhance user interface (configuration menu)
3.4.3 2 Profiles; waiting for responding IP addresses
3.4.5 A NAS/server can be shutdown via Telnet

1) Prerequisites
----------------

Should work on most systems using Enigma2, but this 
isn't granted.
DM7025, DM800SE  + DM8000: Supported.
DM800: Can not wake up by itself. It therefore isn't
really supported.

2) Installation
---------------

If your Dreambox has Internet access, Elektro can be
installed using Plugin-Browser. Or using Addons, if 
it's a Blue Panel Image.

Else, simply copy the elektro*.ipk file to /tmp with
FTP (TCP/IP must be working already) or from an
USB stick using a Filebrowser.

Then install by "Install local extension" (Menu 
Setup Software management). 

Or by entering the following commands in a Telnet
session:

cd /
ipkg install /tmp/elektro*.ipk

To ensure proper operation of Elektro please "Restart"
(reboot) the Dreambox. 


3) Mode of operation    
--------------------
The Elektro Power Save Plugin puts the Dreambox from
Standby to sleep mode (Deep Standby) at specified times.
This only happens if the box is in Standby mode
and no recording is running or scheduled during the
next 20 minutes.

The Dreambox automatically wakes up for recordings or
at the end of the specified sleep time. Hence you needn't
wait for it to boot-up.

4) Options
----------
Main menu -> Extensions -> Elektro Power Save

 - Show in:
   Specify whether Elektro shall show up in plugin menu 
   or extensions menu (needs GUI restart).

 - Name:
   Specify plugin name to be used in menu (needs 
   GUI restart).

 - Description:
   Specify plugin description to be used in menu 
   (needs GUI restart).

 - Active Time profile
   The times of this profile will be used.

 - Use both profiles alternately
   Both profiles are used alternately. When
   shutting down the other profile is enabled.
   This allows two time cycles per day. Do not overlap the times.

 - Check IPs (press OK to edit)
   This list of IP addresses is checked. Elektro waits
   until addresses no longer responds to ping.

 - Enable Elektro Power Save
   Unless this is enabled, this plugin won't run 
   automatically.
   
 - Standby on boot:
   Puts the box in standby after boot.  
   
 - Standby on manual boot:
   Whether to put the box in standby when booted
   manually. On manual boot the box will not go to
   standby before the next deep standby interval
   starts, even if this option is set.
   This option is only active if 'Standby on boot'
   option is set, too.  
   
 - Standby on boot screen timeout:
   Specify how long to show the standby query on
   boot screen. This value can be set to ensure
   the box does not shut down to deep standby again
   too fast when in standby mode.
   
 - Force sleep (even when not in standby):
   Forces deep standby, even when not in standby mode.
   Scheduled recordings remain unaffected.
 
 - Avoid deep standby when HDD is active, e.g. for FTP:
   Wait for the HDD to enter sleep mode. Depending on
   the configuration this can prevent the box entirely
   from entering deep standby mode.
   
 - Dont wake up:
   Do not wake up at the end of next deep standby
   interval.
   
 - Holiday mode:
   The box always enters deep standby mode, except
   for recording.
   
 - Next day starts at and other times:
   If the box is supposed to enter deep standby
   e.g. monday night at 1 AM, it actually is already
   tuesday. To enable this anyway, differing next day
   start time can to be specified here.   
   Hopefully the rest is self-explanatory. 


======================================================
Have fun to let Elektro save power and preserve the 
environment on using your Dreambox!!!!
======================================================
