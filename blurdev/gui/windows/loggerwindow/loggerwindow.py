##
# 	\namespace	blurdev.gui.windows.loggerwindow.loggerwindow
#
# 	\remarks	LoggerWindow class is an overloaded python interpreter for blurdev
#
# 	\author		beta@blur.com
# 	\author		Blur Studio
# 	\date		01/15/08
#

from blurdev.gui import Window
from blurdev import prefs
from PyQt4.QtGui import QSplitter, QKeySequence, QIcon, QColor
from PyQt4.QtCore import Qt
import blurdev


class LoggerWindow(Window):
    _instance = None

    def __init__(self, parent):
        Window.__init__(self, parent)
        self.aboutToClearPathsEnabled = False

        import blurdev.gui

        blurdev.gui.loadUi(__file__, self)

        # create the splitter layout
        self.uiSplitterSPLIT = QSplitter(self)

        # create the console widget
        from console import ConsoleEdit

        self.uiConsoleTXT = ConsoleEdit(self.uiSplitterSPLIT)
        self.uiConsoleTXT.setMinimumHeight(1)

        # create the workbox
        from workboxwidget import WorkboxWidget

        self.uiWorkboxWGT = WorkboxWidget(self.uiSplitterSPLIT)
        self.uiWorkboxWGT.setConsole(self.uiConsoleTXT)
        self.uiWorkboxWGT.setMinimumHeight(1)

        # Store the software name so we can handle custom keyboard shortcuts bassed on software
        self._software = blurdev.core.objectName()

        # create the layout
        from PyQt4.QtGui import QVBoxLayout

        layout = QVBoxLayout()
        layout.addWidget(self.uiSplitterSPLIT)
        self.centralWidget().setLayout(layout)

        # create the connections
        blurdev.core.debugLevelChanged.connect(self.refreshDebugLevels)

        self.uiCloseLoggerACT.triggered.connect(self.closeLogger)

        self.uiNewScriptACT.triggered.connect(blurdev.core.newScript)
        self.uiOpenScriptACT.triggered.connect(blurdev.core.openScript)
        self.uiOpenIdeACT.triggered.connect(blurdev.core.showIdeEditor)
        self.uiRunScriptACT.triggered.connect(blurdev.core.runScript)
        self.uiGotoErrorACT.triggered.connect(self.gotoError)

        self.uiNoDebugACT.triggered.connect(self.setNoDebug)
        self.uiDebugLowACT.triggered.connect(self.setLowDebug)
        self.uiDebugMidACT.triggered.connect(self.setMidDebug)
        self.uiDebugHighACT.triggered.connect(self.setHighDebug)

        self.uiRunAllACT.triggered.connect(self.execAll)
        self.uiRunSelectedACT.triggered.connect(self.execSelected)

        self.uiAutoCompleteEnabledACT.toggled.connect(self.setAutoCompleteEnabled)
        self.uiIndentationsTabsACT.toggled.connect(
            self.uiWorkboxWGT.setIndentationsUseTabs
        )
        self.uiWordWrapACT.toggled.connect(self.setWordWrap)
        self.uiResetPathsACT.triggered.connect(self.resetPaths)
        self.uiSdkBrowserACT.triggered.connect(self.showSdk)
        self.uiClearLogACT.triggered.connect(self.clearLog)
        self.uiSaveConsoleSettingsACT.triggered.connect(self.recordPrefs)
        self.uiClearBeforeRunningACT.triggered.connect(self.setClearBeforeRunning)
        self.uiEditorVerticalACT.toggled.connect(self.adjustWorkboxOrientation)
        blurdev.core.aboutToClearPaths.connect(self.pathsAboutToBeCleared)

        self.uiNewScriptACT.setIcon(QIcon(blurdev.resourcePath('img/ide/newfile.png')))
        self.uiOpenScriptACT.setIcon(QIcon(blurdev.resourcePath('img/ide/open.png')))
        self.uiOpenIdeACT.setIcon(QIcon(blurdev.resourcePath('img/ide.png')))
        self.uiRunScriptACT.setIcon(QIcon(blurdev.resourcePath('img/ide/run.png')))
        self.uiNoDebugACT.setIcon(QIcon(blurdev.resourcePath('img/debug_off.png')))
        self.uiDebugLowACT.setIcon(QIcon(blurdev.resourcePath('img/debug_low.png')))
        self.uiDebugMidACT.setIcon(QIcon(blurdev.resourcePath('img/debug_mid.png')))
        self.uiDebugHighACT.setIcon(QIcon(blurdev.resourcePath('img/debug_high.png')))
        self.uiResetPathsACT.setIcon(QIcon(blurdev.resourcePath('img/reset.png')))
        self.uiClearLogACT.setIcon(QIcon(blurdev.resourcePath('img/ide/clearlog.png')))
        self.uiSaveConsoleSettingsACT.setIcon(
            QIcon(blurdev.resourcePath('img/savesettings.png'))
        )
        self.uiCloseLoggerACT.setIcon(QIcon(blurdev.resourcePath('img/ide/close.png')))

        # Make action shortcuts available anywhere in the Logger
        self.addAction(self.uiClearLogACT)

        # refresh the ui
        self.refreshDebugLevels()
        self.uiWorkboxWGT.setLanguage('Python')
        self.uiWorkboxWGT.setShowSmartHighlighting(True)

        # Ensure the workbox lexer colors are set to sane defaults
        # applications like maya cause the lexer to have bad default colors
        # TODO: This could probably be stored in prefs so its customizable.
        self._paperColor = {
            0: (255, 255, 255, 255),
            1: (255, 255, 255, 255),
            2: (255, 255, 255, 255),
            3: (255, 255, 255, 255),
            4: (255, 255, 255, 255),
            5: (255, 255, 255, 255),
            6: (255, 255, 255, 255),
            7: (255, 255, 255, 255),
            8: (255, 255, 255, 255),
            9: (255, 255, 255, 255),
            10: (255, 255, 255, 255),
            11: (255, 255, 255, 255),
            12: (255, 255, 255, 255),
            13: (224, 192, 224, 255),
            14: (155, 255, 155, 255),
            15: (255, 255, 255, 255),
        }
        self._textColor = {
            0: (128, 128, 128, 255),
            1: (0, 127, 0, 255),
            2: (0, 127, 127, 255),
            3: (127, 0, 127, 255),
            4: (127, 0, 127, 255),
            5: (0, 0, 127, 255),
            6: (127, 0, 0, 255),
            7: (127, 0, 0, 255),
            8: (0, 0, 255, 255),
            9: (0, 127, 127, 255),
            10: (0, 0, 0, 255),
            11: (0, 0, 0, 255),
            12: (127, 127, 127, 255),
            13: (0, 0, 0, 255),
            14: (64, 112, 144, 255),
            15: (128, 80, 0, 255),
        }
        lex = self.uiWorkboxWGT.lexer()
        for key, value in self._paperColor.iteritems():
            lex.setPaper(QColor(*value), key)
        for key, value in self._textColor.iteritems():
            lex.setColor(QColor(*value), key)
        lex.setDefaultPaper(QColor(255, 255, 255, 255))
        self.uiWorkboxWGT.setMarginsFont(self.uiWorkboxWGT.font())

        # calling setLanguage resets this value to False
        self.restorePrefs()
        self.overrideKeyboardShortcuts()
        self.uiConsoleTOOLBAR.show()
        import sys, platform

        self.setWindowTitle(
            'Python Logger - %s %s'
            % ('%i.%i.%i' % sys.version_info[:3], platform.architecture()[0])
        )

    def adjustWorkboxOrientation(self, state):
        if state:
            self.uiSplitterSPLIT.setOrientation(Qt.Horizontal)
        else:
            self.uiSplitterSPLIT.setOrientation(Qt.Vertical)

    def console(self):
        return self.uiConsoleTXT

    def clearLog(self):
        self.uiConsoleTXT.clear()

    def closeEvent(self, event):
        self.recordPrefs()
        Window.closeEvent(self, event)
        if self.uiConsoleTOOLBAR.isFloating():
            self.uiConsoleTOOLBAR.hide()

    def closeLogger(self):
        self.close()

    def execAll(self):
        """
            \remarks	Clears the console before executing all workbox code
        """
        if self.uiClearBeforeRunningACT.isChecked():
            self.clearLog()
        self.uiWorkboxWGT.execAll()

    def execSelected(self):
        """
            \remarks	Clears the console before executing selected workbox code
        """
        if self.uiClearBeforeRunningACT.isChecked():
            self.clearLog()
        self.uiWorkboxWGT.execSelected()

    def gotoError(self):
        text = self.uiConsoleTXT.textCursor().selectedText()
        import re

        results = re.match('[ \t]*File "([^"]+)", line (\d+)', unicode(text))
        if results:
            from blurdev.ide import IdeEditor

            IdeEditor.instance().show()
            filename, lineno = results.groups()
            IdeEditor.instance().load(filename, int(lineno))

    def overrideKeyboardShortcuts(self):
        """
            \remarks	If a specific software has limitations preventing keyboard shortcuts from working, they can be overidden here
                        Example: Softimage treats both enter keys as Qt.Key_Enter, It ignores Qt.Key_Return
        """
        if self._software == 'softimage':
            self.uiRunSelectedACT.setShortcut(
                QKeySequence(Qt.Key_Enter + Qt.ShiftModifier)
            )
            self.uiRunAllACT.setShortcut(
                QKeySequence(Qt.Key_Enter + Qt.ControlModifier)
            )

    def pathsAboutToBeCleared(self):
        if self.uiClearLogOnRefreshACT.isChecked():
            self.clearLog()

    def refreshDebugLevels(self):
        from blurdev.debug import DebugLevel, debugLevel

        dlevel = debugLevel()
        for act, level in [
            (self.uiNoDebugACT, 0),
            (self.uiDebugLowACT, DebugLevel.Low),
            (self.uiDebugMidACT, DebugLevel.Mid),
            (self.uiDebugHighACT, DebugLevel.High),
        ]:
            act.blockSignals(True)
            act.setChecked(level == dlevel)
            act.blockSignals(False)

    def resetPaths(self):
        blurdev.activeEnvironment().resetPaths()

    def recordPrefs(self):
        pref = prefs.find('blurdev\LoggerWindow')
        pref.recordProperty('loggergeom', self.geometry())
        pref.recordProperty('windowState', self.windowState().__int__())
        pref.recordProperty('WorkboxText', self.uiWorkboxWGT.text())
        pref.recordProperty('SplitterVertical', self.uiEditorVerticalACT.isChecked())
        pref.recordProperty('SplitterSize', self.uiSplitterSPLIT.sizes())
        pref.recordProperty('tabIndent', self.uiIndentationsTabsACT.isChecked())
        pref.recordProperty('hintingEnabled', self.uiAutoCompleteEnabledACT.isChecked())
        pref.recordProperty('wordWrap', self.uiWordWrapACT.isChecked())
        pref.recordProperty(
            'clearBeforeRunning', self.uiClearBeforeRunningACT.isChecked()
        )
        pref.recordProperty(
            'clearBeforeEnvRefresh', self.uiClearLogOnRefreshACT.isChecked()
        )
        pref.recordProperty(
            'disableSdkShortcut', self.uiDisableSDKShortcutACT.isChecked()
        )
        pref.recordProperty('toolbarStates', self.saveState())
        pref.recordProperty('consoleFont', self.uiConsoleTXT.font())
        lexer = self.uiWorkboxWGT.lexer()
        if lexer:
            font = lexer.font(0)
        else:
            font = self.uiWorkboxWGT.font()
        pref.recordProperty('workboxFont', font)
        pref.recordProperty('workboxMarginFont', self.uiWorkboxWGT.marginsFont())
        pref.save()

    def restorePrefs(self):
        pref = prefs.find('blurdev\LoggerWindow')
        rect = pref.restoreProperty('loggergeom')
        if rect and not rect.isNull():
            self.setGeometry(rect)
        self.uiWorkboxWGT.setText(pref.restoreProperty('WorkboxText', ''))
        self.uiEditorVerticalACT.setChecked(
            pref.restoreProperty('SplitterVertical', False)
        )
        self.adjustWorkboxOrientation(self.uiEditorVerticalACT.isChecked())
        sizes = pref.restoreProperty('SplitterSize', None)
        if sizes:
            self.uiSplitterSPLIT.setSizes(sizes)
        self.setWindowState(Qt.WindowStates(pref.restoreProperty('windowState', 0)))
        self.uiIndentationsTabsACT.setChecked(pref.restoreProperty('tabIndent', True))
        self.uiWorkboxWGT.setIndentationsUseTabs(self.uiIndentationsTabsACT.isChecked())
        self.uiAutoCompleteEnabledACT.setChecked(
            pref.restoreProperty('hintingEnabled', True)
        )
        self.uiConsoleTXT.completer().setEnabled(
            self.uiAutoCompleteEnabledACT.isChecked()
        )
        self.uiWordWrapACT.setChecked(pref.restoreProperty('wordWrap', True))
        self.setWordWrap(self.uiWordWrapACT.isChecked())
        self.uiClearBeforeRunningACT.setChecked(
            pref.restoreProperty('clearBeforeRunning', False)
        )
        self.uiClearLogOnRefreshACT.setChecked(
            pref.restoreProperty('clearBeforeEnvRefresh', False)
        )
        self.uiDisableSDKShortcutACT.setChecked(
            pref.restoreProperty('disableSdkShortcut', False)
        )
        self.setClearBeforeRunning(self.uiClearBeforeRunningACT.isChecked())
        font = pref.restoreProperty('consoleFont', None)
        if font:
            self.uiConsoleTXT.setFont(font)
        font = pref.restoreProperty('workboxFont', None)
        if font:
            lexer = self.uiWorkboxWGT.lexer()
            if lexer:
                font = lexer.setFont(font, 0)
            else:
                font = self.uiWorkboxWGT.setFont(font)
        font = pref.restoreProperty('workboxMarginFont', None)
        if font:
            self.uiWorkboxWGT.setMarginsFont(font)
        self.restoreToolbars()

    def restoreToolbars(self):
        pref = prefs.find('blurdev\LoggerWindow')
        state = pref.restoreProperty('toolbarStates', None)
        if state:
            self.restoreState(state)

    def setAutoCompleteEnabled(self, state):
        self.uiConsoleTXT.completer().setEnabled(state)
        if state:
            self.uiWorkboxWGT.setAutoCompletionSource(self.uiWorkboxWGT.AcsAll)
        else:
            self.uiWorkboxWGT.setAutoCompletionSource(self.uiWorkboxWGT.AcsNone)

    def setClearBeforeRunning(self, state):
        if state:
            self.uiRunSelectedACT.setIcon(
                QIcon(blurdev.resourcePath('img/ide/runselectedclear.png'))
            )
            self.uiRunAllACT.setIcon(
                QIcon(blurdev.resourcePath('img/ide/runallclear.png'))
            )
        else:
            self.uiRunSelectedACT.setIcon(
                QIcon(blurdev.resourcePath('img/ide/runselected.png'))
            )
            self.uiRunAllACT.setIcon(QIcon(blurdev.resourcePath('img/ide/runall.png')))

    def setNoDebug(self):
        from blurdev import debug

        debug.setDebugLevel(None)

    def setLowDebug(self):
        from blurdev import debug

        debug.setDebugLevel(debug.DebugLevel.Low)

    def setMidDebug(self):
        from blurdev import debug

        debug.setDebugLevel(debug.DebugLevel.Mid)

    def setHighDebug(self):
        from blurdev import debug

        debug.setDebugLevel(debug.DebugLevel.High)

    def setWordWrap(self, state):
        if state:
            self.uiConsoleTXT.setLineWrapMode(self.uiConsoleTXT.WidgetWidth)
        else:
            self.uiConsoleTXT.setLineWrapMode(self.uiConsoleTXT.NoWrap)

    def showEvent(self, event):
        super(LoggerWindow, self).showEvent(event)
        self.restoreToolbars()
        self.uiWorkboxWGT.setIndentationsUseTabs(self.uiIndentationsTabsACT.isChecked())

    def showSdk(self):
        if not self.uiDisableSDKShortcutACT.isChecked():
            blurdev.core.sdkBrowser().show()

    def shutdown(self):
        # close out of the ide system

        # if this is the global instance, then allow it to be deleted on close
        if self == LoggerWindow._instance:
            self.setAttribute(Qt.WA_DeleteOnClose, True)
            LoggerWindow._instance = None

        # clear out the system
        self.close()

    @staticmethod
    def instance(parent=None):
        # create the instance for the logger
        if not LoggerWindow._instance:
            # determine default parenting
            if not (parent or blurdev.core.isMfcApp()):
                parent = blurdev.core.rootWindow()

            # create the logger instance
            inst = LoggerWindow(parent)

            # protect the memory
            inst.setAttribute(Qt.WA_DeleteOnClose, False)

            # cache the instance
            LoggerWindow._instance = inst

        return LoggerWindow._instance

    @classmethod
    def instanceShutdown(cls):
        """ Faster way to shutdown the instance of LoggerWindow if it possibly was not used. Returns if shutdown was required.
            :return: Bool. Shutdown was requried
        """
        if cls._instance:
            cls._instance.shutdown()
            return True
        return False
