#!/bin/sh
for i in ??.po; do
    base=`basename "$i" .po`
    msgfmt --statistics "$i" -o "$base.mo"
done
