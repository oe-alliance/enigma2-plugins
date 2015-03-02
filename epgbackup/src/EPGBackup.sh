#!/bin/sh

LINE="--------------------------------------"
PLUGINNAME="EPGBackup"
PLUGINDIR="/usr/lib/enigma2/python/Plugins/Extensions/EPGBackup"
PLUGINCONFPREFIX="config.plugins.epgbackup"
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
MAKE_BACKUP_AFTER_UNSUCCESS_RESTORE=`grep "$PLUGINCONFPREFIX.make_backup_after_unsuccess_restore" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
ENABLEDEUG=`grep "$PLUGINCONFPREFIX.enable_debug" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
LOGPATH=`grep "$PLUGINCONFPREFIX.backup_log_dir" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
MAXBOOTCOUNT=`grep "$PLUGINCONFPREFIX.max_boot_count" /etc/enigma2/settings | sed -e "s/^.*=\(.*\)\.*$/\1/"`
# defaults
BACKUPENABLED=${BACKUPENABLED:-true}
VALIDSIZE=${VALIDSIZE:-3} # MiB
VALIDSIZE=$(($VALIDSIZE*1024)) # KiB
VALIDSIZE=$(($VALIDSIZE*1024)) # Bytes
VALIDTIMESPAN=${VALIDTIMESPAN:-7} # days
EPGWRITEWAIT=${EPGWRITEWAIT:-3} # seconds
SHOWIN_USR_SCRIPTS=${SHOWIN_USR_SCRIPTS:-true}
BACKUP_STRATEGY=${BACKUP_STRATEGY:-youngest_before_biggest}
MAKE_BACKUP_AFTER_UNSUCCESS_RESTORE=${MAKE_BACKUP_AFTER_UNSUCCESS_RESTORE:-true}
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
LASTRESTOREDFILE="/tmp/.EPGBackup.lastfile.restored"
LASTBACKUPEDFILE="/tmp/.EPGBackup.lastfile.backuped"
OUTERRORTXTFILE="/tmp/.EPGBackup.outerrortxt"

if [ `echo "$ENABLEDEUG" | tr [:upper:] [:lower:]` == "true" ] ; then
  debug="true"
  logfile=$LOGPATH/EPGBackup.log.`date +%Y%m%d`
else
  # always log the current run, but make sure that the file doesn't become to big
  logfile=/tmp/EPGBackup.log
  echo -n "" > $logfile
fi

getVersion () {
  if [ -n "$debug" ] ; then
    vers=`grep -iE ".*version[[:space:]]*=[[:space:]]*\"[0-9]*" $PLUGINDIR/EPGBackupTools.py`
    vers=`echo "$vers" | sed -e "s/^.*=[[:space:]]*\"\(.*\)\"*$/\1/"`
    vers=`echo "$vers" | sed -e "s/\"//"`
    echo -n " V$vers"
  fi
}

echologprefix () {
  echo -n "$LOGPREFIX [`date +'%Y%m%d %H:%M:%S'``getVersion`] "
}

housekeeping () {
  if [ "$1" != "nolog" ]; then
    echologprefix; echo "housekeeping..."
    hkDebug="$debug"
  fi
  
  if [ "$VALIDTIMESPAN" == 1 ]; then
    [ -n "$hkDebug" ] && find "$EPGPATH" -mtime 1 -name "$BACKUPFILEPREFIX*.dat"
    find "$EPGPATH" -mtime 1 -name "$BACKUPFILEPREFIX*.dat" -exec rm {} \;
    if [ -d "$LOGPATH" ]; then
      [ -n "$hkDebug" ] && find "$LOGPATH" -mtime 1 -name "EPGBackup.log*"
      find "$LOGPATH" -mtime 1 -name "EPGBackup.log*" -exec rm {} \;
    fi
    # maybe there are older files than 1 day, so also delete them
    localTimespan=1
  else
    localTimespan=$(($VALIDTIMESPAN-1))
  fi
  [ -n "$hkDebug" ] && find "$EPGPATH" -mtime +"$localTimespan" -name "$BACKUPFILEPREFIX*.dat"
  find "$EPGPATH" -mtime +"$localTimespan" -name "$BACKUPFILEPREFIX*.dat" -exec rm {} \;
  if [ -d "$LOGPATH" ]; then
    [ -n "$hkDebug" ] && find "$LOGPATH" -mtime +"$localTimespan" -name "EPGBackup.log*"
    find "$LOGPATH" -mtime +"$localTimespan" -name "EPGBackup.log*" -exec rm {} \;
  fi
}

printVars () {
  echo "$LINE"
  echo "Variables:"
  echo -e "Backup enabled: $BACKUPENABLED"
  echo -e "Make backup after unsuccessfully restore: $MAKE_BACKUP_AFTER_UNSUCCESS_RESTORE"
  echo -e "Valid Size: $VALIDSIZE Bytes"
  echo -e "Valid Timespan: $VALIDTIMESPAN"
  echo -e "EPG writetime: $EPGWRITEWAIT"
  echo -e "Backup-Strategy: $BACKUP_STRATEGY"
  echo -e "Maximal Bootcount: $MAXBOOTCOUNT"
  echo -e "Debug: $ENABLEDEUG"
  echo -e "Logpath: $LOGPATH"
  echo -e "EPG-Path: $EPGPATH"
  echo "$LINE"
}

getLastFileInfo () {
  fileInfo=""
  if [ "$1" == "backup" ]; then
    [ -e $LASTBACKUPEDFILE ] && fileInfo=`cat $LASTBACKUPEDFILE`
  elif [ "$1" == "error" ]; then
    [ -e $OUTERRORTXTFILE ] && fileInfo=`cat $OUTERRORTXTFILE`
  else
    [ -e $LASTRESTOREDFILE ] && fileInfo=`cat $LASTRESTOREDFILE`
  fi
  
  echo -n "$fileInfo"
}

makeBackup () {
  rm -f $LASTBACKUPEDFILE 2> /dev/null
  if [ `echo "$BACKUPENABLED" | tr [:upper:] [:lower:]` != "true" ] ; then
    echologprefix; echo "Backup/Restore is disabled2!"
    OUTERRORTEXT="BACKUP_RESTORE_DISABLED"
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
      echologprefix; echo "making Backup $EPGbackup ($(($EPGFILESIZE / 1024)) KiB)"
      cp "$EPGFILE" "$EPGPATH/$EPGbackup"
      echo "$EPGPATH/$EPGbackup" > $LASTBACKUPEDFILE 2> /dev/null
    else
      echologprefix; echo "Epg-File too small for Backup ($(($EPGFILESIZE / 1024)) KiB)"
      OUTERRORTEXT="BACKUP_EPGFILE_TOO_SMALL#$(($EPGFILESIZE / 1024)) KiB#$(($VALIDSIZE / 1024)) KiB"
    fi
  else
    echologprefix; echo "No Epg-File found at $EPGPATH"
    OUTERRORTEXT="BACKUP_NO_EPGFILE_FOUND#$EPGPATH"
  fi
}

_restore () {
  success="false"
  
  local __resultvar=$2

  if [ -f "$EPGFILE" ]; then
    let EPGFILESIZE=`ls -lr "$EPGFILE" | tr -s " " | cut -d " " -f 5 | head -n1`
  else
    EPGFILESIZE=0
  fi
  
  wasForced="false"
  if [ "$3" != "" ]; then
    EPGbackup=`ls $EPGPATH/$3 2> /dev/null | head -n1`
  else
    # maybe there's a forced-file
    EPGbackup=`ls $EPGPATH/${FORCEPREFIX}$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1`
    wasForced="true"
  fi
  if [ -f "$EPGbackup" ]; then
    echologprefix; echo "Forced restoring from `basename $EPGbackup`"
    cp -f "$EPGbackup" "$EPGFILE"
    [ "$wasForced" == "true" ] && rm -f $EPGbackup
    success="true"
  else
    if [ "$1" == "biggest" ]; then
      EPGbackupInfo=`ls -leS $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " "`
    else
      EPGbackupInfo=`ls -let $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " "`
    fi  
    EPGbackup=`echo $EPGbackupInfo | cut -d " " -f 11`

    if [ -f "$EPGbackup" ]; then
      if [ "$1" == "biggest" ]; then
        let BACKUPSIZE=`echo $EPGbackupInfo | cut -d " " -f 5`
        if [ ! -f "$EPGFILE" -o $BACKUPSIZE -gt $EPGFILESIZE ]; then
          echologprefix; echo "Restoring from `basename $EPGbackup`"
          cp -f "$EPGbackup" "$EPGFILE"
          success="true"
        else
          echologprefix; echo "`basename $EPGbackup` smaller or equal: $(($BACKUPSIZE / 1024)) KiB --> no restoring!"
          echologprefix; echo "Size of existing Epg-File: $(($EPGFILESIZE / 1024)) KiB"
          OUTERRORTEXT="RESTORE_BACKUPFILE_SMALLER#$(($BACKUPSIZE / 1024)) KiB#$(($EPGFILESIZE / 1024)) KiB"
        fi
      else
        # youngest
        if [ ! -f "$EPGFILE" -o "$EPGbackup" -nt "$EPGFILE" ]; then
          echologprefix; echo "Restoring from `basename $EPGbackup`"
          cp -f "$EPGbackup" "$EPGFILE"
          success="true"
        else
          if [ -n "$debug" ]; then
            BACKUPAGE=`echo $EPGbackupInfo | cut -d " " -f 7-10`
            EPGFILEAGE=`ls -ler "$EPGFILE" | tr -s " " | cut -d " " -f 7-10 | head -n1`
            echologprefix; echo "`basename $EPGbackup` older or equal: $BACKUPAGE --> no restoring!"
            echologprefix; echo "Modify-Date of Epg-File: $EPGFILEAGE"
            OUTERRORTEXT="RESTORE_BACKUPFILE_OLDER#$BACKUPAGE#$EPGFILEAGE"
          fi
        fi
      fi
    fi
  fi
  
  [ "$success" == "true" ] && echo "$EPGbackup" > $LASTRESTOREDFILE 2> /dev/null
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

_isValidFile () {
  valid="false"
  checkFile="$1"
  local  __resultvar=$2
  
  if [ -f "$checkFile" ]; then
    ageOk=`find $(dirname "$checkFile") -mtime -"$VALIDTIMESPAN" -name $(basename "$checkFile") | wc -l`
    if [ "$ageOk" -gt 0 ] ; then
      FILEINFO=`ls -le "$checkFile" | tr -s " "`
      FILESIZE=`echo $FILEINFO | cut -d " " -f 5`
      FILESIZE=${FILESIZE:-0}
      if [ $VALIDSIZE -lt $FILESIZE ]; then
        valid="true"
      else
        [ -n "$debug" ] && echo "`basename $checkFile` hasn't a valid size: $(($FILESIZE / 1024)) KiB"
      fi
    else
      [ -n "$debug" ] && echo "`basename $checkFile` hasn't a valid age: `echo $FILEINFO | cut -d " " -f 7-10`"
    fi
  fi
  
  eval $__resultvar="'$valid'"
}

restore () {
  parambackupfile=$1
  rm -f $LASTRESTOREDFILE 2> /dev/null
  if [ `echo "$BACKUPENABLED" | tr [:upper:] [:lower:]` != "true" ] ; then
    echologprefix; echo "Backup/Restore is disabled!"
    OUTERRORTEXT="BACKUP_RESTORE_DISABLED"
    return
  fi
  echologprefix; echo "Restoring ..."
  [ -n "$debug" ] && printVars
  
  aktbootcount=0
  [ -n "$parambackupfile" ] || _incrementBootCounter aktbootcount
  
  if [ "$aktbootcount" -gt "$MAXBOOTCOUNT" ]; then
    echologprefix; echo "Maximum Boot-Count reached: Deleting EPG-File!"
    OUTERRORTEXT="RESTORE_MAXBOOTCOUNT_REACHED"
    rm -f $EPGFILE 2> /dev/null
    return
  fi
  
  case "$BACKUP_STRATEGY" in
    biggest_before_youngest|biggest)
      _restore "biggest" success $parambackupfile
      if [ "$BACKUP_STRATEGY" == "biggest_before_youngest" -a "$success" == "false" ]; then
        _isValidFile $EPGFILE isValid
        if [ "$isValid" == "false" ] ; then
          echologprefix; echo "Trying fallback - strategy youngest!"
          _restore "youngest" success
        else
          # keep the state unsuccessfully, maybe make a backup later
          echologprefix; echo "Original epg.dat is valid, fallback - strategy not needed!"
          OUTERRORTEXT="RESTORE_ORIGINALFILE_VALID"
        fi
      fi
      ;;
    youngest_before_biggest|youngest)
      _restore "youngest" success $parambackupfile
      if [ "$BACKUP_STRATEGY" == "youngest_before_biggest" -a "$success" == "false" ]; then
        _isValidFile $EPGFILE isValid
        if [ "$isValid" == "false" ] ; then
          echologprefix; echo "Trying fallback - strategy biggest!"
          _restore "biggest" success
        else
          # keep the state unsuccessfully, maybe make a backup later
          echologprefix; echo "Original epg.dat is valid, fallback - strategy not needed!"
          OUTERRORTEXT="RESTORE_ORIGINALFILE_VALID"
        fi
      fi
  esac 
  
  if [ "$success" == "false" ]; then
    echologprefix; echo "No valid Backup found for restore, or restore not needed!"
    if [ `echo "$MAKE_BACKUP_AFTER_UNSUCCESS_RESTORE" | tr [:upper:] [:lower:]` == "true" ]; then
      echologprefix; echo "Trying to make a Backup of current epg.dat!"
      makeBackup
    fi
  fi
}

epgInfo () {
  if [ "$1" == "bySize" ]; then
    files=`ls -S $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null`
  else
    files=`ls -t $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null`
  fi
  biggest=`ls -lS $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " " | cut -d " " -f 9`
  [ -n "$biggest" ] && biggest=`basename $biggest`
  youngest=`ls -t $EPGPATH/$BACKUPFILEPREFIX*.dat 2> /dev/null | head -n1 | tr -s " " | cut -d " " -f 9`
  [ -n "$youngest" ] && youngest=`basename $youngest`
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

prestartfile="/usr/bin/enigma2_pre_start20epgrestore.sh"
info () {
  echo "$LINE"
  printVars
  
  echo -n "$LOGPREFIX Enigma-pre-hook-File $prestartfile "
  if [ -e "$prestartfile" ] ; then
    echo "exists"
  else
    echo "doesn't exists"
  fi
  echo "$LINE"
}

installit () {
  echo $LINE

  # enigma2.sh - hook
  if [ ! -e "$prestartfile" ] ; then
    echo "$LOGPREFIX creating enigma-pre-hook '$prestartfile'"
    echo -e "#!/bin/sh" > $prestartfile
    echo -e "\n$SCRIPTEXEC restore" >> $prestartfile
    echo -e "exit 0" >> $prestartfile
    chmod 755 $prestartfile
  else
    echo "$LOGPREFIX $prestartfile exists"
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
  # enigma2.sh - hook
  echo "$LOGPREFIX remove '$prestartfile'"
  rm -f $prestartfile > /dev/null 2>&1
  
  if [ -d "/usr/script/" ] ; then
    echo "$LOGPREFIX remove $PLUGINNAME from User-Scripts"
    rm -f /usr/script/$SCRIPTNAME > /dev/null 2>&1
  fi
  echo $LINE
}

if [ "$1" != "epginfo" -a "$1" != "getlastfile"  ]; then
  [ -n "$debug" ] || echo "$LOGPREFIX Action: $*"
  [ -n "$debug" ] && echo "$LOGPREFIX [`date +%Y%m%d_%H%M%S``getVersion`] Action: $*"
fi
case "$1" in
     epginfo)
        housekeeping "nolog"
        epgInfo "$2"
        ;;
     getlastfile)
        getLastFileInfo "$2"
        ;;
     backup|b)
        errorHandling=TRUE
        echo "Output will be append to $logfile"
        exec >> $logfile 2>&1
        echo $LINE
        housekeeping
        makeBackup
        ;;
     restore|r)
        errorHandling=TRUE
        echo "Output will be append to $logfile"
        exec >> $logfile 2>&1
        echo $LINE
        [ -z "$2" ] && housekeeping
        restore $2
        ;;
     setforcefile)
        errorHandling=TRUE
        setforcefile "$2"
        ;;
     info)
        info
        ;;
     install)
        SHOWIN_USR_SCRIPTS=${2:-$SHOWIN_USR_SCRIPTS}
        installit
        ;;
     housekeeping)
        [ -n "$debug" ] && printVars
        housekeeping
        ;;
     uninstall)
        uninstall
        ;;
     *)
        echo "Usage: $0 b|backup|r|restore|epginfo|getlastfile|setforcefile|housekeeping|info|install|uninstall"
        exit 1
        ;;
esac

if [ -n "$errorHandling" ] ; then
  rm -f $OUTERRORTXTFILE 2> /dev/null
  if [ -n "$OUTERRORTEXT" ] ; then
    echo "$OUTERRORTEXT" > $OUTERRORTXTFILE
  fi
fi

exit 0
