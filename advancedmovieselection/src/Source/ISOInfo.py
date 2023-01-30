import os
from struct import unpack
if __name__ == '__main__':

    def printStackTrace():
        pass


else:
    from ServiceProvider import eServiceReferenceBludisc
    from Globals import printStackTrace


def LB16(data):
    return unpack('<H', data[0:2])[0]


def LB32(data):
    return unpack('<I', data[0:4])[0]


def LB64(data):
    return unpack('<Q', data[0:8])[0]


def MB16(data):
    return unpack('>H', data[0:2])[0]


def MB32(data):
    return unpack('>I', data[0:4])[0]


def BB16(data):
    return unpack('<H', data[0:2])[0]


def BB32(data):
    return unpack('<I', data[0:4])[0]


class VolumeStructureDescriptor:
    TYPE = 1
    DATA_LEN = 7

    def __init__(self, data):
        self.type = ord(data[0])
        self.identifier = data[1:6]
        self.version = ord(data[6])


class LPathTableRecord:

    def __init__(self, data):
        self.len_di = ord(data[0])
        self.length = 8 + self.len_di
        self.directory = data[8:self.length]
        if self.len_di & 1:
            self.length += 1


class ISORead:
    BLOCK_SIZE = 2048
    VOLUME_TYPE_DVD = 'CD001'
    VOLUME_TYPE_BEA = 'BEA01'

    def __init__(self):
        pass

    def readPathTable(self, file_name):
        path_table = []
        try:
            f = open(file_name, 'rb')
            block = 16 * ISORead.BLOCK_SIZE
            f.seek(block)
            data = f.read(7)
            vd = VolumeStructureDescriptor(data)
            if vd.type == VolumeStructureDescriptor.TYPE and vd.identifier == self.VOLUME_TYPE_DVD:
                f.seek(block + 132)
                path_table_size = LB32(f.read(8))
                l_path_table = LB32(f.read(4))
                if l_path_table > 0 and path_table_size < self.BLOCK_SIZE:
                    f.seek(l_path_table * self.BLOCK_SIZE)
                    length = 0
                    data = f.read(path_table_size)
                    while length < path_table_size:
                        dr = LPathTableRecord(data[length:])
                        length += dr.length
                        path_table.append(dr.directory)

            f.close()
        except:
            printStackTrace()

        return path_table


import commands


class ISOInfo:
    ERROR = -1
    UNKNOWN = 0
    DVD = 1
    BLUDISC = 2
    MOUNT_PATH = '/media/bludisc.iso'

    def __init__(self):
        pass

    def getFormat(self, service):
        print('checking iso:' % service.getPath())
        if not self.mount(service.getPath()):
            return self.ERROR
        if os.path.exists(self.MOUNT_PATH + '/BDMV/'):
            print('Bludisc iso file detected')
            return self.BLUDISC
        if os.path.exists(self.MOUNT_PATH + '/VIDEO_TS/') or os.path.exists(self.MOUNT_PATH + '/VIDEO_TS.IFO'):
            print('DVD iso file detected')
            self.umount()
            return self.DVD
        print('Unknown iso file')
        return self.UNKNOWN

    def getFormatISO9660(self, service):
        print('checking iso: %s' % service.getPath())
        for d in ISORead().readPathTable(service.getPath()):
            if 'BDMV' in d:
                print('Bludisc iso file detected')
                return self.BLUDISC
            if 'VIDEO_TS' in d:
                print('DVD iso file detected')
                return self.DVD

        print('Unknown iso file')
        return self.UNKNOWN

    def mount(self, iso):
        self.umount()
        try:
            if not os.path.exists(self.MOUNT_PATH):
                print('Creating mount path for bludisc iso on: %s' % self.MOUNT_PATH)
                os.mkdir(self.MOUNT_PATH)
            cmd = 'mount -r -o loop "%s" "%s"' % (iso, self.MOUNT_PATH)
            print('exec command: %s' % cmd)
            out = commands.getoutput(cmd)
            if out:
                print('error: %s' % out)
            return not out
        except:
            printStackTrace()
            return False

    @classmethod
    def umount(self):
        try:
            cmd = 'umount -df "%s"' % ISOInfo.MOUNT_PATH
            print('exec command: %s' % cmd)
            out = commands.getoutput(cmd)
            if out:
                print('error: %s' % out)
            return not out
        except:
            printStackTrace()
            return False

    def getPath(self):
        return self.MOUNT_PATH

    def getService(self, service):
        service = eServiceReferenceBludisc(service)
        service.setBludisc(self.MOUNT_PATH)
        return service


if __name__ == '__main__':
    import datetime

    class Service:

        def __init__(self, path):
            self.path = path

        def getPath(self):
            return self.path

    d1 = datetime.datetime.now()
    iso_path = '/media/net/hdd2/DVD'
    iso_files = os.listdir(iso_path)
    for name in iso_files:
        if not name.endswith('.iso'):
            continue
        n = os.path.join(iso_path, name)
        if not os.path.isfile(n):
            continue
        ISOInfo().getFormatISO9660(Service(n))

    d2 = datetime.datetime.now()
    print(d2 - d1)
