#!/bin/sh

echo ""
echo "futurize safe cleanup by Persian Prince"
# Script by Persian Prince for https://github.com/OpenVisionE2
# You're not allowed to remove my copyright or reuse this script without putting this header.
echo ""
echo "Changing py files, please wait ..." 
begin=$(date +"%s")

echo ""
echo "Convert python 2 print to python 3 print"
find . -name "*.py" -type f -exec futurize -w -f libfuturize.fixes.fix_print_with_import {} \;
find . -name "*.bak" -type f -exec rm -rf {} \;
git add -u
git add *
git commit -m "Use futurize to have python 3 compatible print"

echo ""
echo "Convert python 2 long to python 3 int"
find . -name "*.py" -type f -exec futurize -w -f lib2to3.fixes.fix_long {} \;
find . -name "*.bak" -type f -exec rm -rf {} \;
git add -u
git add *
git commit -m "Use futurize to have python 3 compatible int instead of long"

echo ""
echo "Convert python 2 idioms to python 3 idioms"
find . -name "*.py" -type f -exec futurize -w -f lib2to3.fixes.fix_idioms {} \;
find . -name "*.bak" -type f -exec rm -rf {} \;
git add -u
git add *
git commit -m "Use futurize to have python 3 compatible idioms"

echo ""
echo "Convert python 2 has_key to python 3 compatible code"
find . -name "*.py" -type f -exec futurize -w -f lib2to3.fixes.fix_has_key {} \;
find . -name "*.bak" -type f -exec rm -rf {} \;
git add -u
git add *
git commit -m "Use futurize to fix has_key"

echo ""
echo "Convert python 2 except to python 3 except"
find . -name "*.py" -type f -exec futurize -w -f lib2to3.fixes.fix_except {} \;
find . -name "*.bak" -type f -exec rm -rf {} \;
git add -u
git add *
git commit -m "Use futurize to have python 3 compatible except"

echo ""
finish=$(date +"%s")
timediff=$(($finish-$begin))
echo -e "Change time was $(($timediff / 60)) minutes and $(($timediff % 60)) seconds."
echo -e "Fast changing would be less than 5 minutes."
echo ""
echo "futurize Done!"
echo ""
