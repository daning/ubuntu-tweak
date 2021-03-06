#!/usr/bin/python

# Ubuntu Tweak - PyGTK based desktop configuration tool
#
# Copyright (C) 2007-2008 TualatriX <tualatrix@gmail.com>
#
# Ubuntu Tweak is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ubuntu Tweak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ubuntu Tweak; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import os
import gtk
import gio
import pango
import gobject
import thread
from gettext import ngettext

from ubuntutweak.modules  import TweakModule
from ubuntutweak.utils import icon
from ubuntutweak.common.gui import GuiWorker
from ubuntutweak.ui.dialogs import ErrorDialog

MIMETYPE = [
    (_('Audio'), 'audio', 'audio-x-generic'), 
    (_('Text'), 'text', 'text-x-generic'),
    (_('Image'), 'image', 'image-x-generic'), 
    (_('Video'), 'video', 'video-x-generic'), 
    (_('Application'), 'application', 'vcard'), 
    (_('All'), 'all', 'binary-x-generic'),
]

(
    COLUMN_ICON,
    COLUMN_TITLE,
    COLUMN_CATE,
) = range(3)

class CateView(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)

        self.set_rules_hint(True)
        self.model = self.__create_model()
        self.set_model(self.model)
        self.__add_columns()
        self.update_model()

        selection = self.get_selection()
        selection.select_iter(self.model.get_iter_first())
#        self.set_size_request(80, -1)

    def __create_model(self):
        '''The model is icon, title and the list reference'''
        model = gtk.ListStore(
                    gtk.gdk.Pixbuf,
                    gobject.TYPE_STRING,
                    gobject.TYPE_STRING)
        
        return model

    def __add_columns(self):
        column = gtk.TreeViewColumn(_('Categories'))

        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, pixbuf = COLUMN_ICON)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_sort_column_id(COLUMN_TITLE)
        column.set_attributes(renderer, text = COLUMN_TITLE)

        self.append_column(column)

    def update_model(self):
        for title, cate, icon_name in MIMETYPE:
            pixbuf = icon.get_from_name(icon_name)
            iter = self.model.append(None)
            self.model.set(iter, 
                    COLUMN_ICON, pixbuf, 
                    COLUMN_TITLE, title, 
                    COLUMN_CATE, cate)

(
    TYPE_MIME,
    TYPE_ICON,
    TYPE_DESCRIPTION,
    TYPE_APPICON,
    TYPE_APP,
) = range(5)

class TypeView(gtk.TreeView):
    update = False
    def __init__(self):
        gtk.TreeView.__init__(self)

        self.model = self.__create_model()
        self.set_search_column(TYPE_DESCRIPTION)
        self.set_model(self.model)
        self.set_rules_hint(True)
        self.__add_columns()
        self.model.set_sort_column_id(TYPE_DESCRIPTION, gtk.SORT_ASCENDING)

#        self.set_size_request(200, -1)
        self.update_model(filter = 'audio')

    def __create_model(self):
        '''The model is icon, title and the list reference'''
        model = gtk.ListStore(
                    gobject.TYPE_STRING,
                    gtk.gdk.Pixbuf,
                    gobject.TYPE_STRING,
                    gtk.gdk.Pixbuf,
                    gobject.TYPE_STRING,
                    )
        
        return model

    def __add_columns(self):
        column = gtk.TreeViewColumn(_('File Type'))
        column.set_resizable(True)

        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, pixbuf = TYPE_ICON)

        renderer = gtk.CellRendererText()
        renderer.set_fixed_size(180, -1)
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        column.pack_start(renderer, False)
        column.set_attributes(renderer, text = TYPE_DESCRIPTION)
        column.set_sort_column_id(TYPE_DESCRIPTION)
        self.append_column(column)

        column = gtk.TreeViewColumn(_('Associated Application'))

        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, pixbuf = TYPE_APPICON)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer, False)
        column.set_sort_column_id(TYPE_APP)
        column.set_attributes(renderer, text = TYPE_APP)

        self.append_column(column)

    def update_model(self, filter = False, all = False):
        self.model.clear()
        mainwindow = self.get_toplevel().window
        if mainwindow:
            mainwindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        while gtk.events_pending ():
            gtk.main_iteration ()

        for type in gio.content_types_get_registered():
            if filter and filter != type.split('/')[0]:
                continue

            pixbuf = icon.get_from_mime_type(type)
            description = gio.content_type_get_description(type)
            app = gio.app_info_get_default_for_type(type, False)

            if app:
                appname = app.get_name()
                applogo = icon.get_from_app(app)
            elif all and not app:
                appname = _('None')
                applogo = None
            else:
                continue
            
            iter = self.model.append()
            self.model.set(iter, 
                    TYPE_MIME, type,
                    TYPE_ICON, pixbuf, 
                    TYPE_DESCRIPTION, description,
                    TYPE_APPICON, applogo,
                    TYPE_APP, appname)

        if mainwindow:
            mainwindow.set_cursor(None)

    def update_for_type(self, type):
        self.model.foreach(self.do_update_for_type, type)

    def do_update_for_type(self, model, path, iter, type):
        this_type = model.get_value(iter, TYPE_MIME)

        if this_type == type:
            app = gio.app_info_get_default_for_type(type, False)

            if app:
                appname = app.get_name()
                applogo = icon.get_from_app(app)
                
                model.set(iter, 
                        TYPE_APPICON, applogo,
                        TYPE_APP, appname)
            else:
                model.set(iter, 
                        TYPE_APPICON, None,
                        TYPE_APP, _('None'))

(
    TYPE_ADD_APPINFO,
    TYPE_ADD_APPLOGO,
    TYPE_ADD_APPNAME,
) = range(3)


class AddAppDialog(gobject.GObject):
    __gsignals__ = {
        'update': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    def __init__(self, type, parent):
        super(AddAppDialog, self).__init__()

        worker = GuiWorker('type_edit.ui')

        self.dialog = worker.get_object('add_app_dialog') 
        self.dialog.set_modal(True)
        self.dialog.set_transient_for(parent)
        self.app_view = worker.get_object('app_view')
        self.setup_treeview()
        self.app_selection = self.app_view.get_selection()
        self.app_selection.connect('changed', self.on_app_selection_changed)

        self.info_label = worker.get_object('info_label')
        self.description_label = worker.get_object('description_label')

        self.info_label.set_markup(_('Open files of type "%s" with:') % gio.content_type_get_description(type))

        self.add_button = worker.get_object('add_button')
        self.add_button.connect('clicked', self.on_add_button_clicked)

        self.command_entry = worker.get_object('command_entry')
        self.browse_button = worker.get_object('browse_button')
        self.browse_button.connect('clicked', self.on_browse_button_clicked)

    def get_command_or_appinfo(self):
        command = self.command_entry.get_text()
        if command.startswith('/'):
            return command
        else:
            model, iter = self.app_selection.get_selected()
            if iter:
                return model.get_value(iter, TYPE_ADD_APPINFO)

    def get_command_runable(self):
        command = self.command_entry.get_text()
        if command.startswith('/'):
            if not os.access(command, os.X_OK):
                return False
            else:
                return True
        else:
            return True

    def on_browse_button_clicked(self, widget):
        dialog = gtk.FileChooserDialog(_('Choose an application'),
                action = gtk.FILE_CHOOSER_ACTION_OPEN, 
                buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                    gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
        dialog.set_current_folder('/usr/bin')

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            self.command_entry.set_text(dialog.get_filename())

        dialog.destroy()

    def on_app_selection_changed(self, widget):
        model, iter = widget.get_selected()
        if iter:
            appinfo = model.get_value(iter, TYPE_ADD_APPINFO)
            description = appinfo.get_description()

            if description:
                self.description_label.set_label(description)
            else:
                self.description_label.set_label('')

            self.command_entry.set_text(appinfo.get_executable())

    def on_add_button_clicked(self, widget):
        pass

    def setup_treeview(self):
        model = gtk.ListStore(gobject.GObject,
                              gtk.gdk.Pixbuf,
                              gobject.TYPE_STRING)

        self.app_view.set_model(model)
        self.app_view.set_headers_visible(False)

        column = gtk.TreeViewColumn()
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, pixbuf = TYPE_ADD_APPLOGO)
        
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, text = TYPE_ADD_APPNAME)
        column.set_sort_column_id(TYPE_DESCRIPTION)
        self.app_view.append_column(column)

        for appinfo in gio.app_info_get_all():
            if appinfo.supports_files() or appinfo.supports_uris():
                applogo = icon.get_from_app(appinfo)
                appname = appinfo.get_name()

                iter = model.append()
                model.set(iter, 
                        TYPE_ADD_APPINFO, appinfo,
                        TYPE_ADD_APPLOGO, applogo,
                        TYPE_ADD_APPNAME, appname)

    def __getattr__(self, key):
        return getattr(self.dialog, key)

(
    TYPE_EDIT_ENABLE,
    TYPE_EDIT_TYPE,
    TYPE_EDIT_APPINFO,
    TYPE_EDIT_APPLOGO,
    TYPE_EDIT_APPNAME,
) = range(5)

class TypeEditDialog(gobject.GObject):
    __gsignals__ = {
        'update': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    def __init__(self, types, parent):
        super(TypeEditDialog, self).__init__()
        self.types = types

        type_pixbuf = icon.get_from_mime_type(self.types[0], 64)
        worker = GuiWorker('type_edit.ui')

        self.dialog = worker.get_object('type_edit_dialog')
        self.dialog.set_transient_for(parent)
        self.dialog.set_modal(True)
        self.dialog.connect('destroy', self.on_dialog_destroy)

        type_logo = worker.get_object('type_edit_logo')
        type_logo.set_from_pixbuf(type_pixbuf)

        type_label = worker.get_object('type_edit_label')

        if len(self.types) > 1:
            markup_text = ", ".join([gio.content_type_get_description(filetype) for filetype in self.types])
        else:
            markup_text = self.types[0]

        type_label.set_markup(ngettext('Select an application to open files of type: <b>%s</b>',
                              'Select an application to open files for these types: <b>%s</b>',
                              len(self.types)) % markup_text)

        self.type_edit_view = worker.get_object('type_edit_view')
        self.setup_treeview()

        add_button = worker.get_object('type_edit_add_button')
        add_button.connect('clicked', self.on_add_button_clicked)

        remove_button = worker.get_object('type_edit_remove_button')
        # remove button should not available in multiple selection
        if len(self.types) > 1:
            remove_button.hide()
        remove_button.connect('clicked', self.on_remove_button_clicked)

        close_button = worker.get_object('type_edit_close_button')
        close_button.connect('clicked', self.on_dialog_destroy)

    def on_add_button_clicked(self, widget):
        dialog = AddAppDialog(self.types[0], widget.get_toplevel())
        if dialog.run() == gtk.RESPONSE_ACCEPT:
            if dialog.get_command_runable():
                we = dialog.get_command_or_appinfo()
                if type(we) == gio.unix.DesktopAppInfo:
                    app = we
                else:
                    app = gio.AppInfo(we)
                for filetype in self.types:
                    app.set_as_default_for_type(filetype)

                self.update_model()
                self.emit('update', self.types)
            else:
                ErrorDialog(_('Could not find %s') % dialog.get_command_or_appinfo(),
                        title = _('Could not find application')).launch()
                
        dialog.destroy()

    def on_remove_button_clicked(self, widget):
        model, iter = self.type_edit_view.get_selection().get_selected()

        if iter:
            type, appinfo = model.get(iter, TYPE_EDIT_TYPE, TYPE_EDIT_APPINFO)
            appinfo.remove_supports_type(type)

            self.update_model()

        self.emit('update', type)

    def setup_treeview(self):
        model = gtk.ListStore(
                gobject.TYPE_BOOLEAN,
                gobject.TYPE_STRING,
                gobject.GObject,
                gtk.gdk.Pixbuf,
                gobject.TYPE_STRING)

        self.type_edit_view.set_model(model)
        self.type_edit_view.set_headers_visible(False)

        self.model = model

        column = gtk.TreeViewColumn()
        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_renderer_toggled)
        renderer.set_radio(True)
        column.pack_start(renderer, False)
        column.set_attributes(renderer, active = TYPE_EDIT_ENABLE)
        self.type_edit_view.append_column(column)

        column = gtk.TreeViewColumn()
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, pixbuf = TYPE_EDIT_APPLOGO)
        
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, False)
        column.set_attributes(renderer, text = TYPE_EDIT_APPNAME)
        column.set_sort_column_id(TYPE_DESCRIPTION)
        self.type_edit_view.append_column(column)

        self.update_model()

    def update_model(self):
        self.model.clear()

        if len(self.types) > 1:
            app_dict = {}
            default_list = []
            for type in self.types:
                def_app = gio.app_info_get_default_for_type(type, False)

                for appinfo in gio.app_info_get_all_for_type(type):
                    appname = appinfo.get_name()
                    if def_app.get_name() == appname and appname not in default_list:
                        default_list.append(appname)

                    if not app_dict.has_key(appname):
                        app_dict[appname] = appinfo

            for appname, appinfo in app_dict.items():
                applogo = icon.get_from_app(appinfo)
                iter = self.model.append()
                if len(default_list) == 1 and appname in default_list:
                    enabled = True
                else:
                    enabled = False

                self.model.set(iter, 
                        TYPE_EDIT_ENABLE, enabled,
                        TYPE_EDIT_TYPE, '',
                        TYPE_EDIT_APPINFO, appinfo,
                        TYPE_EDIT_APPLOGO, applogo,
                        TYPE_EDIT_APPNAME, appname)
        else:
            type = self.types[0]
            def_app = gio.app_info_get_default_for_type(type, False)

            for appinfo in gio.app_info_get_all_for_type(type):
                applogo = icon.get_from_app(appinfo)
                appname = appinfo.get_name()

                iter = self.model.append()
                self.model.set(iter, 
                        TYPE_EDIT_ENABLE, def_app.get_name() == appname,
                        TYPE_EDIT_TYPE, type,
                        TYPE_EDIT_APPINFO, appinfo,
                        TYPE_EDIT_APPLOGO, applogo,
                        TYPE_EDIT_APPNAME, appname)

    def on_renderer_toggled(self, widget, path):
        model = self.type_edit_view.get_model()
        iter = model.get_iter(path)

        enable, type, appinfo = model.get(iter, TYPE_EDIT_ENABLE, TYPE_EDIT_TYPE, TYPE_EDIT_APPINFO)
        if not enable:
            model.foreach(self.cancenl_last_toggle)
            for filetype in self.types:
                appinfo.set_as_default_for_type(filetype)
            model.set(iter, TYPE_EDIT_ENABLE, not enable)
            self.emit('update', self.types)

    def cancenl_last_toggle(self, model, path, iter):
        enable = model.get(iter, TYPE_EDIT_ENABLE)
        if enable:
            model.set(iter, TYPE_EDIT_ENABLE, not enable)

    def on_dialog_destroy(self, widget):
        self.destroy()

    def __getattr__(self, key):
        return getattr(self.dialog, key)

class FileType(TweakModule):
    __title__ = _('File Type Manager')
    __desc__ = _('Manage all registered file types')
    __icon__ = 'application-x-theme'
    __category__ = 'system'

    def __init__(self):
        TweakModule.__init__(self)

        hbox = gtk.HBox(False, 5)
        self.add_start(hbox)

        self.cateview = CateView()
        self.cate_selection = self.cateview.get_selection()
        self.cate_selection.connect('changed', self.on_cateview_changed)
        hbox.pack_start(self.cateview, False, False, 0)

        self.typeview = TypeView()
        self.typeview.connect('row-activated', self.on_row_activated)
        self.type_selection = self.typeview.get_selection()
        self.type_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.type_selection.connect('changed', self.on_typeview_changed)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.typeview)
        hbox.pack_start(sw)

        hbox = gtk.HBox(False, 5)
        self.add_start(hbox, False, False, 0)

        self.edit_button = gtk.Button(stock=gtk.STOCK_EDIT)
        self.edit_button.connect('clicked', self.on_edit_clicked)
        self.edit_button.set_sensitive(False)
        hbox.pack_end(self.edit_button, False, False, 0)

        self.show_have_app = gtk.CheckButton(_('Only show filetypes with associated applications'))
        self.show_have_app.set_active(True)
        self.show_have_app.connect('toggled', self.on_show_all_toggled)
        hbox.pack_start(self.show_have_app, False, False, 5)

        self.show_all()

    def on_row_activated(self, widget, path, col):
        self.on_edit_clicked(widget)

    def on_show_all_toggled(self, widget):
        model, iter = self.cate_selection.get_selected()
        type = False
        if iter:
            type = model.get_value(iter, COLUMN_CATE)
            self.set_update_mode(type)

    def on_cateview_changed(self, widget):
        model, iter = widget.get_selected()
        if iter:
            type = model.get_value(iter, COLUMN_CATE)
            self.set_update_mode(type)

    def on_typeview_changed(self, widget):
        model, rows = widget.get_selected_rows()
        if len(rows) > 0:
            self.edit_button.set_sensitive(True)
        else:
            self.edit_button.set_sensitive(False)

    def on_edit_clicked(self, widget):
        model, rows = self.type_selection.get_selected_rows()
        if len(rows) > 0:
            types = []
            for path in rows:
                iter = model.get_iter(path)
                types.append(model.get_value(iter, TYPE_MIME))

            dialog = TypeEditDialog(types, self.get_toplevel())
            dialog.connect('update', self.on_mime_type_update)

            dialog.show()
        else:
            return

    def on_mime_type_update(self, widget, types):
        # types maybe just a string in single selection
        # and a list object format string in multiple selection
        if types[0] != "[" and types[-1] != "]":
            self.typeview.update_for_type(types)
        else:
            # convert string back to list object
            types = eval(types)
            for filetype in types:
                self.typeview.update_for_type(filetype)

    def set_update_mode(self, type):
        if type == 'all':
            self.typeview.update_model(all = not self.show_have_app.get_active())
        else:
            self.typeview.update_model(filter = type, all = not self.show_have_app.get_active())
