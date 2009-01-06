INSTALLDIR = $(LIBDIR)/enigma2/python/Plugins/Extensions/WebInterface
DOMAIN=WebInterface
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := de
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: WebInterface.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/WebInterface.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po WebInterface.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
WebInterface.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d WebInterface -s -o WebInterface.pot ../src/*.py

	msguniq -o WebInterfaceuniq.pot WebInterface.pot
	$(RM) WebInterface.pot
	mv WebInterfaceuniq.pot WebInterface.pot

.PHONY: WebInterface.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i WebInterface.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
