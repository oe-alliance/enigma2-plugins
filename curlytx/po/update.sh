#!/bin/sh
xgettext -kT_ -L Python ../src/*.py
mv messages.po messages.pot

for i in ??.po; do
    msgmerge --update --backup=off "$i" messages.pot
done
