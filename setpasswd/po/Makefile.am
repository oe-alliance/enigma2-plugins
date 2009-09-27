INSTALLDIR = $(LIBDIR)/enigma2/python/Plugins/SystemPlugins/SetPasswd
DOMAIN=SetPasswd
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := ar ca cs da de el en es fi fr hr hu is it lt nl no pl pt ru sr sv tr
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: SetPasswd.pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/SetPasswd.mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po SetPasswd.pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
SetPasswd.pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d SetPasswd -s -o SetPasswd.pot ../src/*.py

	msguniq -o SetPasswduniq.pot SetPasswd.pot
	$(RM) SetPasswd.pot
	mv SetPasswduniq.pot SetPasswd.pot

.PHONY: SetPasswd.pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i SetPasswd.pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(INSTALLDIR)/po/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
