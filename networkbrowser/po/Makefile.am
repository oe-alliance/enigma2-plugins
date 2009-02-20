INSTALLDIR = $(LIBDIR)/enigma2/python/Plugins/SystemPlugins/NetworkBrowser
DOMAIN=NetworkBrowser
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := de en ar nl es is it da sv no fr fi tr ca cs hr hu ru pt el lt pl
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: NetworkBrowser.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/NetworkBrowser.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po NetworkBrowser.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
NetworkBrowser.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d NetworkBrowser -s -o NetworkBrowser.pot ../src/*.py

	msguniq -o NetworkBrowseruniq.pot NetworkBrowser.pot
	$(RM) NetworkBrowser.pot
	mv NetworkBrowseruniq.pot NetworkBrowser.pot

.PHONY: NetworkBrowser.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i NetworkBrowser.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
