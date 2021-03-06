#  PACKAGE
#
#  Copyright (C) 2016 Discreete Linux Team <info@discreete-linux.org>
#
###
# Standard-Variablen, die angepasst werden müssen
PYMODS = gpgconf.py gpgkeys.py gpgmessages.py gpgprocess.py gpgplatform.py
BINFILES =
USRBINFILES = gpg-encrypt gpg-decrypt gpg-sign gpg-verify gpg-properties
USRBINFILES += gpg-import gpg-config gpg-group-edit
USRBINFILES += gpg-janitor
EXTENSIONS = gnupg-extension.py
MENUFILES = gnupg-scripts-config.desktop gpg-decrypt.desktop
MENUFILES += gpg-properties.desktop gnupg-scripts-group-edit.desktop
MENUFILES += gpg-import.desktop gpg-verify.desktop
MENUFILES += gnupg-scripts-janitor.desktop
EXTRATARGETS = 
EXTRAINSTALLS = 
###
# Automatische Variablen
NAME = $(shell grep '^Package: ' debian/control | sed 's/^Package: //')
VERSION = $(shell grep '^Version: ' debian/control | sed 's/^Version: //')
PYTHON_VERSION = $(shell python -V 2>&1 | cut -f 2 -d ' ')
PYMINOR := $(shell echo $(PYTHON_VERSION) | cut -f 2 -d '.')
PYMAJOR := $(shell echo $(PYTHON_VERSION) | cut -f 1 -d '.')
BINDIR = $(DESTDIR)/bin
USRBINDIR = $(DESTDIR)/usr/bin
MENUDIR = $(DESTDIR)/usr/share/applications
ICONDIR = $(DESTDIR)/usr/share/icons/gnome
EXTDIR = $(DESTDIR)/usr/share/nemo-python/extensions
LIBDIR = $(DESTDIR)/usr/lib/$(NAME)
LANGDIR = $(DESTDIR)/usr/share/locale
ifeq ($(PYMAJOR),3)
PYLIBDIR = $(DESTDIR)/usr/lib/python3/dist-packages
else
PYLIBDIR = $(DESTDIR)/usr/lib/python2.$(PYMINOR)/dist-packages
endif
ICONS = $(wildcard icons)
UIFILES = $(wildcard *.ui)
POFILES=$(wildcard *.po)
MOFILES=$(addprefix $(LANGDIR)/,$(POFILES:.po=/LC_MESSAGES/$(NAME).mo))
###
# Weitere lokale Variablen

###
# Standard-Rezepte
all:	$(EXTRATARGETS)

clean:
	rm -rf *.pyc

distclean:
	rm -rf *.pyc *.gz $(EXTRATARGETS)
	
pot:	$(BINFILES) $(USRBINFILES) $(UIFILES) $(EXTENSIONS) $(PYLIBS)
	xgettext -L python -d $(NAME) -o $(NAME).pot \
	--package-name=$(NAME) --package-version=$(VERSION) \
	--msgid-bugs-address=info@discreete-linux.org $(BINFILES) $(USRBINFILES) \
	$(EXTENSIONS) $(PYLIBS)
ifneq ($(UIFILES),)
	xgettext -L Glade -d $(NAME) -j -o $(NAME).pot \
	--package-name=$(NAME) --package-version=$(VERSION) \
	--msgid-bugs-address=info@discreete-linux.org $(UIFILES)
endif

update-pot:	$(NAME).pot

update-po:	$(NAME).pot
	for pofile in $(POFILES); do msgmerge -U --lang=$${pofile%.*} $$pofile $(NAME).pot; done

install:	install-bin install-extension install-icon install-lang install-lib install-ui install-usrbin install-usrsbin install-menu $(EXTRAINSTALLS)

install-bin:	$(BINFILES)
ifneq ($(BINFILES),)
	mkdir -p $(BINDIR)
	install -m 0755 $(BINFILES) $(BINDIR)
endif	

install-extension:	$(EXTENSIONS)
ifneq ($(EXTENSIONS),)
	mkdir -p $(EXTDIR)
	install -m 0644 $(EXTENSIONS) $(EXTDIR)
endif
	
install-icon:	$(ICONS)
ifneq ($(ICONS),)
	mkdir -p $(ICONDIR)
	cp -r $(ICONS)/* $(ICONDIR)
endif
	
install-lang:	$(MOFILES)

$(LANGDIR)/%/LC_MESSAGES/$(NAME).mo: %.po
	mkdir -p $(dir $@)
	msgfmt -c -o $@ $*.po	

install-lib:	$(PYMODS)
ifneq ($(PYMODS),)
	mkdir -p $(PYLIBDIR)
	install -m 0644 $(PYMODS) $(PYLIBDIR)	
endif

install-ui:	$(UIFILES)
ifneq ($(UIFILES),)
	mkdir -p $(LIBDIR)
	install -m 0644 $(UIFILES) $(LIBDIR)
endif
	
install-usrbin:	$(USRBINFILES)
ifneq ($(USRBINFILES),)
	mkdir -p $(USRBINDIR)
	install -m 0755 $(USRBINFILES) $(USRBINDIR)
endif

install-usrsbin:	$(USRSBINFILES)
ifneq ($(USRSBINFILES),)
	mkdir -p $(USRSBINDIR)
	install -m 0755 $(USRSBINFILES) $(USRSBINDIR)
endif

install-menu:	$(MENUFILES)
ifneq ($(MENUFILES),)
	mkdir -p $(MENUDIR)
	install -m 0755 $(MENUFILES) $(MENUDIR)
endif
.PHONY:	all clean distclean install
