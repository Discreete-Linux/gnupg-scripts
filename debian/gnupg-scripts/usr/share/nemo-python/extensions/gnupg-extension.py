#!/usr/bin/env python
# GnuPG Scripts Plugin for Nemo
#
# Part of "gnupg-scripts" Package
#
# Copyright 2010-2016 Discreete Linux Team <info@discreete-linux.org>
#
# Encoding: UTF-8
""" A nemo extension which interfaces to gnupg-scripts """
from gi.repository import GObject, Nemo
import gettext
import os
import subprocess
from multiprocessing import Process

class GnupgScriptsExtension(GObject.GObject, Nemo.MenuProvider):
    """ Allows encrypting arbitrary file types """
    def __init__(self):
        """ Init the extionsion. """
        print u"Initializing nemo-gnupg-scripts extension"

    def menu1_activate_cb(self, menu, myfiles):
        """ Encrypt file(s) """
        args = [ "gpg-encrypt" ]
        for myfile in myfiles:
            args.append(myfile.get_location().get_path())
        Process(target=subprocess.call, args=(args, )).start()
        return

    def menu2_activate_cb(self, menu, myfiles):
        """ Sign file """
        args = [ "gpg-sign" ]
        for myfile in myfiles:
            args.append(myfile.get_location().get_path())
        Process(target=subprocess.call, args=(args, )).start()
        return

    def is_valid_file(self, myfile):
        """ Check if myfile is a valid file for us """
        if ( ( myfile.get_uri_scheme() == 'file' ) or \
            ( myfile.get_uri_scheme() == 'smb' ) ):
            return True
        else:
            return False

    def get_file_items(self, window, files):
        """ Tell nemo whether and when to show the menu """
        if len(files) == 0:
            return
        myfile = files[0]
        if not self.is_valid_file(myfile):
            return
        item1 = Nemo.MenuItem(name='Nemo::gnupg_scripts_encrypt',
                                 label=gettext.dgettext('gnupg-scripts', 'Encrypt').decode('utf-8', 'replace'),
                                 tip=gettext.dgettext('gnupg-scripts', 'Encrypt the file(s) with GnuPG').decode('utf-8', 'replace'),
                                 icon="gnupg-scripts-encrypt")
        item1.connect('activate', self.menu1_activate_cb, files)
        item2 = Nemo.MenuItem(name='Nemo::gnupg_scripts_sign',
                                label=gettext.dgettext('gnupg-scripts', 'Sign').decode('utf-8', 'replace'),
                                tip=gettext.dgettext('gnupg-scripts', 'Signs the selected file with a detached signature').decode('utf-8', 'replace'),
                                icon="gnupg-scripts-sign")
        item2.connect('activate', self.menu2_activate_cb, files)
        return item1, item2,
