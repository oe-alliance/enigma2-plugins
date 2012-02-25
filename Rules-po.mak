CATEGORY ?= "Extensions"

plugindir = $(libdir)/enigma2/python/Plugins/$(CATEGORY)/$(PLUGIN)

LANGMO = $(LANGS:=.mo)
LANGPO = $(LANGS:=.po)

BUILT_SOURCES = $(LANGMO)
CLEANFILES = $(LANGMO)

if UPDATE_PO
# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
$(PLUGIN)-py.pot: $(srcdir)/../src/*.py
	$(XGETTEXT) -L python --from-code=UTF-8 --add-comments="TRANSLATORS:" -d $(PLUGIN) -s -o $@ $^

$(PLUGIN)-xml.pot: $(top_srcdir)/xml2po.py $(srcdir)/../src/*.xml
	$(PYTHON) $^ > $@

$(PLUGIN).pot: $(PLUGIN)-py.pot $(PLUGIN)-xml.pot
	cat $^ | $(MSGUNIQ) --no-location -o $@ -

%.po: $(PLUGIN).pot
	if [ -f $@ ]; then \
		$(MSGMERGE) --backup=none --no-location -s -N -U $@ $< && touch $@; \
	else \
		$(MSGINIT) -l $@ -o $@ -i $< --no-translator; \
	fi

CLEANFILES += $(PLUGIN)-py.pot $(PLUGIN)-xml.pot $(PLUGIN).pot
endif

.po.mo:
	$(MSGFMT) -o $@ $<

dist-hook: $(LANGPO)

install-data-local: $(LANGMO)
	for lang in $(LANGS); do \
		$(mkinstalldirs) $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES; \
		$(INSTALL_DATA) $$lang.mo $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES/$(PLUGIN).mo; \
	done

uninstall-local:
	for lang in $(LANGS); do \
		$(RM) $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES/$(PLUGIN).mo; \
	done
