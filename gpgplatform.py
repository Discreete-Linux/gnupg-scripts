"""
GnuPG-Scripts

Copyright (C) 2016 Discreete Linux Team <info@discreete-linux.org>

Module for handling cross-platform issues
"""

import tempfile
import os

def gpg_binary():
    import os
    import sys
    for program in [ "gpg2", "gpg" ]:
        if sys.platform == "win32" and not program.endswith(".exe"):
            program += ".exe"
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
    return None

def gnupg_home(parent=None):
    if os.environ.get("GNUPGHOME"):
        return os.environ.get("GNUPGHOME").decode('utf-8', 'replace')
    elif os.environ.get("HOME"):
        return os.path.join(os.environ.get("HOME").decode('utf-8', 'replace'), u".gnupg")
    elif os.environ.get("AppData"):
        return os.path.join(os.environ.get("AppData").decode('utf-8', 'replace'), u"gnupg")
    else:
        return os.path.join(tempfile.gettempdir().decode('utf-8', 'replace'), u"gnupg")

def uidir():
    if os.path.exists("/usr/lib/gnupg-scripts"):
        return u"/usr/lib/gnupg-scripts"
    elif os.environ.get("ProgramFiles") and \
        os.path.exists(os.path.join(os.environ.get("ProgramFiles").decode('utf-8', 'replace'), u"gnupg-scripts")):
        return os.path.join(os.environ.get("ProgramFiles").decode('utf-8', 'replace'), u"gnupg-scripts")
    else:
        return os.getcwd()
