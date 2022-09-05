PACKAGE=enigma2-plugin-extensions-series2folder
SOURCES=__init__.py plugin.py FileScreens.py
OBJECTS=__init__.pyo plugin.pyo FileScreens.pyo
CONTROL=CONTROL
INSTALL-PATH=usr/lib/enigma2/python/Plugins/Extensions/Series2Folder
BUILD-DIR=build
MKDIR=mkdir
CP=cp
SCP=scp
SSH=ssh
IPKG-BUILD=../ipkg-build
BUILD-HOST=beyonwizv2

package: clean
	${MKDIR} -p ${BUILD-DIR}/${INSTALL-PATH}
	${SCP} ${BUILD-HOST}:/${INSTALL-PATH}/*.py[co] ${BUILD-DIR}/${INSTALL-PATH}
	${CP} -r ${CONTROL} ${BUILD-DIR}/${CONTROL}
	${IPKG-BUILD} build

push:
	${SSH} ${BUILD-HOST} ${MKDIR} -p /${INSTALL-PATH}
	${SCP} ${SOURCES} ${BUILD-HOST}:/${INSTALL-PATH}

dist-clean: clean clean-host

clean:
	rm -rf ${PACKAGE}*.ipk build

clean-host:
	${SSH} ${BUILD-HOST} ${RM} -r /${INSTALL-PATH}
