##
# 	\namespace	python.blurdev.gui.windows.loggerwindow.workboxwidget
#
# 	\remarks	A area to save and run code past the existing session
#
# 	\author		beta@blur.com
# 	\author		Blur Studio
# 	\date		03/17/11
#

from PyQt4.QtGui import QTextEdit
from PyQt4.QtCore import QEvent, Qt
from blurdev.ide.documenteditor import DocumentEditor
from PyQt4.QtGui import QApplication

import blurdev


class WorkboxWidget(DocumentEditor):
    def __init__(self, parent, console=None):
        # initialize the super class
        DocumentEditor.__init__(self, parent)

        self._console = console
        # define the user interface data

    #! 		finish initializing the class

    # create custom properties
    #! 		self._customProperty = ''

    # create connections
    #! 		self.uiNameTXT.textChanged.connect( self.setCustomProperty )

    def console(self):
        return self._console

    def execAll(self):
        """
            \remarks	reimplement the DocumentEditor.exec_ method to run this code without saving
        """
        exec unicode(self.text()).replace('\r', '\n') in locals(), globals()

    def execSelected(self):
        exec unicode(self.selectedText()).replace('\r', '\n') in locals(), globals()

    def execLine(self):
        line, index = self.getCursorPosition()
        exec unicode(self.text(line)).replace('\r', '\n') in locals(), globals()

    def setConsole(self, console):
        self._console = console
