#!/bin/sh

LINE="--------------------------------------"
PLUGINNAME="EPG-Backup"
PLUGINDIR="/usr/lib/enigma2/python/Plugins/Extensions/EPGRefresh"
PLUGINCONFPREFIX="config.plugins.epgrefresh"
SCRIPTNAME=`basename $0`
LOGPREFIX="[$PLUGINNAME-Script]"
SCRIPTEXEC="[ -x $PLUGINDIR/$SCRIPTNAME ] && $PLUGINDIR/$SCRIPTNAME"

# Options
BACKUPENABLED=`grep "$PLUGINCONFPREFIX.backup_enabled" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
VALIDSIZE=`grep "$PLUGINCONFPREFIX.filesize_valid" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
VALIDTIMESPAN=`grep "$PLUGINCONFPREFIX.timespan_valid" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
EPGWRITEWAIT=`grep "$PLUGINCONFPREFIX.epgwrite_wait" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
SHOWIN_USR_SCRIPTS=`grep "$PLUGINCONFPREFIX.showin_usr_scripts" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
BACKUP_STRATEGY=`grep "$PLUGINCONFPREFIX.backup_strategy" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
ENABLEDEUG=`grep "$PLUGINCONFPREFIX.backup_enable_debug" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
LOGPATH=`grep "$PLUGINCONFPREFIX.backup_log_dir" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
MAXBOOTCOUNT=`grep "$PLUGINCONFPREFIX.backup_max_boot_count" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
# defaults
BACKUPENABLED=${BACKUPENABLED:-true}
VALIDSIZE=${VALIDSIZE:-1024} # KB
VALIDTIMESPAN=${VALIDTIMESPAN:-7} # days
EPGWRITEWAIT=${EPGWRITEWAIT:-3} # seconds
SHOWIN_USR_SCRIPTS=${SHOWIN_USR_SCRIPTS:-true}
BACKUP_STRATEGY=${BACKUP_STRATEGY:-biggest}
ENABLEDEUG=${ENABLEDEUG:-false}
LOGPATH=${LOGPATH:-/media/hdd}
MAXBOOTCOUNT=${MAXBOOTCOUNT:-3}

# standard and/or Merlin?
EPGPATH=`grep "config.misc.epgcache_filename" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/" | sed -e "s/\/epg\.dat$//"`
if [ -z "$EPGPATH" ]; then
  EPGPATH=`cat /etc/enigma2/gemini_plugin.conf 2> /dev/null | grep epgCacheDir | sed -e "s/^.*=\(.*\)\.*$/\1/"`
fi
EPGPATH=${EPGPATH:-/media/hdd} # fallback
EPGFILE=$EPGPATH/epg.dat

# Constants
FORCEPREFIX="FORCE"
BACKUPFILEPREFIX="epg_"
BOOTCOUNTERFILE="/tmp/.EPGBackup.boot.counter"

# patch enigma2 Vars
patchcomment="# $PLUGINNAME-Patch"
# Searchstring in patched File
PATCHIDENTIFIER="$SCRIPTNAME"
PATCHFILE="/usr/bin/enigma2.sh"
PATCHFILENAME=`basename $PATCHFILE`
patchline="$SCRIPTEXEC backup"
lineRet="ret=\$?"

if [ `echo "$ENABLEDEUG" | tr [:upper:] [:lower:]` == "true" ] ; then
  debug="true"
  logfile=$LOGPATH/EPGBackup.log.`date +%Y%m%d`
else
  # always log the current run
  logfile=/tmp/EPGBackup.log
fi

housekeeping () {
  find "$EPGPATH" -mtime +"$VALIDTIMESPAN" -name "$BACKUPFILEPREFIX*.dat" -exec rm {} \;
  if [ -d "$LOGPATH" ]; then
    find "$LOGPATH" -mtime +"$VALIDTIMESPAN" -name "EPGBackup.log*" -exec rm {} \;
  fi
}

echologprefix () {
  echo -n "$LOGPREFIX [`date +%Y%m%d_%H%M%S`] "
}

printVars () {
  echo "Variables:"
  echo -e "Backup enabled: $BACKUPENABLED"
  echo -e "Valid Size: $VALIDSIZE"
  echo -e "Valid Timespan: $VALIDTIMESPAN"
  echo -e "EPG writetime: $EPGWRITEWAIT"
  echo -e "Backup-Strategy: $BACKUP_STRATEGY"
  echo -e "Maximal Bootcount: $MAXBOOTCOUNT"
  echo -e "Debug: $ENABLEDEUG"
  echo -e "Logpath: $LOGPATH"
  echo -e "EPG-Path: $EPGPATH"
  echo "$LINE"
}

makeBackup () {
  if [ `echo "$BACKUPENABLED" | tr [:upper:] [:lower:]` != "true" ] ; then
    echologprefix; echo "Backup/Restore is disabled!"
    return
  fi
  echologprefix; echo "Backuping ..."
  [ -n "$debug" ] && printVars
  
  if [ -f "$EPGFILE" ]; then
    # Wait until the filesize didn't change
    trycount=0
    let filesizeold=`ls -lr "$EPGFILE" | tr -s " " | cut -d " " -f 5 | head -n1`
    while [ $trycount -le $EPGWRITEWAIT ]
    do
      sleep 1
      let EPGFILESIZE=`ls -lr "$EPGFILE" | tr -s " " | cut -d " " -f 5 | head -n1`
      if [ $EPGFILESIZE -eq $filesizeold ]; then
        trycount=`expr $trycount + 1`
      else
        trycount=0
      fi
      filesizeold=$EPGFILESIZE
    done
    
    if [ "$EPGFILESIZE" -gt "$VALIDSIZE" ]; then
      EPGbackup="$BACKUPFILEPREFIX`date +%Y%m%d_%H%M`.dat"
      echologprefix; echo "making Backup $EPGbackup ($EPGFILESIZE Kb)"
      cp "$EPGFILE" "$EPGPATH/$EPGbackup"
    else
      echologprefix; echo "Epg-File too small for Backup ($EPGFILESIZE Kb)"
    fi
  else
    echologprefix; echo "No Epg-File found at $EPGPATH"
  fi
}

_restore () {
  success="false"
  
  local  __resultvar=$2

  if [ -f "$EPGFILE" ]; then
    let EPGFILESIZE=`ls -lr "$EPGFILE" | tr -s " " | cut -d " " -f 5 | head -n1`
  else
    EPGFILESIZE=0
  fi
  
  EPGbackup=`ls $EPGPATH/${FORCEPREFIX}$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1`
  if [ -f "$EPGbackup" ]; then
    echologprefix; echo "Forced restoring from `basename $EPGbackup`"
    cp -f "$EPGbackup" "$EPGFILE"
    rm -f $EPGbackup
    success="true"
  else
    if [ "$1" == "biggest" ]; then
      EPGbackupInfo=`ls -lS $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " "`
    else
      EPGbackupInfo=`ls -lt $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " "`
    fi  
    EPGbackup=`echo $EPGbackupInfo | cut -d " " -f 9`

    if [ -f "$EPGbackup" ]; then
      let BACKUPSIZE=`echo $EPGbackupInfo | cut -d " " -f 5`
      if [ $BACKUPSIZE -gt $EPGFILESIZE ]; then
        echologprefix; echo "Restoring from `basename $EPGbackup`"
        cp -f "$EPGbackup" "$EPGFILE"
        success="true"
      else
        [ -n "$debug" ] && echo "`basename $EPGbackup` too small or equal: $BACKUPSIZE bytes"
        [ -n "$debug" ] && echo "Size of existing Epg-File: $EPGFILESIZE bytes"
      fi
    fi
  fi
  
  eval $__resultvar="'$success'"
}

_incrementBootCounter () {
  local  __resultvar=$1
  
  count=`cat $BOOTCOUNTERFILE 2> /dev/null` 
  count=${count:-0}
  
  count=`expr $count + 1`
  echo "$count" > $BOOTCOUNTERFILE
  
  eval $__resultvar="'$count'"
}

restore () {
  if [ `echo "$BACKUPENABLED" | tr [:upper:] [:lower:]` != "true" ] ; then
    echologprefix; echo "Backup/Restore is disabled!"
    return
  fi
  echologprefix; echo "Restoring ..."
  [ -n "$debug" ] && printVars
  
  _incrementBootCounter aktbootcount
  
  if [ "$aktbootcount" -gt "$MAXBOOTCOUNT" ]; then
    echologprefix; echo "Maximum Boot-Count reached: Deleting EPG-File!"
    rm -f $EPGFILE 2> /dev/null
    return
  fi
  
  if [ "$BACKUP_STRATEGY" == "biggest" ]; then
    _restore "biggest" success
    if [ "$success" == "false" ]; then
      _restore "youngest" success
    fi
  else
    _restore "youngest" success
    if [ "$success" == "false" ]; then
      _restore "biggest" success
    fi
  fi
  if [ "$success" == "false" ]; then
    echologprefix; echo "No valid Backup found!"
  fi
}

epgInfo () {
  if [ "$1" == "bySize" ]; then
    files=`ls -S $EPGPATH/$BACKUPFILEPREFIX*.dat`
  else
    files=`ls -t $EPGPATH/$BACKUPFILEPREFIX*.dat`
  fi
  biggest=`ls -lS $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " " | cut -d " " -f 9`
  biggest=`basename $biggest`
  youngest=`ls -t $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " " | cut -d " " -f 9`
  youngest=`basename $youngest`
  forced=`ls $EPGPATH/${FORCEPREFIX}$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1`
  if [ -n "$forced" ]; then
    forced=`basename $forced`
    forced=`echo $forced | cut -c 6-`
  fi
  for aktFile in $files; do
    aktFile=`echo "$aktFile" | tr -s " " | cut -d " " -f 9`
    size=`du -ha $aktFile | cut -f 1`
    aktFile=`basename $aktFile`
    
    if [ "$aktFile" == "$forced" ]; then
      forcextend=" (force)"
    else
      forcextend=""
    fi
    
    if [ "$aktFile" == "$youngest" ]; then
      youngextend=" (youngest)"
    else
      youngextend=""
    fi
    
    if [ "$aktFile" == "$biggest" ]; then
      bigextend=" (biggest)"
    else
      bigextend=""
    fi
    
    echo -e "$aktFile   $size$forcextend$youngextend$bigextend"
  done
}

setforcefile () {
  forcefile="$1"
  
  rm -f $EPGPATH/$FORCEPREFIX*.dat 2> /dev/null
  if [ -f "$EPGPATH/$forcefile" ]; then
    ln -s $EPGPATH/$forcefile $EPGPATH/$FORCEPREFIX$forcefile
  fi
  
}

ispachted () {
  if grep -qs $PATCHIDENTIFIER $PATCHFILE ; then
    echo -n "true"
  else
    echo -n "false"
  fi
}

info () {
  echo "$LINE"
  printVars
  
  echo -n "$LOGPREFIX $PATCHFILENAME is "
  if grep -qs $PATCHIDENTIFIER $PATCHFILE ; then
    echo "patched"
  else
    echo "NOT patched"
  fi
  
  helpfile="/etc/rc3.d/S20$SCRIPTNAME"
  echo -n "$LOGPREFIX Patcher-File $helpfile "
  if [ -e "$helpfile" ] ; then
    echo "exists"
  else
    echo "doesn't exists"
  fi
  
  helpfile="/usr/bin/enigma2_pre_start20epgrestore.sh"
  echo -n "$LOGPREFIX Enigma-pre-hook-File $helpfile "
  if [ -e "$helpfile" ] ; then
    echo "exists"
  else
    echo "doesn't exists"
  fi
  echo "$LINE"
}

installit () {
  echo $LINE
  if [ ! -e "$PATCHFILE" ] ; then
    echo "$LOGPREFIX no $PATCHFILENAME found"
    return
  fi
  
  if grep -qs $PATCHIDENTIFIER $PATCHFILE ; then
    echo "$LOGPREFIX $PATCHFILENAME already patched"
  else
    if [ "$1" = "auto" -a `echo "$BACKUPENABLED" | tr [:upper:] [:lower:]` != "true" ] ; then
      echologprefix; echo "Backup/Restore is disabled! Won't (re)-install EPG-Backup"
      return
    fi
    
  	echo "$LOGPREFIX patching $PATCHFILENAME (Enigma-Restart will be needed)"
    patchedfile="/tmp/${PATCHFILENAME}.patched"
    patchlines=`cat $PATCHFILE | grep -n "^[[:space:]]*PAGECACHE_FLUSH_INTERVAL"`
    rm -f $patchedfile 2> /dev/null
    firstloop="true"
    addRetAssignment="false"
    headoffset=0
    tailoffset=1
    while [ -n "$patchlines" ]; do
      aktpatchline=`echo "$patchlines" | head -n 1`
      patchoffset=`echo $aktpatchline | cut -d: -f1`
      if [ -n "$firstloop" ]; then
        head -n $patchoffset $PATCHFILE >> $patchedfile
      
        # check if there is already a Return-Value-Assignment, or add it
        nextoffset=`expr $patchoffset + 1`
        nextline=`sed -n ${nextoffset}p $PATCHFILE`
        if [ `echo $nextline | grep -nc "^[[:space:]]*ret="` -eq 0 ]; then
          addRetAssignment="true"
          patchline="ret=\$?\n$patchline"
        else
          echo -e "$nextline" >> $patchedfile
          headoffset=1
          tailoffset=2
        fi
      fi
    
      echo -e "$patchcomment begin" >> $patchedfile
      echo -e "$patchline" >> $patchedfile
      echo -e "$patchcomment end" >> $patchedfile

      if [ `echo "$patchlines" | wc -l` -gt 1 ]; then
        # Add text between akt-Line and next patchline
        nextpatchoffset=`echo "$patchlines" | tail -n +2`
        nextpatchoffset=`echo "$nextpatchoffset" | head -n 1 | cut -d: -f1`
        head -n `expr $nextpatchoffset + $headoffset` $PATCHFILE > "/tmp/${PATCHFILENAME}.lines"
        tail -n +`expr $patchoffset + $tailoffset` "/tmp/${PATCHFILENAME}.lines" > "/tmp/${PATCHFILENAME}.lines2"
        cat "/tmp/${PATCHFILENAME}.lines2" >> $patchedfile
        rm -f /tmp/${PATCHFILENAME}.lines*
      else
        tail -n +`expr $patchoffset + $tailoffset` $PATCHFILE >> $patchedfile
      fi
      
      patchlines=`echo "$patchlines" | tail -n +2`
      firstloop=""
    done
    
    # Remove Enigma-Return-Value - Assignment: it was placed directly after enigma-call by the previous patch
    if [ "$addRetAssignment" == "true" ]; then
      cp $patchedfile ${patchedfile}2
      patchline=`cat ${patchedfile}2 | grep -w "ret=\$\?" | tail -1`
      patchoffset=`cat ${patchedfile}2 | grep -wn "ret=\$\?" | cut -d: -f1 | tail -1`
      patchoffset=`expr $patchoffset - 1`
      head -n $patchoffset ${patchedfile}2 > $patchedfile
      echo -e "$patchcomment begin" >> $patchedfile
      echo "$patchcomment original $patchline" >> $patchedfile
      echo -e "$patchcomment end" >> $patchedfile
      patchoffset=`expr $patchoffset + 2`
      tail -n +$patchoffset ${patchedfile}2 >> $patchedfile
      rm ${patchedfile}2
    else
      # If the Original - Assignment is still removed, 
      # but the other patch will be "uninstalled" before this patch 
      # then add a dummy-Patch-Comment for a "Patch-Remove" of this patch in future
      
      cp $patchedfile ${patchedfile}2
      aktpatchline=`cat ${patchedfile}2 | grep -n '^[[:space:]]*case \$ret in' | tail -1`
      patchline=`echo $aktpatchline | cut -d: -f2`
      patchoffset=`echo $aktpatchline | cut -d: -f1`
      patchoffset=`expr $patchoffset - 1`
      head -n $patchoffset ${patchedfile}2 > $patchedfile
      echo -e "$patchcomment begin" >> $patchedfile
      echo -e "$patchcomment original $lineRet" >> $patchedfile
      echo -e "$patchcomment end" >> $patchedfile
      patchoffset=`expr $patchoffset + 1`
      tail -n +$patchoffset ${patchedfile}2 >> $patchedfile
      rm ${patchedfile}2
    fi
    
    if [ -d /hdd ] ; then
      bakDestination=/hdd/${PATCHFILENAME}.before_patch.${PLUGINNAME}
    else
      bakDestination=/tmp/${PATCHFILENAME}.before_patch.${PLUGINNAME}
    fi
    echo "$LOGPREFIX copying $PATCHFILENAME to $bakDestination"
    cp -p $PATCHFILE $bakDestination
    chmod 755 $patchedfile
    mv -f $patchedfile $PATCHFILE
  fi
  
  # patcher after updates
  helpfile="/etc/rc3.d/S20$SCRIPTNAME"
  if [ ! -e "$helpfile" ] ; then
    echo "$LOGPREFIX creating patcher '$helpfile'"
    echo -e "#!/bin/sh" > $helpfile
    echo -e "\n$SCRIPTEXEC install" >> $helpfile
    echo -e "exit 0" >> $helpfile
    chmod 755 $helpfile
  fi
 
  # enigma2.sh - hook
  helpfile="/usr/bin/enigma2_pre_start20epgrestore.sh"
  if [ ! -e "$helpfile" ] ; then
    echo "$LOGPREFIX creating enigma-pre-hook '$helpfile'"
    echo -e "#!/bin/sh" > $helpfile
    echo -e "\n$SCRIPTEXEC restore" >> $helpfile
    echo -e "exit 0" >> $helpfile
    chmod 755 $helpfile
  fi
  
  # if there is an Oozoon(like)-Image: enable it in user-scripts
  if [ -d "/usr/script/" ] ; then
    echo "$LOGPREFIX enable $PLUGINNAME in User-Scripts: $SHOWIN_USR_SCRIPTS"
    if [ `echo "$SHOWIN_USR_SCRIPTS" | tr [:upper:] [:lower:]` == "true" ] ; then
      ln -sfn $PLUGINDIR/$SCRIPTNAME /usr/script/
    else
      rm /usr/script/$SCRIPTNAME > /dev/null 2>&1
    fi
  fi
  echo $LINE
}

uninstall(){
  echo $LINE
  if [ ! -e "$PATCHFILE" ] ; then
    echo "$LOGPREFIX no $PATCHFILENAME found"
    return
  fi
  
  if grep -qs $PATCHIDENTIFIER $PATCHFILE ; then
    echo "$LOGPREFIX restoring $PATCHFILENAME (Enigma-Restart will be needed)"
    
    patchedfile="/tmp/${PATCHFILENAME}.patched"
    patchedfilecopy="/tmp/${PATCHFILENAME}.patched2"
    cp $PATCHFILE $patchedfilecopy
    patchlines=`cat $patchedfilecopy | grep -wn "$patchcomment"`
    while [ -n "$patchlines" ]; do
      aktpatchline=`echo "$patchlines" | head -n 1`
      if [ `echo "$aktpatchline" | grep "$patchcomment begin" | wc -l` -gt 0 ] ; then
        patchoffset=`echo $aktpatchline | cut -d: -f1`
        head -n `expr $patchoffset - 1` $patchedfilecopy > $patchedfile
        patchlines=`echo "$patchlines" | tail -n +2`
      elif [ `echo "$aktpatchline" | grep "$patchcomment original" | wc -l` -gt 0 ] ; then
        patchline=`echo $aktpatchline | cut -d: -f2`
        patchline=`echo "$patchline" | sed -e "s/$patchcomment original//"`
        patchline=`echo "$patchline" | sed -e "s/^ //"`
        patchlines=`echo "$patchlines" | tail -n +2`
      else
        patchoffset=`echo $aktpatchline | cut -d: -f1`
        tail -n +`expr $patchoffset + 1` $patchedfilecopy >> $patchedfile
        cp $patchedfile $patchedfilecopy
        patchlines=`cat $patchedfilecopy | grep -wn "$patchcomment"`
      fi
    done
    rm -f $patchedfilecopy
    chmod 755 $patchedfile
    mv -f $patchedfile $PATCHFILE
  else
    echo "$LOGPREFIX $PATCHFILENAME not patched"
  fi

  # patcher after updates
  helpfile="/etc/rc3.d/S20$SCRIPTNAME"
  echo "$LOGPREFIX remove '$helpfile'"
  rm -f $helpfile 2> /dev/null
  
  # enigma2.sh - hook
  helpfile="/usr/bin/enigma2_pre_start20epgrestore.sh"
  echo "$LOGPREFIX remove '$helpfile'"
  rm -f $helpfile > /dev/null 2>&1
  
  if [ -d "/usr/script/" ] ; then
    echo "$LOGPREFIX remove $PLUGINNAME from User-Scripts"
    rm -f /usr/script/$SCRIPTNAME > /dev/null 2>&1
  fi
  echo $LINE
}

if [ "$1" != "epginfo" -a "$1" != "ispatched" ]; then
  [ -n "$debug" ] || echo "$LOGPREFIX Action: $*"
  [ -n "$debug" ] && echo "$LOGPREFIX [`date +%Y%m%d_%H%M%S`] Action: $*"
fi
case "$1" in
     epginfo)
        epgInfo "$2"
        ;;
     backup|b)
        echo "Output will be append to $logfile"
        exec >> $logfile 2>&1
        echo $LINE
        housekeeping
        makeBackup
        exit 0
        ;;
     restore|r)
        echo "Output will be append to $logfile"
        exec >> $logfile 2>&1
        echo $LINE
        housekeeping
        restore
        exit 0
        ;;
     setforcefile)
        setforcefile "$2"
        ;;
     ispatched)
        ispachted
        ;;
     info)
        info
        ;;
     autoinstall)
        echo "Output will be append to $logfile"
        exec >> $logfile 2>&1
        installit "auto"
        ;;
     install)
        installit
        ;;
     uninstall)
        uninstall
        ;;
     *)
        echo "Usage: $0 epginfo|backup|restore|setforcefile|info|install|uninstall"
        exit 1
        ;;
esac

exit 0
