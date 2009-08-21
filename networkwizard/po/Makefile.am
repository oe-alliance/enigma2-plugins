INSTALLDIR = $(LIBDIR)/enigma2/python/Plugins/SystemPlugins/NetworkWizard
DOMAIN=NetworkWizard
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := de en ar nl es is it da sv no fr fi tr ca cs hr hu ru pt el lt pl fy sr
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: NetworkWizard.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/NetworkWizard.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po NetworkWizard.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
NetworkWizard.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d NetworkWizard -s -o NetworkWizard.pot ../src/*.py

	../../xml2po.py ../src/ >> NetworkWizard.pot

	msguniq -o NetworkWizarduniq.pot NetworkWizard.pot
	$(RM) NetworkWizard.pot
	mv NetworkWizarduniq.pot NetworkWizard.pot

.PHONY: NetworkWizard.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i NetworkWizard.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
