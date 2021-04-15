# Copyright 2015    Christoph Reiter
#           2016-20 Nick Boultbee
#           2019    Peter Strulo
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from gi.repository import Gtk

from quodlibet import _
from quodlibet import config
from quodlibet.qltk.entry import UndoEntry
from quodlibet.qltk import Icons
from quodlibet.util.string import decode
from quodlibet.plugins.events import EventPlugin


def _config(section, option, label, tooltip=None, getter=None):
    def on_changed(entry, *args):
        config.settext(section, option, entry.get_text())

    entry = UndoEntry()
    if tooltip:
        entry.set_tooltip_text(tooltip)
    entry.set_text(config.gettext(section, option))
    entry.connect("changed", on_changed)

    def on_reverted(*args):
        config.reset(section, option)
        entry.set_text(config.gettext(section, option))

    revert = Gtk.Button()
    revert.add(Gtk.Image.new_from_icon_name(
        Icons.DOCUMENT_REVERT, Gtk.IconSize.BUTTON))
    revert.connect("clicked", on_reverted)

    lbl = Gtk.Label(label=label, use_underline=True)
    lbl.set_mnemonic_widget(entry)

    return (lbl, entry, revert)


def text_config(section, option, label, tooltip=None):
    def getter(section, option):
        return decode(config.get(section, option))

    return _config(section, option, label, tooltip, getter)


def boolean_config(section, option, label, tooltip):
    def on_reverted(*args):
        config.reset(section, option)
        button.set_active(config.getboolean(section, option))

    def __toggled(self, section, option):
        config.set(section, option, str(bool(self.get_active())).lower())

    default = config.getboolean(section, option)
    button = Gtk.CheckButton()
    button.set_active(config.getboolean(section, option, default))
    button.set_tooltip_text(tooltip)
    button.connect('toggled', __toggled, section, option)
    revert = Gtk.Button()
    revert.add(Gtk.Image.new_from_icon_name(Icons.DOCUMENT_REVERT, Gtk.IconSize.BUTTON))
    revert.connect("clicked", on_reverted)

    lbl = Gtk.Label(label=label, use_underline=True)
    lbl.set_mnemonic_widget(button)
    return lbl, button, revert


def int_config(section, option, label, tooltip):
    def getter(section, option):
        return str(config.getint(section, option))

    return _config(section, option, label, tooltip, getter)


class AdvancedPreferences(EventPlugin):
    PLUGIN_ID = "Advanced Preferences"
    PLUGIN_NAME = _("Advanced Preferences")
    PLUGIN_DESC = _("Allow editing of advanced config settings.")
    PLUGIN_CAN_ENABLE = False
    PLUGIN_ICON = Icons.PREFERENCES_SYSTEM

    def __init_defaults(self):
        self.__enabled = False

    def PluginPreferences(self, *args):
        def changed(entry, name, section="settings"):
            config.set(section, name, entry.get_text())

        vb = Gtk.VBox(spacing=12)

        # Tabulate all settings for neatness
        table = Gtk.Table(n_rows=14, n_columns=4)
        table.set_col_spacings(12)
        table.set_row_spacings(6)
        # We don't use translations as these things are internal
        # and don't want to burden the translators...
        # TODO: rethink translation here? (#3494)
        rows = [
            text_config(
                "editing", "id3encoding",
                "ID3 encodings:",
                ("ID3 encodings separated by spaces. "
                 "UTF-8 is always tried first, and Latin-1 is always tried last.")),
            text_config(
                "settings", "search_tags",
                "Search tags:",
                ("Tags which get searched in addition to "
                 "the ones present in the song list. Separate with \",\"")),
            text_config("settings", "rating_symbol_full", "Rating symbol (full):"),
            text_config("settings", "rating_symbol_blank", "Rating symbol (blank):"),
            int_config(
                "settings", "weight_smoothing_factor",
                "Weight smoothing factor:",
                ("This is used to smooth the length-based weights. Without smoothing, "
                 "very long songs would dominate an average value of an album. "
                 "At the same time, short good songs would have no affect on, for "
                 "example, the average rating of an album. "
                 "If this is -1 or less, averages are unweighted. "
                 "If this is 0, no smoothing is applied. (Default is 10)")),
            text_config(
                "player", "backend",
                "Backend:",
                "Identifier of the playback backend to use"),
            boolean_config(
                "settings", "disable_hints",
                "Disable hints:",
                "Disable popup windows (treeview hints)"),
            int_config(
                "browsers", "cover_size",
                "Album cover size:",
                ("Size of the album cover images in the album list browser "
                 "(restart required)")),
            boolean_config(
                "settings", "disable_mmkeys",
                "Disable multimedia keys:",
                "(restart required)"),
            text_config(
                "settings", "window_title_pattern",
                "Main window title:",
                ("A (tied) tag for the main window title, e.g. ~title~~people "
                 "(restart required)")),
            text_config(
                "settings", "datecolumn_timestamp_format",
                "DateColumn timestamp format",
                "A timestamp format, e.g. %Y%m%d %X "),
            text_config(
                "settings", "scrollbar_always_visible",
                "Scrollbars always visible:",
                ("Toggles whether the scrollbars on the bottom and side of "
                 "the window always are visible or get hidden when not in use "
                 "(restart required)")),
            boolean_config(
                "settings", "monospace_query",
                "Use monospace font for search input:",
                "Helps readability of code-like queries, but looks less consistent "
                "(restart required)"),
            text_config(
                "settings", "query_font_size",
                "Search input font size",
                "Size to apply to the search query entry, "
                "in any Pango CSS units, e.g. '100%', '1rem'. (restart required)"),
            boolean_config(
                "settings", "pangocairo_force_fontconfig",
                "Force Use Fontconfig Backend:",
                "It's not the default on win/macOS (restart required)"),
            text_config(
                "browsers", "ignored_characters",
                "Ignored characters: ",
                "Characters to ignore in queries"),
            boolean_config(
                "settings", "plugins_window_on_top",
                "Plugin window on top: ",
                "Toggles whether the plugin window appears on top of others")
        ]

        for (row, (label, widget, button)) in enumerate(rows):
            label.set_alignment(1.0, 0.5)
            table.attach(label, 0, 1, row, row + 1, xoptions=Gtk.AttachOptions.FILL)
            if isinstance(widget, Gtk.CheckButton):
                xoptions = Gtk.AttachOptions.FILL
                widget.set_alignment(0.0, 0.5)
                table.attach(widget, 1, 2, row, row + 1, xoptions=xoptions)
                # This stops checkbox from expanding too big, or shrinking text entries
                blank = Gtk.Label()
                table.attach(blank, 2, 3, row, row + 1,
                             xoptions=Gtk.AttachOptions.EXPAND)
            else:
                xoptions = Gtk.AttachOptions.FILL
                table.attach(widget, 1, 3, row, row + 1, xoptions=xoptions)
            table.attach(button, 3, 4, row, row + 1,
                         xoptions=Gtk.AttachOptions.SHRINK)

        def on_click(button):
            button.hide()
            table.set_no_show_all(False)
            table.show_all()

        button = Gtk.Button(label=_("I know what I'm doing"), use_underline=True)
        button.connect("clicked", on_click)
        vb.pack_start(button, True, True, 0)
        vb.pack_start(table, True, True, 0)
        table.set_no_show_all(True)

        return vb
