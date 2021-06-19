#!/bin/sh

# Script by Persian Prince for https://github.com/OpenVisionE2
# You're not allowed to remove my copyright or reuse this script without putting this header.

setup_git() {
  git config --global user.email "bot@enigma2-plugins.com"
  git config --global user.name "enigma2-plugins python bot"
}

commit_files() {
  git clean -fd
  rm -rf *.pyc
  rm -rf *.pyo
  rm -rf *.mo
  git checkout python3
  ./CI/chmod.sh
  ./CI/dos2unix.sh
  ./CI/PEP8.sh
}

upload_files() {
  git remote add upstream https://${GITHUB_TOKEN}@github.com/oe-alliance/enigma2-plugins.git > /dev/null 2>&1
  git push --quiet upstream python3 || echo "failed to push with error $?"
}

setup_git
commit_files
upload_files
