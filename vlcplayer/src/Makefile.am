if HAVE_E2_INCLUDES
SUBDIRS = servicets
endif

installdir = /usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer

if HAVE_E2_INCLUDES
install_PYTHON = *.py servicets/servicets.so
else
install_PYTHON = *.py servicets.so
endif

install_DATA = *.png maintainer.info
