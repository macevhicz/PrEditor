##
# 	\namespace	blurdev.ide.config.[module]
#
# 	\remarks	Edit the addon properties for the IDE
#
# 	\author		eric.hulser@drdstudios.com
# 	\author		Dr. D Studios
# 	\date		07/08/11
#

from __future__ import absolute_import
import re
import blurdev

from Qt import QtCompat
from Qt.QtCore import QSize
from Qt.QtGui import QColor, QFont
from Qt.QtWidgets import QApplication, QColorDialog, QTreeWidgetItem

from blurdev.gui.dialogs.configdialog import ConfigSectionWidget


class ColorItem(QTreeWidgetItem):
    def __init__(self, key, color):
        super(ColorItem, self).__init__(['', self.prettyText(key)])
        self.setBackground(0, color)
        self.setSizeHint(0, QSize(40, 30))
        self._key = key

    def key(self):
        return self._key

    def color(self):
        return self.background(0).color()

    def prettyText(self, key):
        text = key.split('_')[-1]
        text = text[0].upper() + text[1:]
        return ' '.join(re.findall('[A-Z][^A-Z]*', text))

    def setColor(self, color):
        self.setBackground(0, color)


class SchemeConfig(ConfigSectionWidget):
    def initUi(self):
        # load the ui
        import blurdev.gui

        blurdev.gui.loadUi(__file__, self)

        # initialize the sizing
        for tree in (self.uiApplicationColorTREE, self.uiPageColorTREE):
            header = tree.header()
            QtCompat.QHeaderView.setSectionResizeMode(
                header, 0, header.ResizeToContents
            )
            QtCompat.QHeaderView.setSectionResizeMode(header, 1, header.Stretch)
            tree.setColumnWidth(0, 40)
            tree.installEventFilter(self)

        self.uiApplicationColorTREE.itemDoubleClicked.connect(self.editItemColor)
        self.uiPageColorTREE.itemDoubleClicked.connect(self.editItemColor)

    def editItemColor(self, item):
        color = QColorDialog.getColor(item.color())
        if color.isValid():
            item.setColor(color)

    def recordUi(self):
        """records the latest ui settings to the data"""
        section = self.section()

        # record application settings
        font = QFont(self.uiApplicationFontDDL)
        font.setPointSize(self.uiApplicationFontSizeSPN.value())
        section.setValue('application_font', font.toString())
        section.setValue('application_tree_indent', self.uiTreeIndentSPN.value())

        # record application colors
        for i in range(self.uiApplicationColorTREE.topLevelItemCount()):
            item = self.uiApplicationColorTREE.topLevelItem(i)
            section.setValue(item.key(), item.color())

        section.setValue(
            'application_override_colors', self.uiApplicationColorGRP.isChecked()
        )
        section.setValue(
            'document_override_colors', self.uiDocumentColorGRP.isChecked()
        )

        # record document settings
        font = QFont(self.uiPageFontDDL.currentFont())
        font.setPointSize(self.uiPageFontSizeSPN.value())

        section.setValue('document_font', font.toString())

        font = QFont(self.uiPageMarginFontDDL.currentFont())
        font.setPointSize(self.uiPageMarginFontSizeSPN.value())

        section.setValue('document_marginFont', font.toString())

        section.setValue(
            'document_EnableFontResize', self.uiEnableFontResizeCHK.isChecked()
        )

        # record document colors
        for i in range(self.uiPageColorTREE.topLevelItemCount()):
            item = self.uiPageColorTREE.topLevelItem(i)
            section.setValue(item.key(), item.color())

    def refreshUi(self):
        """refreshes the ui with the latest data settings"""
        section = self.section()

        # restore application settings
        font = QFont()
        font.fromString(section.value('application_font'))
        self.uiApplicationFontDDL.setCurrentFont(font)
        self.uiApplicationFontSizeSPN.setValue(font.pointSize())
        self.uiTreeIndentSPN.setValue(section.value('application_tree_indent'))

        # restore document settings
        font = QFont()
        font.fromString(section.value('document_font'))
        self.uiPageFontDDL.setCurrentFont(QFont(font.family()))
        self.uiPageFontSizeSPN.setValue(font.pointSize())

        font = QFont()
        font.fromString(section.value('document_marginFont'))
        self.uiPageMarginFontDDL.setCurrentFont(QFont(font.family()))
        self.uiPageMarginFontSizeSPN.setValue(font.pointSize())

        self.uiEnableFontResizeCHK.setChecked(
            section.value('document_EnableFontResize')
        )

        # include override options
        self.uiApplicationColorGRP.setChecked(
            section.value('application_override_colors')
        )
        self.uiDocumentColorGRP.setChecked(section.value('document_override_colors'))

        # restore colors
        keys = sorted(section.properties())
        for key in keys:
            if '_color_' not in key:
                continue

            item = ColorItem(key, section.value(key))
            if key.startswith('document'):
                self.uiPageColorTREE.addTopLevelItem(item)
            else:
                self.uiApplicationColorTREE.addTopLevelItem(item)


def registerSections(configSet):
    """registers one or many new sections to the config system

    Args:
        configSet (blurdev.gui.dialogs.configdialog.ConfigSet):
    """

    # define section
    group = 'Editor'
    section = 'Scheme'
    icon = blurdev.relativePath(__file__, 'img/schemeconfig.png')
    cls = SchemeConfig

    afont = QApplication.font()
    apalette = QApplication.palette()

    # set default font information
    dfont = QFont()
    dfont.setFamily('Courier New')
    dfont.setFixedPitch(True)
    dfont.setPointSize(9)

    # set default margin font
    mfont = QFont(dfont)
    mfont.setPointSize(9)

    dbackground = QColor('white')

    params = {
        # application scheme settings
        'application_font': afont.toString(),
        'application_override_colors': False,
        'application_color_window': apalette.color(apalette.Window),
        'application_color_windowText': apalette.color(apalette.WindowText),
        'application_color_background': apalette.color(apalette.Base),
        'application_color_alternateBackground': apalette.color(apalette.AlternateBase),
        'application_color_text': apalette.color(apalette.Text),
        'application_color_highlight': apalette.color(apalette.Highlight),
        'application_color_highlightedText': apalette.color(apalette.HighlightedText),
        'application_tree_indent': 20,
        # document scheme settings
        'document_override_colors': False,
        'document_font': dfont.toString(),
        'document_marginFont': mfont.toString(),
        'document_EnableFontResize': True,
        'document_color_currentLine': dbackground,
        'document_color_cursor': QColor('black'),
        'document_color_background': dbackground,
        'document_color_method': QColor('darkBlue'),
        'document_color_text': QColor('black'),
        'document_color_comment': QColor('darkGreen'),
        'document_color_keyword': QColor('darkBlue'),
        'document_color_keywordBackground': dbackground,
        'document_color_number': QColor('darkRed'),
        'document_color_string': QColor('darkOrange'),
        'document_color_operator': QColor('darkRed'),
        'document_color_regex': QColor('darkRed'),
        'document_color_margins': QColor(224, 224, 224),
        'document_color_marginsText': QColor('black'),
        'document_color_foldMargin': QColor('white'),
        'document_color_foldMarginText': QColor('black'),
        'document_color_indentGuide': QColor('black'),
        'document_color_invalidBrace': QColor('red'),
        'document_color_braceHighlight': QColor('yellow'),
        'document_color_braceBackground': dbackground,
        'document_color_braceText': QColor('black'),
        'document_color_markerForeground': QColor('white'),
        'document_color_markerBackground': QColor('black'),
        'document_color_controlCharacter': QColor('blue'),
        'document_color_lineNumber': QColor('black'),
        'document_color_highlight': apalette.color(apalette.Highlight),
        'document_color_highlightText': apalette.color(apalette.HighlightedText),
        'document_color_limitColumn': QColor('red'),
        'document_color_misc': QColor(200, 200, 200),
        'document_color_attribute': QColor('darkOrange'),
        'document_color_tag': QColor('darkBlue'),
        'document_color_entity': QColor('darkBlue'),
        'document_color_error': QColor('darkRed'),
        'document_color_smartHighlight': QColor(64, 112, 144),
        'document_color_smartHighlightBackground': QColor(155, 255, 155),
    }

    # register the section to the configset
    configSet.registerSection(section, cls, params, group=group, icon=icon)
