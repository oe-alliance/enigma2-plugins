TuxCom:

History:
---------
08.04.2007 Version 1.16
 - single window view selectable (toggle with info-button)
 - show file sizes in "human readable" (MB/GB) form (can be set in main menu)
 - filesize in bytes is shown in file properties (button "1")

30.10.2006 Version 1.15
 - possibility to execute scripts depending on file extension
 - two small fixes (thanks to murks)

06.03.2006 Version 1.14
 - use /tmp/keyboard.lck to signal decoding of the keyboard (by robspr1)

22.01.2006 Version 1.13
 - overwrite directory corrected

27.12.2005 Version 1.12
 - portugese translation added (thanks to jlmota)
 - two little bugfixes in editor
 
22.11.2005 Version 1.11
 - better keyboard handling when using Exit/Enter on DMM-Keyboard
 - small bugs fixed in editor
 - less memory usage 
 - file /tmp/tuxcom.out is deleted when exiting plugin

01.10.2005 Version 1.10a
 - numbers on USB-Keyboard now working again

24.09.2005 Version 1.10
 - link to files in read-only directories creatable
 - check for existing files when creating directory

11.09.2005 Version 1.9a
 - added swedish language support (thanks to yeager)

10.08.2005 Version 1.9
 - support of dbox2-keyboards integrate (by robspr)

15.07.2005 Version 1.8a
 - added italian language support (thanks to fbrassin)

11.06.2005 Version 1.8
 - direct jump into root-directory possible (select entry '/')
 - more file information in rights-dialogue
 - pressing OK at a file which is not executable opens viewer
 - new created file/directory is automatically selected
 - bugfix: sometimes \n was removed when editing a line

12.01.2005 Version 1.7
 - some colors changed
 - bugfix: crash when entering text in last line in editor
 - no automatic saving settings when leaving plugin (set in main menu)
 - select language in main menu (for Neutrino, as automatic detection does not work there)
 - new functionality in editor: mark/copy/move/delete multiple lines (as in Midnight-Commander)

10.10.2004 Version 1.6
 - bugfix: wrong text in clipboard
 - new main menu (dream-button)
 - new feature: search for files (in main menu)
 - Editing of .ftp-files with own mask
 - bugfix: correct selected file after renaming
 - bugfix: under certain circumstances the last character was cut off in textinput
 - textcolor black on yellow background
 - bugfix: change rights of file with red button now possible
 
22.09.2004 Version 1.5a
 - bugfix: crash in editor / after closing editor
 - bugfix: crash when moving (button 6) a single file

30.08.2004 Version 1.5
 - password protection included (Button Info -> Blue)
 - possibility to rename file when copying or moving
 - display error in taskmanager corrected
 - bugfixes in Editor
 - display error in properties corrected
 - cancel of FTP-Download possible (and restart at current position, if supported by server)
 - bugfixes in FTP-Client
 
26.08.2004 Version 1.4b
 - Textinput: possibility to mark (green button) and insert text (blue button) (kind of a mini-clipboard :-) )
 - Editor: display \r as white box (DOS/Win-textfile) (blue button -> convert to linux-format)
 - FTP-client: remove whitspace characters at end of filename when downloading
 - FTP-client: improved download-speed
 
11.08.2004 Version 1.4a
 - support of usb-keyboards (needs kernel-module hid.ko from BoxMan)
 - read .ftp-files even when created by windows
 - BugFix: inserting new line in empty file in editor
 - minor bugfixes in Editor
 - many bugfixes in ftp-client
 - changes in keyboard routine
 - BugFix: wrong display after pressing red button (clear) while editing
 - BugFix: crash when leaving plugin with open ftp-connection

25.07.2004 Version 1.4
 - Taskmanager added (on Info-Button)
 - scrolling back/forward possible when executing commands or scripts
 - scrolling back/forward in viewer not limited to 100k anymore
 - remember current selected file on plugin exit
 - Support for DMM-Keyboard installed
 - delay for pressed button 
 - Bugfix: workaround for button-press bug from enigma
 - create link (Button 0): display current filename as name.
 
21.06.2004 Version 1.3
 - FTP-Client added
 - minor bugfixes in editor
 - text input: jumping to next character when pressing another Number.
 - text input: removing last character when at end of line and pressing volume-
 - toggle between 4:3 and 16:9-mode with dream-button
 - Viewer:scrolling possible as in editor (for files up to 100k size)

05.06.2004 Version 1.2a
 - BugFix: missing characters in text input added.
 - text input in "sms-style" included

29.05.2004 Version 1.2
 - support for reading and extracting from "tar", "tar.Z", "tar.gz" and "tar.bz2" archives
   does not work with many Archives in Original-Image 1.07.4 ( BusyBox-Version to old :( )
 - display current line in editor
 - using tuxtxt-position for display
 - big font when editing a line
 - change scrolling through characters in edit mode to match enigma standard (switch up/down)
 - Version of plugin available on Info-Button
 - confirm-messagebox when overwriting existing files.

08.05.2004 Version 1.1a
 - BugFix: No more spaces at the end of renamed files

02.05.2004 version 1.1
 - changed some colors
 - added german language
 - possibility to keep buttons pressed (up/down, left/right, volume+/-, green button)
 - 3 states of transparency
 - set markers on files -> possibility to copy/move/delete multiple files
 - Key for transparency now mute (green button needed for setting file marker)
  
03.04.2004 version 1.0 : 
   first public version



Keys:
---------------

left/right		choose left/right window
up/down			select prev/next entry in current window
volume -/+		one page up/down in current window
ok			execute selected file / change dir in current window / open archive for reading
1			view/edit properties (rights) of selected file 
2			rename selected file 
3			view selected file 
4			edit selected file 
5			copy selected file from current window to other window
6			move selected file from current window to other window
7			create new directory in current window
8			delete selected file 
9			create new file in current window
0			create symbolic link to selected file in current window in directory of other window	
red			enter linux command
green			toggle file marker
yellow			toggle sorting of entries in current window
blue			refresh display
mute			toggle transparency
dream			main menu
info			toggle single window view

in messageboxes:

left/right		change selection
ok			confirm selection
red/green/yellow	change selection

in textinput:

left/right		change selected stringposition
up/down			change character
ok			confirm changes
volume +		insert new character
volume -		remove character
red			clear input
green			enter marking mode
yellow			change between uppercase/lowercase
blue			insert text from clipboard
0..9			select character in "sms-style" (as in enigma textinput)

in marking mode:

left/right		change selected stringposition
ok			copy marked text in clipboard
exit			return to normal edit mode

in properties:

up/down			change selection
ok			toggle right 
red			confirm selection
green			cancel selection

in Editor:

left/right		Page back/forward
up/down 		Line up/down
ok			edit line
volume +		jump to first line
volume -		jump to last line
red			delete line
green			insert line
blue			convert DOS/Win-textfile to linux format
3			start/stop marking mode
5			copy marked rows
6			move marked rows
8			delete marked rows

in Viewer:

ok/right		view next page
left/right		Page back/forward
up/down 		Line up/down
volume +		jump to first line
volume -		jump to last line

in Taskmanager:

ok/right		view next page
left/right		Page back/forward
up/down 		Line up/down
volume +		jump to first line
volume -		jump to last line
red			kill process

in Searchresult:

left/right		Page back/forward
up/down 		Line up/down
volume +		jump to first line
volume -		jump to last line
ok			navigate to file

in main menu:

up/down 		select menu item
left/right		change setting
ok			choose menu item

in all dialogs: 

exit			exit dialog



colors:
------------
background: 
black : directory is readonly
blue  : directory is read/write

filename:
white : entry is directory
orange: entry is link
yellow: entry is executable
gray  : entry is writable
green : entry is readable


Using the FTP-Client:
-----------------------
1.) create file with ending .ftp
2.) edit this file:
possible entries:
host=<ftp-adress>	(required, e.g.: host=ftp.gnu.org)
user=<username> 	(optional)
pass=<password> 	(optional)
port=<ftpport>  	(optional, default 21)
dir=<directory>		(optional, default /)
3.) select file and press OK . 
you are connected to the specified adress.

buttons for usb-keyboard:
-------------------------
exit			Esc
volume+/-	PgUp/PgDn
OK				Enter
red				F5
green			F6
yellow			F7
blue			F8
dream			F9
info			F10
mute			F11


buttons for dbox2-keyboard:
---------------------------
home			Esc
volume+/-	PgUp/PgDn
OK				Enter
red				F1
green			F2
yellow			F3
blue			F4
dbox			F5
?				F6
mute			F7

If you want to put in a number with the dbox2-keyboard directly,
you have to press the number-key together with the ALT-key.
You get the special characters at the number-keys (²³{[]}\), if you press ALTGR and the number-key.


use of password protection:
---------------------------
if you have entered a password (in main menu),
you will be asked for the password after starting the plugin.
you can remove the password protection by simply setting an empty password.
if you have forgotten your password, you can reset it by deleting /etc/tuxbox/tuxcom.conf.

