MovieCut-1.4
------------
2012-02-26
Anders Holst (aho@sics.se)


This module makes it possible to execute the cuts specified by the
Cutlist editor in enigma2, i.e. the specified sections are actually
removed from the file, saving disk space and simplifying if the movie
is to be e.g. burned to a DVD. When installed it will be accessible
from the file list menu (i.e. selecting a file in the file list and
pressing the menu button) under the name "Execute cuts...". First use
the Cutlist editor to set the appropriate cut marks. Then select 
"Execute cuts..." and it will give some options for usage.

The real work is done by the program "mcut". It was inspired and
guided by the similar package "moviecutter" bu Georges. However, you
need not wait over the night but it can run in the background as you
keep watching on your dreambox, and a typical movie takes about 15-20
minutes to process. The program "mcut" can also be called directly
from a shell. With no arguments it will give a brief description of
the options.


News since version 1.3

* Language support added (thanks, Thorsten Manthei). Initially only
  with german and swedish, but more translations will hopefully
  follow.

* Minor bug-fixes.


News since version 1.2

* The same mcut program can now cut movies on both DM7025 and
  DM800/DM8000, and both normal and HD movies. There may still be some
  flickering at the cut points, especially on DM800/DM8000, but rather
  limited.

(* There is a driver change on DM7025 that makes movies cut with the
   old mcut program (1.2 and earlier) to show much more flickering at
   the cut points than before. Therefore you should change to he new
   version, 1.3, even if you have only a DM7025 and thus no HD movies.)

* The mcut program now cuts the new .sc files too (making precise fast
  forward and rewind possible), and copies the .eit as well (making
  the info button work on cut movies).

* Some code cleanup.


News since version 1.1

* Nothing really is supposed to have changed functionally. However,
  the plugin is updated to the skin changes of 2008-04-14, and the
  location changes of 2008-06-28, and it uses eConsoleAppContainer
  instead of spawnv/waitpid to launch "mcut".


News since version 1.0

* Cutting is still in the background, but now a notification will pop
  up either when cutting is successfully finished, or with a suitable
  error message if cutting fails.

* The cutting can now be done quite exact: If all cut marks are placed
  at GOP boundaries (singlestep GOPs by pausing and pressing either
  "rewind" or with the appropriate settings "pause"), then the
  retained part will start with the same frame you were at when you
  placed the IN cut, and it will stop just a few frames before
  (typically 3 frames before - I can't easily get rid of this) the one
  where you placed the OUT cut. Note however that due to a bug in
  enigma2 (still there 2008-02-28) the CutListEditor will set the mark
  at the right place, but when revisiting the mark you will end up one
  GOP later. Trust the original mark position, not where it seems to
  be when jumping to it.

* There are no flickering between cuts any more! There is a small (3
  frames long) pause before the next cut starts, but all flickering
  and squares seem to be gone. I believe this is as good as it can get
  without remuxing.


Caveats

* The manual specification of cuts in the "advanced cut parameter"
  dialogue is as awkward as before to specify with the remote control:
  "0" is mapped to ".","0", and ":" since this was most
  straightforward to implement using existing python code. Also note
  that the cuts are given in pairs of *included* sections, not
  *excluded* as in the cutlist editor (i.e. there is first an IN time,
  followed by OUT, and so on).

* There may still be occasional flickering at the cut points, at least
  on some platforms and for some services. It is hard to do much
  better without remuxing.


Disclaimer

I have really tried to be careful and make it reasonably "safe": It
checks for errors during the process and will abort in a controlled
way if it happens; If "-r"="replace" is specified, it will not remove
any files until the whole cutting is successfully done; if "-r" is not
given it will not overwrite any existing file with the same name as the
destination; if no cuts are specified nothing will be done; etc.

However, all use will be on your own risk. I will not take
responsibility for any damage or loss of movies or other files due to
either bugs in the program or uncareful use. 

