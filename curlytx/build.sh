#!/bin/sh
[ -d tmp ] && rm -r tmp

extdir=usr/lib/enigma2/python/Plugins/Extensions/CurlyTx
mkdir -p tmp/$extdir/locale/
cp -R CONTROL tmp/

for i in po/??.mo; do
    lang=`basename "$i" .mo`
    mkdir -p tmp/$extdir/locale/$lang/LC_MESSAGES
    cp "$i" tmp/$extdir/locale/$lang/LC_MESSAGES/CurlyTx.mo
done
cp po/messages.pot tmp/$extdir/locale/CurlyTx.pot

python -O -m compileall src/ -f
cp src/*.py tmp/$extdir/
cp src/*.pyo tmp/$extdir/

ipkg-build tmp/
rm -r tmp

[ ! -d releases ] && mkdir releases
mv enigma2-plugin-extensions-curlytx_*_mipsel.ipk releases/
