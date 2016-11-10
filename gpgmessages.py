"""
GnuPG-Scripts

Copyright (C) 2016 Discreete Linux Team <info@discreete-linux.org>

Module for handling GnuPG messages
"""
# Encoding: UTF-8
import os
from gi.repository import Gtk
import gettext
from datetime import datetime
import gpgkeys
import gpgprocess

# Init translations
os.environ.setdefault("LANG", "en")
gettext.install("gnupg-scripts", unicode=1)

def displayMessage(message, title=u"Error", type=Gtk.MessageType.ERROR, icon=None, parent=None):
    """ Display error and warning messages """
    if parent != None:
        flags = Gtk.DialogFlags.DESTROY_WITH_PARENT
    else:
        flags = 0
    md = Gtk.MessageDialog(parent, flags, type,
                                       Gtk.ButtonsType.CLOSE, message)
    md.set_position(Gtk.WindowPosition.CENTER)
    if icon:
        md.set_icon(icon)
    md.set_title(title)
    md.run()
    md.destroy()
    return True

def umlautConv(s):
    """ Replace escaped Umlaut's in key ids from windows keys """
    s = s.replace("\\x5c", "\\").replace("\\x3a", ":")
    if (("\\xc4" in repr(s)) or
        ("\\xd6" in repr(s)) or
        ("\\xdc" in repr(s)) or
        ("\\xe4" in repr(s)) or
        ("\\xf6" in repr(s)) or
        ("\\xfc" in repr(s)) or
        ("\\xdf" in repr(s))):
        return repr(s).decode("WINDOWS-1252", "replace")
    else:
        return s

def yesNoQuestion(msg, icon=None, title=None, parent=None):
    """ Ask a user question with yes/no response """
    answer = True
    opt = 0
    if parent:
        opt = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
    md = Gtk.MessageDialog(parent, opt, Gtk.MessageType.QUESTION,
                           Gtk.ButtonsType.YES_NO, msg)
    md.set_position(Gtk.WindowPosition.CENTER)
    if icon:
        md.set_icon(icon)
    if title:
        md.set_title(title)
    if md.run() == Gtk.ResponseType.NO:
        answer = False
    md.destroy()
    return answer

def startFailed(parent, icon=None, title=None):
    """ Issue an error when gpg cannot start """
    displayMessage(_("Can't start program gpg!"), title,
                   Gtk.MessageType.ERROR, icon, parent)

class GpgMessages(object):
    """ Class for parsing GnuPG messages """
    def __init__(self, icon, title, action):
        self._encto_msg = "[GNUPG:] ENC_TO"
        self._date_msg = "[GNUPG:] VALIDSIG"
        self._goodsig_msg = "[GNUPG:] GOODSIG"
        self._badsig_msg = "[GNUPG:] BADSIG"
        self._errsig_msg = "[GNUPG:] ERRSIG"
        self._keyexpire_msg = "[GNUPG:] KEYEXPIRED"
        self._expkeysig_msg = "[GNUPG:] EXPKEYSIG"
        self._faildec_msg = "[GNUPG:] DECRYPTION_FAILED"
        self._nodata_msg = "[GNUPG:] NODATA"
        self._nopass_msg = "[GNUPG:] MISSING_PASSPHRASE"
        self._uncomp_msg = "gpg: uncompressing failed:"
        self._packet_msg = "gpg: packet(1) with unknown version"
        self._handle_msg = "gpg: handle plaintext failed:"
        self._marker_msg = "gpg: invalid marker packet"
        self._cancel_msg = _("gpg: cancelled by user")
        self._orig_msg = _("gpg: original file name=")
        self._failsig_msg = _("gpg: the signature could not be verified.")
        self._warn_msg = _("gpg: WARNING:")
        self._fatal_msg = _("gpg: fatal: ")
        self._badpass_msg = _(": sign+encrypt failed: bad passphrase")
        self._badkey_msg = _(": sign+encrypt failed: unusable public key")
        self._failopen_msg = _("gpg: can't open `%s': ")
        self._skipped_msg = _(": skipped: public key already present")
        self.icon = icon
        self.title = title
        self.action = action
        self.failed = False
        self.signed = False
        self.badpass = False
        self.failopen = False
        self.badkey = False
        self.keys = ""
        self.signer = ""
        self.sigstate = ""
        self.origname = ""
        self.messages = ""
        self.date = datetime(1970, 1, 1)
        self.expire = datetime(1970, 1, 1)
        self.cancelled = False
        self.unchanged = False

        self.goodsig_msg = _("gpg: Good signature from ")
        self.badsig_msg = _("gpg: BAD signature from ")
        self.badpass_msg = _("Bad passphrase")
        self.badkey_msg = _("Unusable public key")
        self.failopen_msg = _("Can't open %s.")
        self.create_msg = _("Signature created ")
        self.damaged_msg = _("The signature %s seems to be damaged.")
        self.not_enc_msg = _("The file %s isn't PGP encrypted.\n")
        self.expired_msg = _("But signature key has expired on %s")
        self.unchanged_msg = _("not changed")
        self.failkey_msg = _("gpg: import from `%s' failed:")
        
    def getKey(self, line):
        """ Return key from line of text """
        key = _("unknown key")
        kid = line.strip().split(" ")[2]
        ret = gpgprocess.gpg([ "--with-colons", "-k", kid ])
        for line in ret["stdout"]:
            if line.startswith("pub:"):
                key = line.strip().split(":")[9]
                break
        else:
            key += " " + kid
        #self.keys += umlautConv(key) + "\n"
        self.keys += key + "\n"

    def getReason(self, fields):
        """ Get reason for failed signature verification """
        rc = int(fields[7])
        if rc == 9:
            reason = _("Missing public key: ") + fields[2]
        elif rc == 4:
            reason = _("Unknown algorithm")
        else:
            reason = _("Unknown reason")
        return reason

    def parse(self, filename, line):
        """ parse a line of gpg output """
        #linerepr = repr(line.strip()).strip("'")
        linerepr = line.strip()
        if (linerepr.startswith(self._cancel_msg) or
            linerepr.startswith(self._nopass_msg)):
            self.cancelled = True
        elif linerepr.startswith(self._encto_msg):
            self.getKey(linerepr)
        elif linerepr.startswith(self._orig_msg):
            self.origname = linerepr.strip().split("=", 1)[1].strip("'").decode('utf-8', 'replace')
        elif linerepr.startswith(self._date_msg):
            timestamp = linerepr.strip().split(" ")[4]
            self.date = datetime.fromtimestamp(float(timestamp))
            self.signed = True
        elif linerepr.startswith(self._keyexpire_msg):
            if not self.sigstate or self.sigstate == "valid":
                self.sigstate = "expired"
            timestamp = linerepr.strip().split(" ")[2]
            self.expire = datetime.fromtimestamp(float(timestamp))
        elif (linerepr.startswith(self._faildec_msg) and
              (self.action != "check") and (not self.cancelled)):
            self.failed = True
            msg = (filename + ":\n" + _("gpg: decryption failed:") + "\n" +
                   _("File encrypted with:\n") + self.keys)
            displayMessage(msg, self.title, icon=self.icon)
        elif linerepr.endswith(self._badkey_msg):
            self.badkey = True
            self.failed = True
        elif linerepr.startswith(self._goodsig_msg):
            self.signed = True
            if self.sigstate != "expired":
                self.sigstate = "valid"
            self.signer = linerepr.strip().split(" ", 3)[3].decode('utf-8', 'replace')
        elif linerepr.startswith(self._badsig_msg):
            self.signed = True
            self.sigstate = "bad"
            self.signer = linerepr.strip().split(" ", 3)[3].decode('utf-8', 'replace')
        elif linerepr.startswith(self._expkeysig_msg):
            self.signed = True
            self.signer = linerepr.strip().split(" ", 3)[3].decode('utf-8', 'replace')
        elif linerepr.startswith(self._errsig_msg):
            fields = linerepr.strip().split(" ")
            self.date = datetime.fromtimestamp(float(fields[6]))
            msg = (filename + ":\n" + _("gpg: Can't check signature:") + "\n" +
                   self.getReason(fields) + "\n" + self.create_msg +
                   str(self.date))
            displayMessage(msg, self.title, Gtk.MessageType.WARNING, self.icon)
            self.signed = True
        elif linerepr.startswith(self._warn_msg):
            msg = filename + ":\n" + line[5:]
            displayMessage(msg, self.title, Gtk.MessageType.WARNING, self.icon)
        elif (linerepr.startswith(self._nodata_msg) or
              linerepr.startswith(self._failsig_msg)):
            self.failed = True
            msg = filename + ":\n"
            if self.action == "verify":
                msg += self.damaged_msg % filename
            elif self.action == "decrypt":
                msg += self.not_enc_msg % filename
            if self.action != "check":
                displayMessage(msg, self.title)
        elif (linerepr.startswith(self._uncomp_msg) or
              linerepr.startswith(self._packet_msg ) or
              linerepr.startswith(self._handle_msg) or
              linerepr.startswith(self._marker_msg)):
            self.failed = True
            msg = self.not_enc_msg % filename
            if self.action != "check":
                displayMessage(msg, self.title, icon=self.icon)
        elif linerepr.startswith(self._fatal_msg):
            self.failed = True
            msg = _("A fatal error occurred:\n") + line[len(self._fatal_msg):]
            if self.action != "check":
                displayMessage(msg, self.title, icon=self.icon)
        elif linerepr.endswith(self._badpass_msg):
            self.badpass = True
        elif linerepr.startswith(self._failopen_msg % filename):
            if self.action != "encrypt":
                msg = self.failopen_msg % filename
                displayMessage(msg, self.title, Gtk.MessageType.ERROR,
                               self.icon)
            self.failopen = True
        elif linerepr.endswith(self.unchanged_msg):
            self.unchanged = True
        elif linerepr.startswith(self.failkey_msg % filename):
            self.failed = True
        elif linerepr.endswith(self._skipped_msg):
            pass
        else:
            j = linerepr.rfind(": ")
            if j >= 0:
                line = line[j + 2:]
            if not line in self.messages:
                self.messages += line
        return True
