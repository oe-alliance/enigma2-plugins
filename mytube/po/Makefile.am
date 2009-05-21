INSTALLDIR = $(LIBDIR)/enigma2/python/Plugins/Extensions/MyTube
DOMAIN=MyTube
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := de en ar nl es is it da sv no fr fi tr ca cs hr hu ru pt el lt pl fy
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: MyTube.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/MyTube.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po MyTube.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
MyTube.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d MyTube -s -o MyTube.pot ../src/*.py

	../../xml2po.py ../src/ >> MyTube.pot

	msguniq -o MyTubeuniq.pot MyTube.pot
	$(RM) MyTube.pot
	mv MyTubeuniq.pot MyTube.pot

.PHONY: MyTube.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i MyTube.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
