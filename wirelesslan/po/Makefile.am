INSTALLDIR = $(LIBDIR)/enigma2/python/Plugins/SystemPlugins/WirelessLan
DOMAIN=WirelessLan
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := de en ar nl es is it da sv no fr fi fy tr ca cs hr hu ru pt el lt pl sr
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: WirelessLan.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/WirelessLan.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po WirelessLan.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
WirelessLan.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d WirelessLan -s -o WirelessLan.pot ../src/*.py

	msguniq -o WirelessLanuniq.pot WirelessLan.pot
	$(RM) WirelessLan.pot
	mv WirelessLanuniq.pot WirelessLan.pot

.PHONY: WirelessLan.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i WirelessLan.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
