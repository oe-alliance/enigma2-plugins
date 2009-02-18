installdir = /usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer
DOMAIN=VlcPlayer
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := de es it tr
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: VlcPlayer.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/VlcPlayer.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po VlcPlayer.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
VlcPlayer.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d VlcPlayer -s -o VlcPlayer.pot ../src/*.py
	msguniq -o VlcPlayeruniq.pot VlcPlayer.pot
	$(RM) VlcPlayer.pot
	mv VlcPlayeruniq.pot VlcPlayer.pot

.PHONY: VlcPlayer.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i VlcPlayer.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
