*******
CurlyTx
*******
Enigma2 (Dreambox) plugin that lets you view the contents of remote
*plain text* files, e.g. HTTP URLs.

Multiple URLs can be configured and navigated.

.. contents::
   :depth: 2


========
Features
========
- Load any remote plain text files, e.g. via HTTP
- Unlimited number of remote URLs/pages
- Reload pages
- Non-blocking URL loading
- Show HTTP headers
- Configurable page titles
- Configurable text size
- Configurable default page
- Import complete page list from Atom feed
- Visible in the main menu or the extension menu (configurable)
- Configurable menu title
- Help screen for main window and settings window


=====
Usage
=====

First run
=========
After installing CurlyTx and restarting Enigma2, open the main menu.
The first entry will be "CurlyTx" - activate it.

You will see the main window with the message
"Go and add a page in the settings".
Do just that end press the red button to access the settings window.

Now we'll add the first URL:

- Press the yellow button ("New"); the "page edit" window will show up
- Enter the page URL, e.g. http://ip.cweiske.de
- If you wish, enter a page title, e.g. "My IP"
- Set the text size if you want. 20 is a good default value.
- Press the green button ("OK"), and you are back on the settings window.
- The page you have just created is in the configuration list now.


If you made a mistake and want to change it, select the page with the
up/down buttons and press "OK" - the page edit window will open.

Press the green button and the settings will be saved.
You're back on the main window now and the URL you just configured will be loaded.


Adding many pages
=================
You can use the settings window to add new pages, but this gets tedious if you
want to add many pages.

It's better to use the Atom feed import in this case.
All you need is a text editor and a web server you can serve the feed page with.

Here is an example feed::

  <?xml version="1.0" encoding="utf-8"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <title>URL list for CurlyTx</title>
   <author>
    <name>Christian Weiske</name>
    <email>cweiske@cweiske.de</email>
   </author>
   <link rel="self" href="http://home.cweiske.de/pagefeed.atom"/>
   <entry>
    <id>ip</id>
    <title>My IP</title>
    <link rel="alternate" type="text/html" href="http://ip.cweiske.de/" />
   </entry>
   <entry>
    <id>temp</id>
    <title>House temperatures</title>
    <link rel="alternate" type="text/html" href="http://home/temperatures.txt" />
   </entry>
  </feed>

Start CurlyTx, go to the settings and write the feed URL in the
"Page feed URL" field.
Then press "OK" and the feed's pages will be loaded into the settings window.


=================
Modifying CurlyTx
=================


Translation
===========
Beginning a new translation
---------------------------
Replace ``$lang_code`` with your two-letter language code::

    $ cd po
    $ cp messages.po $lang_code.po
    ... edit $lang_code.po now
    $ ./compile.sh


Editing an existing translation
-------------------------------
Simply run ::

    $ cd po
    $ ./update.sh

This will update the translation template ``messages.pot`` from the source code
and will merge the changes into the single translation files.


Testing a translation
---------------------
Link your compiled translation file into ::

    src/locale/$lang_code/LC_MESSAGES/CurlyTx.mo

Enigma2 will pick it up automatically.


Building
========
First upgrade the version number in ``CONTROL/control``.

Then simply run ::

    ./build.sh

Directory ``releases/`` will contain the freshly baked ``.ipk`` file that can
then be transferred to your dreambox, e.g. via ``scp``::

    $ scp releases/enigma2-plugin-extensions-curlytx_2.3_mipsel.ipk dreambox:
    $ ssh dreambox
    $ ipkg install enigma2-plugin-extensions-curlytx_2.3_mipsel.ipk

You will need the ``ipkg-build`` script from
 http://reichholf.net/files/dreambox/tools/ipkg-build

Also see http://dream.reichholf.net/wiki/Howto:IPK_Pakete_erstellen


Open issues / ideas
===================
- move mode to re-order pages
- how to show clock in lcd?


=====
About
=====
Homepage
========
https://open-dreambox.org/trac/dreambox/wiki/CurlyTx

Author
======
Christian Weiske, `cweiske@cweiske.de`__

.. __: mailto:cweiske@cweiske.de

License
=======
The plugin is subject to the GPLv3_ or later.

Additional exception:
  This plugin may be distributed and executed on hardware which is licensed by
  Dream Multimedia GmbH.

.. _GPLv3: http://www.gnu.org/licenses/agpl.html
