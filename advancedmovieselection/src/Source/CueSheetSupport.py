import os
import struct
from Components.config import config
from Screens.InfoBarGenerics import InfoBarCueSheetSupport
from shutil import copyfile
from bisect import insort
from Globals import printStackTrace


def hasLastPosition(service):
    file_name = service.getPath() + '.cuts'
    cuts_file = None
    if not os.path.exists(file_name):
        return False
    try:
        cuts_file = open(file_name, 'rb')
        while 1:
            data = cuts_file.read(12)
            if data == '':
                break
            what = struct.unpack('>I', data[8:12])[0]
            if what == InfoBarCueSheetSupport.CUT_TYPE_LAST:
                return True

    except:
        pass
    finally:
        if cuts_file is not None:
            cuts_file.close()

    return False


def checkDVDCuts(fileName):
    cuts_file = None
    cut_list = []
    if not os.path.exists(fileName + '.cuts'):
        return False
    try:
        cuts_file = open(fileName + '.cuts', 'rb')
        while 1:
            data = cuts_file.read(12)
            if data == '':
                break
            where = struct.unpack('>Q', data[0:8])[0]
            what = struct.unpack('>I', data[8:12])[0]
            print("%s %s" % (what, where))
            cut_list.append((where, what))
            title = struct.unpack('<i', cuts_file.read(4))[0:4][0]
            chapter = struct.unpack('<i', cuts_file.read(4))[0:4][0]
            block = struct.unpack('<I', cuts_file.read(4))[0:4][0]
            audio_id = struct.unpack('<i', cuts_file.read(4))[0:4][0]
            audio_lock = struct.unpack('<i', cuts_file.read(4))[0:4][0]
            spu_id = struct.unpack('<i', cuts_file.read(4))[0:4][0]
            spu_lock = struct.unpack('<i', cuts_file.read(4))[0:4][0]
            what = struct.unpack('>i', cuts_file.read(4))[0:4][0]
            print('py_resume_pos: resume_info.title=%d, chapter=%d, block=%d, audio_id=%d, audio_lock=%d, spu_id=%d, spu_lock=%d  (pts=%d)' % (title,
             chapter,
             block,
             audio_id,
             audio_lock,
             spu_id,
             spu_lock,
             what))
            if what == 4:
                return True

    except:
        printStackTrace()
    finally:
        if cuts_file is not None:
            cuts_file.close()

    return False


class CueSheet:

    def __init__(self, serviceref):
        self.serviceref = serviceref

    def __call__(self):
        return self

    def getCutList(self):
        cuts = None
        cut_list = []
        file_name = self.serviceref.getPath() + '.cuts'
        if not os.path.exists(file_name):
            return cut_list
        try:
            cuts = open(file_name, 'rb')
            while 1:
                data = cuts.read(12)
                if data == '':
                    break
                where = struct.unpack('>Q', data[0:8])[0]
                what = struct.unpack('>I', data[8:12])[0]
                cut_list.append((long(where), what))

        except:
            print('ERROR reading cutlist %s' % file_name)
            printStackTrace()
        finally:
            if cuts is not None:
                cuts.close()

        return cut_list

    def setCutList(self, cut_list):
        cuts = None
        try:
            file_name = self.serviceref.getPath() + '.cuts'
            cuts = open(file_name, 'wb')
            for where, what in cut_list:
                data = struct.pack('>Q', where)
                cuts.write(data)
                data = struct.pack('>I', what)
                cuts.write(data)

        except Exception as e:
            print('ERROR writing cutlist' % file_name)
            printStackTrace()
            return e
        finally:
            if cuts is not None:
                cuts.close()


class CutListSupportBase:

    def __init__(self, service):
        self.currentService = service
        self.cut_list = []
        self.resume_point = 0
        self.jump_first_mark = None
        self.jump_first_play_last = None
        self.currently_playing = False
        self.new_service_started = True

    def playNewService(self, service):
        if self.currentService == service:
            return
        self.new_service_started = True
        self.ENABLE_RESUME_SUPPORT = True
        self.playerClosed(service)
        self.currentService = service
        self.session.nav.playService(service)

    def getCuesheet(self):
        service = self.session.nav.getCurrentService()
        if service is None:
            return
        else:
            cue = service.cueSheet()
            if cue:
                return cue
            cue = CueSheet(self.currentService)
            self.session.nav.currentlyPlayingService.cueSheet = cue
            return cue

    def checkResumeSupport(self):
        self.jump_first_mark = None
        self.jump_first_play_last = None
        stop_before_end_time = int(config.AdvancedMovieSelection.stop_before_end_time.value)
        length, last = self.getCuePositions()
        if stop_before_end_time > 0:
            if (length - last) / 60 < stop_before_end_time or length < last:
                self.ENABLE_RESUME_SUPPORT = False
            else:
                self.ENABLE_RESUME_SUPPORT = True
        if config.AdvancedMovieSelection.jump_first_mark.value is True:
            first = self.getFirstMark()
            if first and length > 0 and first / 90000 < length / 2:
                self.jump_first_play_last = first
                if not hasLastPosition(self.currentService):
                    self.ENABLE_RESUME_SUPPORT = False
                    self.jump_first_mark = self.resume_point = first

    def getFirstMark(self):
        firstMark = None
        for pts, what in self.cut_list:
            if what == self.CUT_TYPE_MARK:
                if not firstMark:
                    firstMark = pts
                elif pts < firstMark:
                    firstMark = pts

        return firstMark

    def downloadCuesheet(self):
        try:
            if not self.new_service_started:
                print('cancel cue download, no new service started!!!')
                self.ENABLE_RESUME_SUPPORT = False
                return
            self.new_service_started = False
            self.currently_playing = True
            cue = self.getCuesheet()
            if cue is None:
                print('download failed, no cuesheet interface! Try to load from cuts')
                self.cut_list = []
                if self.currentService is not None:
                    self.cut_list = CueSheet(self.currentService).getCutList()
            else:
                self.cut_list = cue.getCutList()
            self.checkResumeSupport()
            if self.jump_first_mark:
                self.doSeek(self.resume_point)
        except Exception as e:
            print('DownloadCutList exception:\n' + str(e))

    def modifyCutListEnries(self):
        seek = self.session.nav.getCurrentService().seek()
        if seek is None:
            return
        stopPosition = seek.getPlayPosition()[1]
        length = seek.getLength()[1]
        if stopPosition > length:
            stopPosition = 0
        if self.cut_list is not None:
            inList = False
            endInList = False
            for index, item in enumerate(self.cut_list):
                if item[1] == self.CUT_TYPE_LAST:
                    self.cut_list[index] = (stopPosition, self.CUT_TYPE_LAST)
                    inList = True
                if item[1] == self.CUT_TYPE_OUT:
                    self.cut_list[index] = (length, self.CUT_TYPE_OUT)
                    endInList = True

            if not inList:
                insort(self.cut_list, (stopPosition, self.CUT_TYPE_LAST))
            if not endInList:
                insort(self.cut_list, (length, self.CUT_TYPE_OUT))
        else:
            self.cut_list = [(stopPosition, self.CUT_TYPE_LAST)]
            insort(self.cut_list, (length, self.CUT_TYPE_OUT))

    def getCuePositions(self):
        length = 0
        last_pos = 0
        for pts, what in self.cut_list:
            if what == self.CUT_TYPE_OUT:
                length = pts / 90000
            if what == self.CUT_TYPE_LAST:
                last_pos = pts / 90000

        if length == 0:
            from ServiceProvider import ServiceCenter
            info = ServiceCenter.getInstance().info(self.currentService)
            if info:
                length = info.getLength(self.currentService)
        return [length, last_pos]

    def addPlayerEvents(self):
        try:
            self.onClose.insert(0, self.playerClosed)
        except Exception as e:
            print('addPlayerEvents exception: ' + str(e))

    def playerClosed(self, service=None):
        try:
            self.currently_playing = False
            cancel_cutlist = ['ts',
             'm4a',
             'mp3',
             'ogg',
             'wav']
            ext = self.currentService.getPath().split('.')[-1].lower()
            if ext in cancel_cutlist:
                if service:
                    self.currentService = service
                return
            self.modifyCutListEnries()
            CueSheet(self.currentService).setCutList(self.cut_list)
            if service:
                self.currentService = service
        except Exception as e:
            print('playerClosed exception:\n' + str(e))

    def isCurrentlyPlaying(self):
        return self.currently_playing

    def getDVDNameFromFile(self, file_name):
        if os.path.isfile(file_name):
            return os.path.basename(os.path.splitext(file_name)[0])
        else:
            return os.path.basename(file_name)

    def storeDVDCueSheet(self):
        try:
            file_name = self.currentService.getPath()
            name = self.getDVDNameFromFile(file_name)
            src = '/home/root/dvd-%s.cuts' % name.upper()
            if os.path.isdir(file_name):
                src = os.path.join(file_name, 'dvd.cuts')
            dst = file_name + '.cuts'
            if os.path.exists(src):
                copyfile(src, dst)
        except Exception as e:
            print('storeDVDCueSheet exception:\n' + e)

    def loadDVDCueSheet(self):
        try:
            file_name = self.currentService.getPath()
            src = file_name + '.cuts'
            if os.path.exists(src) and os.path.isfile(file_name) and checkDVDCuts(file_name):
                name = self.getDVDNameFromFile(file_name)
                dst = '/home/root/dvd-%s.cuts' % name.upper()
                copyfile(src, dst)
        except Exception as e:
            print('loadDVDCueSheet exception:\n' + e)


class DVDCutListSupport(CutListSupportBase):

    def __init__(self, service):
        CutListSupportBase.__init__(self, service)
        self.jump_relative = False

    def downloadCuesheet(self):
        from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer as eDVDPlayer
        eDVDPlayer.downloadCuesheet(self)
        if len(self.cut_list) == 0:
            self.cut_list = CueSheet(self.currentService).getCutList()
            self.jump_relative = True
        self.checkResumeSupport()
        if self.ENABLE_RESUME_SUPPORT is False:
            if self.jump_first_mark:
                eDVDPlayer.playLastCB(self, True)
            else:
                eDVDPlayer.playLastCB(self, False)

    def __getServiceName(self, service):
        try:
            from enigma import iPlayableServicePtr
            if isinstance(service, iPlayableServicePtr):
                info = service and service.info()
                ref = None
            else:
                info = service and self.source.info
                ref = service
            if info is None:
                return 'no info'
            name = ref and info.getName(ref)
            if name is None:
                name = info.getName()
            return name.replace('\xc2\x86', '').replace('\xc2\x87', '')
        except Exception as e:
            print(str(e))

    def playLastCB(self, answer):
        from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer as eDVDPlayer
        if not self.jump_relative:
            eDVDPlayer.playLastCB(self, answer)
        else:
            if answer is True:
                eDVDPlayer.doSeekRelative(self, self.resume_point)
            eDVDPlayer.playLastCB(self, False)


class CutListSupport(CutListSupportBase):

    def __init__(self, service):
        CutListSupportBase.__init__(self, service)

    def playLastCB(self, answer):
        if answer is False and self.jump_first_play_last:
            self.resume_point = self.jump_first_play_last
            answer = True
        InfoBarCueSheetSupport.playLastCB(self, answer)

    def toggleMark(self, onlyremove=False, onlyadd=False, tolerance=450000, onlyreturn=False):
        if not self.currentService.getPath().endswith('.ts'):
            tolerance = 1800000
        InfoBarCueSheetSupport.toggleMark(self, onlyremove=False, onlyadd=False, tolerance=tolerance, onlyreturn=False)


class BludiscCutListSupport(CutListSupport):

    def __init__(self, service, main_movie):
        CutListSupportBase.__init__(self, service)
        self.main_movie = main_movie

    def playerClosed(self, service=None):
        seek = self.session.nav.getCurrentService().seek()
        if seek is None:
            return
        if self.main_movie:
            CutListSupportBase.playerClosed(self, service)

    def getCuesheet(self):
        service = self.session.nav.getCurrentService()
        if service is None:
            return
        cue_bd = service.cueSheet()
        cut_bd = cue_bd.getCutList()
        cue = CueSheet(self.currentService)
        cut_hd = cue.getCutList()
        update_cue = False
        if cut_bd and (0, 2) not in cut_hd and self.main_movie:
            for cut in cut_bd:
                if cut not in cut_hd:
                    print('add cut: %s' % cut)
                    insort(cut_hd, cut)
                    update_cue = True

        if update_cue:
            print('update cue')
            cue.setCutList(cut_hd)
        if not self.main_movie:
            print('no bludisc main movie, disable resume support')
            self.ENABLE_RESUME_SUPPORT = False
            return cue_bd
        self.session.nav.currentlyPlayingService.cueSheet = cue
        return cue

    def toggleMark(self, onlyremove=False, onlyadd=False, tolerance=450000, onlyreturn=False):
        if self.main_movie:
            InfoBarCueSheetSupport.toggleMark(self, onlyremove=False, onlyadd=False, tolerance=tolerance, onlyreturn=False)

    def checkResumeSupport(self):
        if self.main_movie:
            CutListSupport.checkResumeSupport(self)
