import os
from Components.Element import cached
from Components.Sources.ServiceEvent import ServiceEvent as eServiceEvent
from enigma import eServiceCenter, iServiceInformation, eServiceReference
from Tools.Directories import fileExists
from EventInformationTable import EventInformationTable
from ServiceUtils import getFolderSize
from CueSheetSupport import CueSheet
from ServiceDescriptor import DirectoryEvent
from Globals import printStackTrace
instance = None


class ServiceTypes:
    idInvalid = eServiceReference.idInvalid
    idStructure = eServiceReference.idStructure
    idDVB = eServiceReference.idDVB
    idFile = eServiceReference.idFile
    idUser = eServiceReference.idUser
    idDVD = 4369
    idMP3 = 4097
    idBD = 4


class ServiceFlags:
    isDirectory = eServiceReference.isDirectory
    mustDescent = eServiceReference.mustDescent
    canDescent = eServiceReference.canDescent
    flagDirectory = isDirectory | mustDescent | canDescent
    shouldSort = eServiceReference.shouldSort
    hasSortKey = eServiceReference.hasSortKey
    sort1 = eServiceReference.sort1
    isMarker = eServiceReference.isMarker
    isGroup = eServiceReference.isGroup


def getServiceInfoValue(ref, what):
    info = eServiceCenter.getInstance().info(ref)
    v = ref and info.getInfo(ref, what) or info.getInfo(what)
    if v != iServiceInformation.resIsString:
        return ''
    return ref and info.getInfoString(ref, what) or info.getInfoString(what)


class eServiceReferenceVDir(eServiceReference):

    def __init__(self, file_name):
        eServiceReference.__init__(self, eServiceReference.idFile, ServiceFlags.flagDirectory | ServiceFlags.isMarker, file_name)


class eServiceReferenceMarker(eServiceReference):

    def __init__(self, file_name):
        eServiceReference.__init__(self, eServiceReference.idUser, ServiceFlags.flagDirectory | ServiceFlags.isMarker, file_name)


class eServiceReferenceBackDir(eServiceReference):

    def __init__(self, file_name):
        eServiceReference.__init__(self, eServiceReference.idUser, eServiceReference.flagDirectory, file_name)


class eServiceReferenceListAll(eServiceReference):

    def __init__(self, file_name):
        eServiceReference.__init__(self, eServiceReference.idUser, eServiceReference.flagDirectory, file_name)


class eServiceReferenceHotplug(eServiceReference):

    def __init__(self, file_name):
        eServiceReference.__init__(self, eServiceReference.idUser, eServiceReference.flagDirectory, file_name)


class eServiceReferenceBludisc(eServiceReference):

    def __init__(self, serviceref, isStruct=False):
        idx = 0
        eServiceReference.__init__(self, ServiceTypes.idDVD, 0, serviceref.getPath())
        self.isStruct = isStruct
        if isStruct is True:
            self.setPath(serviceref.getPath()[0:-1])
            self.setName(os.path.basename(self.getPath()))
            self.flags = eServiceReference.isDirectory
        else:
            self.setName(os.path.basename(os.path.splitext(serviceref.getPath())[0]))
        self.bludisc_path = self.getPath()

    def getBludisc(self):
        if self.isStruct is True:
            return self.bludisc_path + '/'
        else:
            return self.bludisc_path

    def setBludisc(self, path):
        self.bludisc_path = path


class eServiceReferenceDvd(eServiceReference):

    def __init__(self, serviceref, dvdStruct=False):
        eServiceReference.__init__(self, ServiceTypes.idDVD, 0, serviceref.getPath())
        self.dvdStruct = dvdStruct
        if dvdStruct is True:
            self.setPath(self.getPath()[0:-1])
            self.setName(os.path.basename(self.getPath()))
            self.flags = eServiceReference.isDirectory
        else:
            self.setName(os.path.basename(os.path.splitext(self.getPath())[0]))

    def getDVD(self):
        if self.dvdStruct is True:
            return [self.getPath() + '/']
        else:
            return [self.getPath()]

    def isIsoImage(self):
        return not self.dvdStruct


def detectBludiscStructure(loadPath):
    if not os.path.isdir(loadPath):
        return None
    if fileExists(loadPath + 'BDMV/'):
        return loadPath + 'BDMV/'


def detectDVDStructure(loadPath):
    if not os.path.isdir(loadPath):
        return None
    if fileExists(loadPath + 'VIDEO_TS.IFO'):
        return loadPath + 'VIDEO_TS.IFO'
    if fileExists(loadPath + 'VIDEO_TS/VIDEO_TS.IFO'):
        return loadPath + 'VIDEO_TS/VIDEO_TS.IFO'


class ServiceCenter:

    def __init__(self):
        global instance
        instance = eServiceCenter.getInstance()
        instance.info = self.info

    @staticmethod
    def getInstance():
        if instance is None:
            ServiceCenter()
        return instance

    def info(self, serviceref):
        info = eServiceCenter.getInstance().info(serviceref)
        if info is not None:
            if serviceref.getPath().endswith('.ts'):
                info.cueSheet = CueSheet(serviceref)
                return info
            return Info(serviceref)
        else:
            return Info(serviceref)


class ServiceEvent(eServiceEvent):

    def __init__(self):
        eServiceEvent.__init__(self)

    @cached
    def getInfo(self):
        return self.service and ServiceCenter.getInstance().info(self.service)

    info = property(getInfo)


def checkCreateMetaFile(serviceref):
    if not serviceref.flags & eServiceReference.mustDescent:
        if serviceref.type == eServiceReference.idDVB:
            meta_path = serviceref.getPath() + '.meta'
        else:
            meta_path = serviceref.getPath() + '.ts.meta'
        if not os.path.exists(meta_path):
            if os.path.isfile(serviceref.getPath()):
                title = os.path.basename(os.path.splitext(serviceref.getPath())[0])
            else:
                title = serviceref.getName()
            lt = long(os.stat(serviceref.getPath()).st_mtime)
            print('create new metafile')
            print(serviceref.toString())
            print(lt)
            sid = '%d:%d:0:0:0:0:0:0:0:0:' % (serviceref.type, serviceref.flags)
            descr = ''
            time = lt
            tags = ''
            metafile = open(meta_path, 'w')
            metafile.write('%s\n%s\n%s\n%d\n%s\n' % (sid,
             title,
             descr,
             time,
             tags))
            metafile.close()
        return meta_path


class ServiceInfo:

    def __init__(self, serviceref):
        self.servicename = ''
        self.description = ''
        self.tags = ''
        self.name = ''
        self.time_create = ''
        try:
            try:
                meta_path = checkCreateMetaFile(serviceref)
            except Exception as e:
                print(str(e))
                if os.path.isfile(serviceref.getPath()):
                    self.name = os.path.basename(serviceref.getPath()).split('.')[0]
                else:
                    self.name = serviceref.getName()
                return

            if meta_path is not None and os.path.exists(meta_path):
                meta_file = open(meta_path, 'r')
                meta_file.readline()
                self.name = meta_file.readline().rstrip('\r\n')
                self.description = meta_file.readline().rstrip('\r\n')
                self.time_create = meta_file.readline().rstrip('\r\n')
                self.tags = meta_file.readline().rstrip('\r\n')
                meta_file.close()
        except Exception as e:
            print('Exception in load meta data: ' + str(e))
            printStackTrace()

    def getServiceName(self):
        return self.servicename

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getTags(self):
        return self.tags


class Info:

    def __init__(self, serviceref):
        self.cue = CueSheet(serviceref)
        self.serviceInfo = ServiceInfo(serviceref)
        self.length = 0
        self.end = 0
        self.last = 0
        serviceref.cueSheet = self.cueSheet

    def cueSheet(self):
        return self.cue

    def getLength(self, serviceref):
        cut_list = self.cue.getCutList()
        for pts, what in cut_list:
            if what == 1:
                self.length = pts / 90000

        if self.length == 0:
            file_name = serviceref.getPath()
            if not os.path.isdir(file_name):
                eit_file = os.path.splitext(file_name)[0] + '.eit'
            else:
                eit_file = file_name + '.eit'
            self.length = EventInformationTable(eit_file, True).getDuration()
        return self.length

    def getInfoString(self, serviceref, type):
        if type == iServiceInformation.sServiceref:
            return 'iServiceInformation.sServiceref'
        if type == iServiceInformation.sDescription:
            return self.serviceInfo.description
        if type == iServiceInformation.sTags:
            return self.serviceInfo.tags
        return 'None'

    def getInfo(self, serviceref, type):
        if type == iServiceInformation.sTimeCreate:
            if os.path.exists(serviceref.getPath()):
                if self.serviceInfo.time_create:
                    return long(self.serviceInfo.time_create)
                return long(os.stat(serviceref.getPath()).st_mtime)

    def getInfoObject(self, serviceref, type):
        if type == iServiceInformation.sFileSize:
            try:
                dvd = detectDVDStructure(serviceref.getPath() + '/')
                if dvd:
                    return getFolderSize(os.path.dirname(dvd))
                return os.path.getsize(serviceref.getPath())
            except Exception as e:
                print(str(e))
                return -1

    def getServiceReference(self):
        return self.serviceInfo

    def getName(self, serviceref):
        if self.serviceInfo.name:
            return self.serviceInfo.name
        else:
            return serviceref.getName()

    def getEvent(self, serviceref):
        file_name = serviceref.getPath()
        if serviceref.flags & eServiceReference.mustDescent:
            eit_file = file_name + '.eit'
            if os.path.exists(eit_file):
                return EventInformationTable(eit_file)
            return DirectoryEvent(serviceref)
        if not serviceref.flags & eServiceReference.isDirectory:
            eit_file = os.path.splitext(file_name)[0] + '.eit'
        else:
            eit_file = file_name + '.eit'
        if os.path.exists(eit_file):
            return EventInformationTable(eit_file)
        return Event(self, serviceref)


class Event:

    def __init__(self, info, serviceref):
        self.info = info
        self.serviceref = serviceref

    def getEventName(self):
        return self.info.serviceInfo.name

    def getShortDescription(self):
        return self.info.serviceInfo.description

    def getExtendedDescription(self):
        return ''

    def getEventId(self):
        return 0

    def getBeginTimeString(self):
        from datetime import datetime
        begin = self.info.getInfo(self.serviceref, iServiceInformation.sTimeCreate)
        d = datetime.fromtimestamp(begin)
        return d.strftime('%d.%m.%Y %H:%M')

    def getDuration(self):
        return self.info.length

    def getBeginTime(self):
        return self.info.getInfo(self.serviceref, iServiceInformation.sTimeCreate)
