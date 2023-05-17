#!/bin/bash
# Script to generate po files outside of the normal build process
#  
# Pre-requisite:
# The following tools must be installed on your system and accessible from path
# gawk, find, xgettext, sed, python, msguniq, msgmerge, msgattrib, msgfmt, msginit
#
# Run this script from within the po folder.
#
# Author: Pr2 for OpenPLi Team
# Version: 1.1
#
# Author: jbleyel
# Version: 1.2
#

while getopts p:n: flag
do
    case "${flag}" in
        p) packagefolder=${OPTARG};;
        n) packagename=${OPTARG};;
    esac
done

PACKAGENAME=$packagename
PACKAGEFOLDER="./$packagefolder"
PACKAGEFOLDERPO="./$packagefolder/po/"
PACKAGECONTROL="./$packagefolder/CONTROL/control"
PACKAGEVERSION="1.1"
PACKAGEDESCRIPION="SOME DESCRIPTIVE TITLE."


if [[ $PACKAGEFOLDER == "./" ]]; then
	echo "missing parameter -p packagefolder"
	exit 1
fi

if [[ $PACKAGENAME == "" ]]; then
	echo "missing packagename -n packagename"
	exit 1
fi

if [ ! -d "$PACKAGEFOLDER" ]; then
	echo "Directory ${PACKAGEFOLDER} DOES NOT exists."
	exit 1
fi

if [ ! -d "$PACKAGEFOLDERPO" ]; then
	echo "Directory ${PACKAGEFOLDERPO} DOES NOT exists."
	exit 1
fi

#if test -f "$PACKAGECONTROL"; then
#	echo "Directory ${PACKAGECONTROL} DOES NOT exists."
#	exit 1
#fi

localgsed="sed"
findoptions=""

#
# Script only run with sed but on some distro normal sed is already sed so checking it.
#
sed --version 2> /dev/null | grep -q "GNU"
if [ $? -eq 0 ]; then
	localgsed="sed"
else
	"$localgsed" --version | grep -q "GNU"
	if [ $? -eq 0 ]; then
		printf "GNU sed found: [%s]\n" $localgsed
	fi
fi

which python
if [ $? -eq 1 ]; then
	which python3
	if [ $? -eq 1 ]; then
		printf "python not found on this system, please install it first or ensure that it is in the PATH variable.\n"
		exit 1
	fi
fi

which xgettext
if [ $? -eq 1 ]; then
	printf "xgettext not found on this system, please install it first or ensure that it is in the PATH variable.\n"
	exit 1
fi


#
# On Mac OSX find option are specific
#
if [[ "$OSTYPE" == "darwin"* ]]
	then
		# Mac OSX
		printf "Script running on Mac OSX [%s]\n" "$OSTYPE"
    	findoptions=" -s -X "
        localgsed="gsed"
fi

#
# Arguments to generate the pot and po files are not retrieved from the Makefile.
# So if parameters are changed in Makefile please report the same changes in this script.
#
printf "Creating temporary file $PACKAGEFOLDER-py.pot\n"
find $findoptions $PACKAGEFOLDER -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $PACKAGENAME -s -o $PACKAGENAME-py.pot --package-name=$PACKAGENAME --package-version=$PACKAGEVERSION {} \+
$localgsed --in-place $PACKAGENAME-py.pot --expression=s/CHARSET/UTF-8/
$localgsed --in-place $PACKAGENAME-py.pot --expression=s/SOME DESCRIPTIVE TITLE./$PACKAGEDESCRIPION
printf "Creating temporary file enigma2-xml.pot\n"
which python
if [ $? -eq 0 ]; then
	find $findoptions $PACKAGEFOLDER -name "setup.xml" -exec python xml2po.py {} \+ > $PACKAGENAME-xml.pot
else
	find $findoptions $PACKAGEFOLDER -name "setup.xml" -exec python3 xml2po.py {} \+ > $PACKAGENAME-xml.pot
fi
printf "Merging pot files to create: $PACKAGENAME.pot\n"
cat $PACKAGENAME-py.pot $PACKAGENAME-xml.pot | msguniq -s --no-wrap --no-location -o $PACKAGENAME.pot -
cp -f $PACKAGEFOLDERPO$PACKAGENAME.pot $PACKAGENAME-old.pot
cp -f $PACKAGENAME.pot $PACKAGENAME-new.pot
$localgsed -i -e'/POT-Creation/d' $PACKAGENAME-old.pot
$localgsed -i -e'/POT-Creation/d' $PACKAGENAME-new.pot
DIFF=$(diff $PACKAGENAME-old.pot $PACKAGENAME-new.pot)
if [ "$DIFF" != "" ] 
then
	mv -f $PACKAGENAME.pot $PACKAGEFOLDERPO$PACKAGENAME.pot
fi
printf "remove temp pot files\n"
rm $PACKAGENAME-py.pot $PACKAGENAME-xml.pot $PACKAGENAME-old.pot $PACKAGENAME-new.pot $PACKAGENAME.pot
printf "pot update from script finished!\n"

pushd $PACKAGEFOLDERPO
languages=($(ls *.po | tr "\n" " " | gsed 's/.po//g'))
for lang in "${languages[@]}" ; do
	msgmerge --backup=none --no-wrap --no-location -s -U $lang.po $PACKAGENAME.pot && touch $lang.po
	msgattrib --no-wrap --no-obsolete $lang.po -o $lang.po
done
popd