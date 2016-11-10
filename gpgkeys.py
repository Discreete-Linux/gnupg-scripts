"""
GnuPG-Scripts

Copyright (C) 2016 Discreete Linux Team <info@discreete-linux.org>

Module for handling GnuPG keys
"""

import os
from gi.repository import Gtk
import gettext
from datetime import date
import gpgconf
import gpgmessages
import gpgprocess
import gpgplatform

# Init translations
os.environ.setdefault("LANG", "en")
gettext.install("gnupg-scripts", unicode=1)


def strDate(d):
    """ Format key expiration date including the special case "never" """
    if d:
        return d.strftime("%x")
    else:
        return _("never")


class PubKeys(object):
    """ Class for accessing user's public keys """
    def __init__(self, parent, encryptOnly=True):
        """ read GnuPG configuration """
        self.parent = parent
        self.encryptOnly = encryptOnly
        self.srcconf = gpgconf.SrcConf()
        self.keylist = []
        self.readKeys()

    def readKeys(self):
        """ read all keys """
        try:
            ret = gpgprocess.gpg([ "--with-colons", "-k" ])
        except IOError:
            gpgmessages.startFailed(self.parent)
            return False
        for line in ret["stdout"]:
            if (line.startswith("pub:f:") or
                line.startswith("pub:m:") or
                line.startswith("pub:u:") or
                (self.srcconf.unsigned_keys and
                 (line.startswith("pub:-:") or
                  line.startswith("pub:q:")))):
                l = line.split(":")
                if len(l) < 12 or 'D' in l[11]:
                    continue
                if self.encryptOnly and 'e' not in l[11].lower():
                    continue
                kid = l[4]
                ld = l[5].split("-")
                if len(ld) == 3:
                    cdate = date(int(ld[0]), int(ld[1]), int(ld[2]))
                else:
                    cdate = None
                ld = l[6].split("-")
                if len(ld) == 3:
                    edate = date(int(ld[0]), int(ld[1]), int(ld[2]))
                else:
                    edate = None
                skid = kid[9:16]
                #name = gpgmessages.umlautConv(l[9].strip())
                name = l[9].strip()
                self.keylist.append([ kid, cdate, edate, name ])
            elif ((line.startswith("uid:f:") or
                   line.startswith("uid:m:") or
                   line.startswith("uid:u:") or
                   (self.srcconf.unsigned_keys and
                    (line.startswith("uid:-:") or
                     line.startswith("uid:q:")))) and self.keylist):
                    l = line.split(":")
                    self.keylist[-1][3] += "\n"
                    #self.keylist[-1][3] += gpgmessages.umlautConv(l[9].strip())
                    self.keylist[-1][3] += l[9].strip()
        return True

    def check_key(self, keyid):
        """ Check key for validity """
        result = [ "unknown", "" ]
        try:
            ret = gpgprocess.gpg([ "--with-colons", "-k", keyid ])
        except IOError:
            gpgmessages.startFailed(self.parent)
            return result
        for line in ret["stdout"]:
            if line.startswith("pub:"):
                l = line.split(":")
                if len(l) > 9:
                    #result[1] = gpgmessages.umlautConv(l[9].strip())
                    result[1] = l[9].strip()
                    if l[1] == "r" or l[1] == "e":
                        result[0] = l[1]
                    elif len(l) > 11 and 'D' in l[11]:
                        result[0] = "d"
                    elif not self.srcconf.unsigned_keys and l[1] == "-":
                        result[0] = "n"
                    elif self.encryptOnly and 'e' not in l[11].lower():
                        result[0] = "s"
                    else:
                        result[0] = "v"
                break
        return result


class SecKeys(object):
    """ Class for accessing user's private keys """
    def __init__(self, parent, encryptOnly=True):
        """ read GnuPG configuration """
        self.parent = parent
        self.encryptOnly = encryptOnly
        self.keylist = []
        self.readKeys()

    def readKeys(self):
        """ Read all secret keys """
        try:
            ret = gpgprocess.gpg([ "--with-colons", "-K" ])
        except IOError:
            gpgmessages.startFailed(self.parent)
            return
        for line in ret["stdout"]:
            if line.startswith("sec:"):
                l = line.split(":")
                if len(l) < 12:
                    continue
                kid = l[4]
                ld = l[5].split("-")
                if len(ld) == 3:
                    cdate = date(int(ld[0]), int(ld[1]), int(ld[2]))
                else:
                    cdate = None
                ld = l[6].split("-")
                if len(ld) == 3:
                    edate = date(int(ld[0]), int(ld[1]), int(ld[2]))
                else:
                    edate = None
                ret2 = gpgprocess.gpg([ "--with-colons", "-k", kid ])
                added = False
                for line in ret2["stdout"]:
                    if line.startswith("pub:"):
                        l = line.split(":")
                        if (len(l) > 11 and l[1] == "u" and 'D' not in l[11]):
                            if self.encryptOnly and 'e' not in l[11].lower():
                                continue
                            #name = gpgmessages.umlautConv(l[9].strip())
                            name = l[9].strip()
                            self.keylist.append([ kid, cdate, edate, name ])
                            added = True
                    elif added and line.startswith("uid:"):
                        l = line.split(":")
                        if len(l) > 9:
                            s = l[9].strip()
                            self.keylist[-1][3] += "\n"
                            #self.keylist[-1][3] += gpgmessages.umlautConv(s)
                            self.keylist[-1][3] += s
