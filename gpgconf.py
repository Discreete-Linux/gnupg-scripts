"""
GnuPG-Scripts

Copyright (C) 2016 Discreete Linux Team <info@discreete-linux.org>

Module for handling the configuration of GnuPG and GnuPG-Scripts
"""

import os
from gi.repository import Gtk
import gettext
import gpgmessages
import gpgplatform

# Init translations
os.environ.setdefault("LANG", "en")
gettext.install("gnupg-scripts", unicode=1)

class GpgConf(object):
    """ Class for handling GnuPG's own settings (gpg.conf) """
    def __init__(self, parent=None):
        """ Read gpg.conf and set variables accordingly """
        self.gpgconf = os.path.join(gpgplatform.gnupg_home(parent), u"gpg.conf")
        self.parent = parent
        self.use_embedded_filename = True
        self.defaultkey = ""
        self.groups = []
        self.conflist = []
        self.read_config()

    def read_config(self):        
        try:
            fr = open(self.gpgconf, "r")
            for line in fr.readlines():
                line = line.lstrip()
                if not line:
                    line = "\n"
                if line.startswith("group") and line[5].isspace():
                    grpdef = line.split(None, 1)
                    if len(grpdef) > 1 and grpdef[1].find("=") > 0:
                        grpdef = grpdef[1].split("=", 1)
                        grpnam = grpdef[0].strip()
                        grplst = grpdef[1].split()
                        self.groups.append([ grpnam, grplst ])
                elif line.strip() == "use-embedded-filename":
                    self.use_embedded_filename = True
                elif line.startswith("default-key") and line[11].isspace():
                    keydef = line.split()
                    if len(keydef) > 1:
                        self.defaultkey = keydef[1]
                else:
                    self.conflist.append(line)
            fr.close()
        except IOError:
            pass


    def write_config(self):
        """ Write back gpg.conf with current settings """
        try:
            fw = open(self.gpgconf, "w")
            for line in self.conflist:
                fw.write(line)
            for grp in self.groups:
                n = len(grp[1])
                if n > 0:
                    line = "group "
                    line += grp[0]
                    line += "="
                    for key in grp[1]:
                        line += key
                        n -= 1
                        if n:
                            line += " "
                    line += "\n"
                    fw.write(line)
            if self.use_embedded_filename:
                fw.write("use-embedded-filename\n")
            if self.defaultkey:
                fw.write("default-key " + self.defaultkey + "\n")
            fw.close()
            return True
        except IOError:
            msg = _("Error writing GnuPG configuration file %s!") % self.gpgconf.decode('UTF-8', 'replace')
            gpgmessages.displayMessage(msg, _("Error"), parent=self.parent)
            return False



class SrcConf(object):
    """ Class for handling settings of GnuPG-Scripts (gnupg-scripts.conf) """
    def __init__(self, parent=None):
        """ Read gnupg-scripts.conf and set variables accordingly """
        self.srcconf = os.path.join(gpgplatform.gnupg_home(parent),
                                    u"gnupg-scripts.conf")
        self.parent = parent
        self.pack = "ask"
        self.unpack = "ask"
        self.archive = ".zip"
        self.packform = "%y%m%d"
        self.removeorig = False
        self.removepacked = False
        self.removeunpacked = False
        self.enctoself = True
        self.unsigned_keys = True
        try:
            fr = open(self.srcconf, "r")
            for line in fr.readlines():
                line = line.strip()
                if line.startswith("GNUPG_SCRIPTS_ENCRYPT_TO_SELF"):
                    keyval = line.split("=")
                    if len(keyval) > 1 and keyval[1].strip().lower() == "no":
                        self.enctoself = False
                elif line.startswith("GNUPG_SCRIPTS_PACK"):
                    keyval = line.split("=")
                    if len(keyval) > 1:
                        self.pack = keyval[1].strip().lower()
                elif line.startswith("GNUPG_SCRIPTS_UNPACK"):
                    keyval = line.split("=")
                    if len(keyval) > 1:
                        self.unpack = keyval[1].strip().lower()
                elif line.startswith("GNUPG_SCRIPTS_ARCHIVE_FORMAT"):
                    keyval = line.split("=")
                    if len(keyval) > 1:
                        self.archive = keyval[1].strip()
                        if (self.archive != ".zip" and
                            self.archive != ".tar.gz" and
                            self.archive != ".tar.bz2"):
                            self.archive = ".zip"
                elif (line.startswith("GNUPG_SCRIPTS_ZIP_NAME_FORMAT") or
                      line.startswith("GNUPG_SCRIPTS_ARCHIVE_NAME_FORMAT")):
                    keyval = line.split("=")
                    if len(keyval) > 1:
                        self.packform = keyval[1].strip("\"\t ")
                elif (line.startswith("GNUPG_SCRIPTS_REMOVE_ZIP_FILE") or
                      line.startswith("GNUPG_SCRIPTS_REMOVE_PACKED_FILE")):
                    keyval = line.split("=")
                    if len(keyval) > 1 and keyval[1].strip().lower() == "yes":
                        self.removepacked = True
                elif (line.startswith("GNUPG_SCRIPTS_REMOVE_UNZIPPED_FILE") or
                      line.startswith("GNUPG_SCRIPTS_REMOVE_UNPACKED_FILE")):
                    keyval = line.split("=")
                    if len(keyval) > 1 and keyval[1].strip().lower() == "yes":
                        self.removeunpacked = True
                elif line.startswith("GNUPG_SCRIPTS_REMOVE_ORIGINALS"):
                    keyval = line.split("=")
                    if len(keyval) > 1 and keyval[1].strip().lower() == "yes":
                        self.removeorig = True
                elif line.startswith("GNUPG_SCRIPTS_USE_UNSIGNED_KEYS"):
                    keyval = line.split("=")
                    if len(keyval) > 1 and keyval[1].strip().lower() == "no":
                        self.unsigned_keys = False
            fr.close()
        except IOError:
            pass


    def write_config(self):
        """ Write back gpg.conf with current settings """
        try:
            fw = open(self.srcconf, "w")
            if self.enctoself:
                fw.write("GNUPG_SCRIPTS_ENCRYPT_TO_SELF=yes\n")
            else:
                fw.write("GNUPG_SCRIPTS_ENCRYPT_TO_SELF=no\n")
            if self.pack == "yes":
                fw.write("GNUPG_SCRIPTS_PACK=yes\n")
            elif self.pack == "no":
                fw.write("GNUPG_SCRIPTS_PACK=no\n")
            else:
                fw.write("GNUPG_SCRIPTS_PACK=ask\n")
            if self.unpack == "yes":
                fw.write("GNUPG_SCRIPTS_UNPACK=yes\n")
            elif self.unpack == "no":
                fw.write("GNUPG_SCRIPTS_UNPACK=no\n")
            else:
                fw.write("GNUPG_SCRIPTS_UNPACK=ask\n")
            if self.archive:
                fw.write("GNUPG_SCRIPTS_ARCHIVE_FORMAT=" + self.archive + "\n")
            if self.packform:
                fw.write("GNUPG_SCRIPTS_ARCHIVE_NAME_FORMAT=" +
                         self.packform + "\n")
            if self.removepacked:
                fw.write("GNUPG_SCRIPTS_REMOVE_PACKED_FILE=yes\n")
            else:
                fw.write("GNUPG_SCRIPTS_REMOVE_PACKED_FILE=no\n")
            if self.removeunpacked:
                fw.write("GNUPG_SCRIPTS_REMOVE_UNPACKED_FILE=yes\n")
            else:
                fw.write("GNUPG_SCRIPTS_REMOVE_UNPACKED_FILE=no\n")
            if self.removeorig:
                fw.write("GNUPG_SCRIPTS_REMOVE_ORIGINALS=yes\n")
            else:
                fw.write("GNUPG_SCRIPTS_REMOVE_ORIGINALS=no\n")
            if self.unsigned_keys:
                fw.write("GNUPG_SCRIPTS_USE_UNSIGNED_KEYS=yes\n")
            else:
                fw.write("GNUPG_SCRIPTS_USE_UNSIGNED_KEYS=no\n")
            fw.close()
            return True
        except IOError:
            msg = _("Error writing script configuration file %s!") % self.srcconf.decode('UTF-8', 'replace')
            gpgmessages.displayMessage(msg, _("Error"), parent=self.parent)
        return False
