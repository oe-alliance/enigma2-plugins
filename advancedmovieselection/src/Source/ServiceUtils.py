"""
Copyright (C) 2012 cmikula

Move and Copy support for Advanced Movie Selection

In case of reuse of this source code please do not remove this copyright.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For more information on the GNU General Public License see:
<http://www.gnu.org/licenses/>.

For example, if you distribute copies of such a program, whether gratis or for a fee, you
must pass on to the recipients the same freedoms that you received. You must make sure
that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
"""
from __future__ import print_function
import os
import glob
import shutil
import time
import operator
import threading


def realSize(bytes, digits=1, factor=1024):
    size = float(bytes)
    if bytes == 0:
        digits = 0
    f = '%%.%df' % digits
    if size < 1000:
        return f % size + ' Bytes'
    size = size / factor
    if size < 1000:
        return f % size + ' KB'
    size = size / factor
    if size < 1000:
        return f % size + ' MB'
    size = size / factor
    if size < 1000:
        return f % size + ' GB'
    size = size / factor
    return f % size + ' TB'


def diskUsage(path):
    """Return disk usage statistics about the given path.

    Returned valus is a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return (total, used, free)


def getFolderSize(loadPath):
    folder_size = 0
    try:
        for path, dirs, files in os.walk(loadPath):
            for f in files:
                filename = os.path.join(path, f)
                if os.path.exists(filename):
                    folder_size += os.path.getsize(filename)

    except Exception as e:
        print(str(e))

    return folder_size


def getDirSize(root):
    folder_size = 0
    try:
        for filename in os.listdir(root):
            p = os.path.join(root, filename)
            if os.path.exists(p):
                folder_size += os.path.getsize(p)

    except Exception as e:
        print(str(e))

    return folder_size


class ServiceFileInfo:
    CP_EXT = '~'
    STAT_WAITING = 0
    STAT_STARTED = 1
    STAT_FINISHED = 2

    def __init__(self, service, dst):
        self.service = service
        self.destination_path = os.path.normpath(dst)
        self.source_path, self.file_name = os.path.split(service.getPath())
        self.status = self.STAT_WAITING
        print('ServiceFileInfo')
        print('Name:', self.file_name)
        print('From:', self.source_path)
        print('To:', self.destination_path)
        if os.path.isfile(service.getPath()):
            filename = service.getPath().rsplit('.', 1)[0] + '.*'
            l = self.listAllFromSource(filename)
            self.file_list = sorted(l, key=operator.itemgetter(1), reverse=True)
        else:
            filename = service.getPath() + '.*'
            l = self.listAllFromSource(filename)
            self.file_list = sorted(l, key=operator.itemgetter(1), reverse=True)
            self.file_list.insert(0, (service.getPath(), getFolderSize(service.getPath())))
        self.total = 0
        for item in self.file_list:
            self.total += item[1]

        print('Total:', realSize(self.total, 3))
        print('Files:', self.file_list)

    def listAllFromSource(self, filename):
        l = []
        for sfile in os.listdir(self.source_path):
            f = os.path.join(self.source_path, sfile)
            if f.startswith(filename[:-1]):
                l.append((f, os.path.getsize(f)))

        return l

    def getTotal(self):
        return self.total

    def getFileCount(self):
        return len(self.file_list)

    def getName(self):
        return self.service.getName()

    def getPath(self):
        return self.service.getPath()

    def getDestinationPath(self):
        return self.destination_path

    def getSourcePath(self):
        return self.source_path

    def getFileName(self):
        return self.file_name

    def getStatus(self):
        return self.status

    def setStatus(self, status):
        self.status = status


class Job:

    def __init__(self, list, cb=None):
        self.list = list
        self.cb = cb
        self.copied = 0
        self.file_index = 0
        self.current_index = 0
        self.count = 0
        self.total = 0
        self.lock = threading.Lock()
        self.start_time = 0
        self.end_time = 0
        self.do_move = False
        self.setCurrentFile(None, None)
        self.current_name = ''
        self.current_dst_path = ''
        self.current_src_path = ''
        self.error = None
        for item in self.list:
            self.total += item.getTotal()
            self.count += item.getFileCount()

    def StartAsync(self, do_move=False):
        self.do_move = do_move
        self.abort = False
        from thread import start_new_thread
        start_new_thread(self.Run, (do_move,))

    def Run(self, do_move=False):
        try:
            self.start_time = time.time()
            for si in self.list:
                if self.abort:
                    return
                self.current_name = si.getName()
                self.current_src_path = si.getSourcePath()
                self.current_dst_path = si.getDestinationPath()
                self.current_index += 1
                si.setStatus(ServiceFileInfo.STAT_STARTED)
                self.copy(si, do_move)
                si.setStatus(ServiceFileInfo.STAT_FINISHED)

        except Exception as e:
            self.error = e
        except IOError as e:
            self.error = e
        finally:
            if self.error:
                print('Job failed:', self.error)
            self.end_time = time.time()
            self.current_name = ''
            if self.cb:
                self.cb(self)

    def copy(self, si, do_move=False):
        if len(si.file_list) == 0:
            return
        if not os.path.exists(si.getDestinationPath()):
            os.makedirs(si.getDestinationPath())
        try:
            for index, src in enumerate(si.file_list):
                self.file_index += 1
                file_name = os.path.basename(src[0])
                dst = os.path.join(si.getDestinationPath(), file_name)
                if index == 0:
                    new = dst
                    dst = old = new + si.CP_EXT
                elif os.path.exists(dst):
                    raise Exception('File already exists: %s' % os.path.basename(dst))
                self.setCurrentFile(src[0], dst)
                if do_move:
                    print('move: "%s" -> "%s"' % (src[0], dst))
                    cmd = 'mv "%s" "%s"' % (src[0], dst)
                else:
                    print('copy: "%s" -> "%s"' % (src[0], dst))
                    if os.path.isfile(src[0]):
                        cmd = 'cp -p "%s" "%s"' % (src[0], dst)
                    else:
                        cmd = 'cp -p -r "%s" "%s"' % (src[0], dst)
                print(cmd)
                l = os.popen(cmd)
                print(l.readlines())
                l.close()
                self.setCurrentFile(None, None)
                self.copied += src[1]

        finally:
            if os.path.exists(old):
                print('rename: "%s" -> "%s"' % (old, new))
                os.rename(old, new)

    def prepare(self):
        available = []
        for si in self.list:
            fp = si.getPath()
            file_name = os.path.basename(fp)
            dst = os.path.join(si.getDestinationPath(), file_name)
            if os.path.exists(dst):
                available.append(si.service)

        return available

    def cancel(self):
        """we still process started movies to the end and skipping all following!"""
        self.abort = True

    def isCancelled(self):
        return self.abort

    def setCurrentFile(self, src_file, dst_file):
        self.lock.acquire()
        self.src_file = src_file
        self.dst_file = dst_file
        self.lock.release()

    def getSizeCopied(self):
        self.lock.acquire()
        copied = self.copied
        try:
            if self.dst_file and os.path.exists(self.dst_file):
                if os.path.isfile(self.dst_file):
                    copied = self.copied + os.path.getsize(self.dst_file)
                else:
                    copied = self.copied + getFolderSize(self.dst_file)
        finally:
            self.lock.release()

        return copied

    def getFileInfo(self):
        return (self.src_file, self.dst_file)

    def getFileCount(self):
        return self.count

    def getFileIndex(self):
        return self.file_index

    def getMovieCount(self):
        return len(self.list)

    def getMovieName(self):
        return self.current_name

    def getSourcePath(self):
        return self.current_src_path

    def getDestinationPath(self):
        return self.current_dst_path

    def getMovieIndex(self):
        return self.current_index

    def getSizeTotal(self):
        return self.total

    def getStartTime(self):
        return self.start_time

    def getEndTime(self):
        return self.end_time

    def getElapsedTime(self):
        if self.isFinished():
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def getError(self):
        return self.error

    def isStarted(self):
        return self.start_time != 0

    def isFinished(self):
        return self.end_time != 0

    def getMode(self):
        return self.do_move

    def __repr__(self):
        return '<MoveCopyJob: %d/%d>' % (self.file_index, self.count)


class ServiceUtil:

    def __init__(self):
        self.list = []
        self.proc = []

    def setServices(self, service_list, dst):
        self.list = []
        self.add(service_list, dst)

    def add(self, service_list, dst):
        self.cleanup()
        if not isinstance(service_list, list):
            service_list = [service_list]
        for s in service_list:
            self.list.append(ServiceFileInfo(s, dst))

    def clear(self):
        self.list = []

    def prepareJob(self):
        return Job(self.list)

    def move(self):
        self.start(True)

    def copy(self):
        self.start(False)

    def start(self, do_move):
        job = Job(self.list, self.jobFinished)
        self.proc.append(job)
        job.StartAsync(do_move)
        self.list = []

    def jobFinished(self, job):
        print('Job finished:')

    def cleanup(self):
        self.proc = filter(lambda job: not job.isFinished(), self.proc)

    def removeJob(self, job):
        if job in self.proc:
            self.proc.remove(job)

    def getJobs(self):
        return self.proc

    def isServiceMoving(self, serviceref):
        for job in self.proc:
            if job.getMode() and not job.isFinished():
                for si in job.list:
                    if si.service.getPath() == serviceref.getPath():
                        return True


class eServiceReference:

    def __init__(self, path):
        self.path = path
        p = path
        if p.endswith('.ts'):
            meta_path = p[:-3] + '.ts.meta'
        else:
            meta_path = p + '.ts.meta'
        if os.path.exists(meta_path):
            file = open(meta_path, 'r')
            file.readline()
            self.setName(file.readline().rstrip('\r\n'))
            if len(self.name) == 0:
                self.setName(os.path.basename(p))
            self.short_description = file.readline().rstrip('\r\n')
            file.close()
        else:
            self.setName(os.path.basename(p))
            self.short_description = ''

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def setPath(self, path):
        self.path = path

    def getPath(self):
        return self.path

    def getShortDescription(self):
        return self.short_description


class JobMonitor:

    def __init__(self, monitor):
        from thread import start_new_thread
        start_new_thread(self.Run, (monitor,))

    def Run(self, monitor):
        import time
        update_time = 0.1
        while True:
            for job in monitor.getJobs():
                try:
                    if not job.isStarted():
                        continue
                    full = job.getSizeTotal()
                    copied = job.getSizeCopied()
                    elapsed_time = job.getElapsedTime()
                    progress = copied * 100 / full
                    b_per_sec = copied / elapsed_time
                    print('%0s,%s' % job.getFileInfo())
                    print('%s: %0d%%, %s, %s, %s/S - %.3f S (%d/%d)' % (job.getMovieName(),
                     progress,
                     realSize(full),
                     realSize(copied),
                     realSize(b_per_sec, 3),
                     elapsed_time,
                     job.getCurrentIndex(),
                     job.getFileCount()))
                    if job.isFinished():
                        monitor.removeJob(job)
                        continue
                except Exception as e:
                    print(str(e))

            time.sleep(update_time)


serviceUtil = ServiceUtil()
if __name__ == '__main__':
    jobMonitor = JobMonitor(serviceUtil)
    import os
    p = '/media/Lokaler Datentr\xc3\xa4ger/Users'
    l = []
    for file in glob.glob(os.path.join(p, '*.iso')):
        l.append(eServiceReference(file))

    serviceUtil.add(l, os.path.join(p, 'Test1'))
    serviceUtil.copy()
    serviceUtil.add(l, os.path.join(p, 'Test2'))
    serviceUtil.copy()
