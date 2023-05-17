#!/bin/bash
# Script to generate po files outside of the normal build process
#
# Pre-requisite:
# The following tools must be installed on your system and accessible from path
# find, xgettext, sed/gsed, python/python3, msguniq, msgmerge, msgattrib, msgfmt
#
# xml2po.py in this folder is also needed
#
# Run this script in the root folder of this repo.
# Each package needs a po and src folder
#
# Example usage
# ./updatepot.sh -p epgrefresh -n EPGRefresh
#
# Author: jbleyel
# Version: 2.0
#
# partly based of the script by Pr2

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
PACKAGEFOLDERSRC="./$packagefolder/src/"
PACKAGECONTROL="./$packagefolder/CONTROL/control"
PACKAGEVERSION="1.1"
PACKAGEDESCRIPION="SOME DESCRIPTIVE TITLE."
CURRENT=$(pwd) &> /dev/null

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

if [ ! -d "$PACKAGEFOLDERSRC" ]; then
	echo "Directory ${PACKAGEFOLDERSRC} DOES NOT exists."
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
	"$localgsed" --version 2> /dev/null | grep -q "GNU"
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
printf "Creating temporary file $PACKAGEFOLDER-py.pot\n"
pushd $PACKAGEFOLDERSRC
find $findoptions . -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $PACKAGENAME -s -o $PACKAGENAME-py.pot --package-name=$PACKAGENAME --package-version=$PACKAGEVERSION {} \+
$localgsed --in-place $PACKAGENAME-py.pot --expression='s/CHARSET/UTF-8/g'
$localgsed --in-place $PACKAGENAME-py.pot --expression='s/SOME DESCRIPTIVE TITLE./$PACKAGEDESCRIPION/g'
printf "Creating temporary file enigma2-xml.pot\n"
which python
if [ $? -eq 0 ]; then
	find $findoptions . -name "setup.xml" -exec python $CURRENT/xml2po.py {} \+ > $PACKAGENAME-xml.pot
else
	find $findoptions . -name "setup.xml" -exec python3 $CURRENT/xml2po.py {} \+ > $PACKAGENAME-xml.pot
fi
printf "Merging pot files to create: $PACKAGENAME.pot\n"
cat $PACKAGENAME-py.pot $PACKAGENAME-xml.pot | msguniq -s --no-wrap -o ../po/$PACKAGENAME.pot -
printf "remove temp pot files\n"
rm $PACKAGENAME-py.pot $PACKAGENAME-xml.pot
printf "pot update from script finished!\n"
popd
pushd $PACKAGEFOLDERPO
languages=($(ls *.po | tr "\n" " " | $localgsed 's/.po//g'))
for lang in "${languages[@]}" ; do
	msgmerge --backup=none --no-wrap -s -U $lang.po $PACKAGENAME.pot && touch $lang.po
	msgattrib --no-wrap --no-obsolete $lang.po -o $lang.po
done
popd
