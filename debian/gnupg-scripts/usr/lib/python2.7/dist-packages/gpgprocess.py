"""
GnuPG-Scripts

Copyright (C) 2011 - 2016 Discreete Linux Team <info@discreete-linux.org>

Module for handling GnuPG processes
"""

import os
from gi.repository import Gtk
import gettext
import time
import subprocess
import select
import threading
import zipfile
import tarfile
import gpgmessages
import gpgplatform


gettext.install("gnupg-scripts", unicode=1)
# Init icons
icon_theme = Gtk.IconTheme.get_default()
try:
    icon = icon_theme.load_icon("gnupg-scripts-encrypt", 24, 0)
except:
    pass
zip_encoding = 'utf-8'


def getKeyRings(name):
    keyringList = []
    for dirpath, dirs, files in os.walk("/media"):
        if ".gnupg" in dirs:
            keyring = os.path.join(dirpath, ".gnupg", name)
            if os.path.exists(keyring):
                keyringList.append(keyring)
    return keyringList


def addPubrings(arglist):
    for keyring in getKeyRings("pubring.gpg"):
        arglist.append("--keyring")
        arglist.append(keyring)


def addSecrings(arglist):
    for keyring in getKeyRings("secring.gpg"):
        arglist.append("--secret-keyring")
        arglist.append(keyring)


class GpgThread(threading.Thread):
    def __init__(self, args):
        super(GpgThread, self).__init__()
        self.args = args

    def run(self):
        arglist = [ gpgplatform.gpg_binary(), "--batch", "--no-tty" ]
        if type(self.args) == str:
            arglist.append(self.args)
        else:
            arglist += self.args
        self.result = {}
        proc = subprocess.Popen(args=arglist, bufsize=-1,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        self.result["stdout"] = []
        self.result["stderr"] = []
        for line in proc.stdout:
            self.result["stdout"].append(line.decode('UTF-8', 'replace'))
        for line in proc.stderr:
            self.result["stderr"].append(line.decode('UTF-8', 'replace'))
        self.result["return-code"] = proc.wait()
        proc.stdout.close()
        proc.stderr.close()

    def response(self):
        return self.result


class ZipThread(threading.Thread):
    def __init__(self, encfiles, arname, duplicateMessage,
                 workdir, remove=False):
        super(ZipThread, self).__init__()
        print "encfiles:", encfiles
        print "arname:", arname
        self.encfiles = encfiles
        self.duplicateMessage = duplicateMessage
        self.remove = remove
        self.arname = arname
        self.result = False
        self.workdir = workdir

    def run(self):
        global icon
        zfile = zipfile.ZipFile(self.arname, "w", zipfile.ZIP_DEFLATED)
        # Add files to ZIP archive
        namelist = []
        for curfile in self.encfiles:
            name = os.path.basename(curfile)
            curdir = os.path.dirname(curfile)
            if name in namelist:
                msg = self.duplicateMessage % name
                gpgmessages.displayMessage(msg, _("Archive Packing"), icon=icon)
                self.result = False
                break
            if os.path.isfile(curfile):
                zfile.write(curfile, name)
                namelist.append(name)
                if self.remove:
                    os.remove(curfile)
            elif os.path.isdir(curfile):
                if curdir:
                    try:
                        os.chdir(curdir)
                    except OSError:
                        continue
                for dirpath, dirs, files in os.walk(name):
                    if files:
                        zfile.write(dirpath)
                    for f in files:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            zfile.write(fp)
                        if self.remove:
                            os.remove(fp)
                try:
                    os.chdir(self.workdir)
                except OSError:
                    self.result = False
                    break
                namelist.append(name)
        zfile.close()
        self.result = [ self.arname ]

    def response(self):
        return self.result


class TarThread(threading.Thread):
    def __init__(self, encfiles, arname, duplicateMessage,
                 mode, workdir, remove=False):
        super(TarThread, self).__init__()
        print "encfiles:", encfiles
        print "arname:", arname
        self.encfiles = encfiles
        self.duplicateMessage = duplicateMessage
        self.remove = remove
        self.arname = arname
        self.mode = mode
        self.result = False
        self.workdir = workdir

    def run(self):
        global icon
        tfile = tarfile.open(self.arname, self.mode)
        namelist = []
        for curfile in self.encfiles:
            name = os.path.basename(curfile)
            curdir = os.path.dirname(curfile)
            if name in namelist:
                msg = self.duplicateMessage % name
                gpgmessages.displayMessage(msg, _("Archive Packing"), icon=icon)
                self.result = False
                break
            if os.path.isfile(curfile) or os.path.isdir(curfile):
                tfile.add(curfile, name)
                namelist.append(name)
            if self.remove and os.path.isfile(curfile):
                os.remove(curfile)
            if self.remove and os.path.isdir(curfile):
                if curdir:
                    try:
                        os.chdir(curdir)
                    except OSError:
                        continue
                for dirpath, dirs, files in os.walk(name):
                    for f in files:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            os.remove(fp)
                try:
                    os.chdir(self.workdir)
                except OSError:
                    self.result = False
                    break
                namelist.append(name)
        tfile.close()
        self.result = [ self.arname ]

    def response(self):
        return self.result


class UnzipThread(threading.Thread):
    def __init__(self, outname):
        super(UnzipThread, self).__init__()
        self.outname = outname
        self.unpack = True

    def run(self):
        global icon
        zfile = zipfile.ZipFile(self.outname, "r")
        namelist = zfile.namelist()
        msg = _("Unpacking failed because %s is in the way.")
        for name in namelist:
            if name.endswith(os.sep):
                oname = name.rstrip(os.sep)
                if not os.path.isdir(oname):
                    try:
                        os.makedirs(oname)
                    except OSError:
                        msg = msg % oname
                        gpgmessages.displayMessage(msg, _("Archive Unpacking"),
                            icon=icon)
                        self.unpack = False
                        break
            else:
                s = zfile.read(name)
                if os.path.exists(name):
                    msg = msg % name
                    gpgmessages.displayMessage(msg, _("Archive Unpacking"),
                        icon=icon)
                    self.unpack = False
                    break
                fp = open(name, "wb")
                fp.write(s)
                fp.close()

    def response(self):
        return self.unpack


class UntarThread(threading.Thread):
    def __init__(self, outname):
        super(UntarThread, self).__init__()
        self.outname = outname
        self.unpack = True

    def run(self):
        global icon
        tfile = tarfile.open(self.outname, "r")
        namelist = tfile.getnames()
        msg = _("Unpacking failed because %s is in the way.")
        for name in namelist:
            if os.path.exists(name) and not os.path.isdir(name):
                msg = msg % name
                gpgmessages.displayMessage(msg, _("Archive Unpacking"),
                    icon=icon)
                self.unpack = False
                break
            tfile.extract(name)
        tfile.close()

    def response(self):
        return self.unpack


def gpg(args):
    "Call gpg with the given argument(s)"
    arglist = [ gpgplatform.gpg_binary(), "--batch", "--no-tty" ]
    if type(args) == str:
        arglist.append(args)
    else:
        arglist += args
    result = {}
    proc = subprocess.Popen(args=arglist, bufsize=-1, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, universal_newlines=True)
    result["stdout"] = []
    result["stderr"] = []
    for line in proc.stdout:
        result["stdout"].append(line.decode('UTF-8', 'replace'))
    for line in proc.stderr:
        result["stderr"].append(line.decode('UTF-8'))
    result["return-code"] = proc.wait()
    proc.stdout.close()
    proc.stderr.close()
    return result


def findRunningGpgDecrypts():
    """ Find other running gpg-decrypt processes """
    result = []
    if os.name == "posix":
        args = [ "ps", "-eo", "pid,comm", "--no-headers" ]
        ps = subprocess.Popen(args=args, bufsize=-1, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        for line in ps.stdout.readlines():
            splitline = line.split()
            if len(splitline) > 1 and splitline[1] == "gpg-decrypt":
                result.append(int(splitline[0]))
        ps.stdin.close()
        ps.stdout.close()
        ps.stderr.close()
    elif os.name == "nt":
        from win32com.client import GetObject
        WMI = GetObject("winmgmts:")
        procs = WMI.InstancesOf('Win32_Process')
        for p in procs:
            if "gpg-decrypt" in p.Property_('Name').Value:
                result.append(int(p.Property_('ProcessID').Value))
    return result


def waitUntilPriorGpgDecryptsFinished(timeout=-1):
    """ Wait until other (earlier) gpg-decrypt processes have exited """
    mypid = os.getpid()
    priorprocs = filter(lambda pid: pid < mypid, findRunningGpgDecrypts())
    while priorprocs:
        if timeout > 0:
            timeout -= 1
        if timeout == 0:
            break
        time.sleep(1)
        priorprocs = filter(lambda pid: pid < mypid, findRunningGpgDecrypts())
    return priorprocs
