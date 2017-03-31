import os
import sys
import time
import smtplib

from PyQt4.QtCore import QObject, pyqtSignal, QEvent, QDateTime, Qt, SIGNAL, QRect
from PyQt4.QtGui import (
    QApplication,
    QWidget,
    QFileDialog,
    QMessageBox,
    QSplashScreen,
    QMainWindow,
    QDialog,
)

import blurdev
import blurdev.prefs
import blurdev.debug
import blurdev.osystem
import blurdev.tools
import blurdev.tools.tool
import blurdev.tools.toolsenvironment
import blurdev.cores.application
import blurdev.settings


class Core(QObject):
    """
    The Core class provides all the main shared functionality and signals that need to be distributed between different pacakges.
    """

    # ----------------------------------------------------------------
    # blurdev signals
    environmentActivated = pyqtSignal()
    debugLevelChanged = pyqtSignal()
    fileCheckedIn = pyqtSignal(str)
    fileCheckedOut = pyqtSignal(str)
    aboutToClearPaths = pyqtSignal()  # emited before environment is changed or reloaded
    styleSheetChanged = pyqtSignal(str)

    # ----------------------------------------------------------------
    # 3d Application Signals (common)
    # Depreciated, use blur3d signals

    # scene signals
    sceneClosed = pyqtSignal()
    sceneExportRequested = pyqtSignal()
    sceneExportFinished = pyqtSignal()
    sceneImportRequested = pyqtSignal()
    sceneImportFinished = pyqtSignal()
    sceneInvalidated = pyqtSignal()
    sceneMergeRequested = pyqtSignal()
    sceneMergeFinished = pyqtSignal()
    sceneNewRequested = pyqtSignal()
    sceneNewFinished = pyqtSignal()
    sceneOpenRequested = pyqtSignal(str)
    sceneOpenFinished = pyqtSignal(str)
    sceneReset = pyqtSignal()
    sceneSaveRequested = pyqtSignal(str)
    sceneSaveFinished = pyqtSignal(str)

    # layer signals
    layerCreated = pyqtSignal()
    layerDeleted = pyqtSignal()
    layersModified = pyqtSignal()
    layerStateChanged = pyqtSignal()

    # object signals
    selectionChanged = pyqtSignal()

    # render signals
    rednerFrameRequested = pyqtSignal(int)
    renderFrameFinished = pyqtSignal()
    renderSceneRequested = pyqtSignal(list)
    renderSceneFinished = pyqtSignal()

    # time signals
    currentFrameChanged = pyqtSignal(int)
    frameRangeChanged = pyqtSignal()

    # application signals
    startupFinished = pyqtSignal()
    shutdownStarted = pyqtSignal()

    # the event id for Queue Processing
    qProcessID = 15648

    # ----------------------------------------------------------------

    def __init__(self, hwnd=0, objectName=None):
        QObject.__init__(self)
        if objectName == None:
            objectName = 'blurdev'
        QObject.setObjectName(self, objectName)

        # create custom properties
        self._protectedModules = []
        self._hwnd = hwnd
        self._keysEnabled = True
        self._lastFileName = ''
        self._mfcApp = False
        self._logger = None
        self._supportsDocking = False
        self._linkedSignals = {}
        self._itemQueue = []
        self._maxDelayPerCycle = 0.1
        self._stylesheet = None
        self._headless = False
        self._useAppUserModelID = None
        self.environment_override_filepath = os.environ.get(
            'BDEV_ENVIRONMENT_OVERRIDE_FILEPATH', ''
        )
        # When Using Fusion, this will be populated with a PeyeonScript.scriptapp connected to
        # the parent fusion process. Otherwise this will be None
        self.fusionApp = None

        # create the connection to the environment activiation signal
        self.environmentActivated.connect(self.registerPaths)
        self.environmentActivated.connect(self.recordSettings)
        self.debugLevelChanged.connect(self.recordSettings)

    def activeWindow(self):
        if QApplication.instance():
            return QApplication.instance().activeWindow()
        return None

    def addLibraryPaths(self, app):
        # Set library paths so qt plugins, image formats, sql drivers, etc can be loaded if needed
        if sys.platform != 'win32':
            return
        if blurdev.osystem.getPointerSize() == 64:
            app.addLibraryPath("c:/windows/system32/blur64/")
        else:
            app.addLibraryPath("c:/blur/common/")

    def configUpdated(self):
        """ Preform any core specific updating of config. Returns if any actions were taken.
        """
        return False

    def connectAppSignals(self):
        """ Connect the signals emitted by the application we're in to the blurdev core system
        """
        pass

    def connectPlugin(
        self, hInstance, hwnd, style='Plastique', palette=None, stylesheet=''
    ):
        """ Creates a QMfcApp instance for the inputed plugin and window if no app is currently running

            :param int hInstance:
            :param int hwnd:
            :param str style:
            :param QPalette palette:
            :param str stylesheet:
            :returns: bool for success

        """

        # check to see if there is an application already running
        if not QApplication.instance():
            if sys.platform == 'win32':  # shitty
                from PyQt4.QtWinMigrate import QMfcApp
            # create the plugin instance
            if QMfcApp.pluginInstance(hInstance):
                self.setHwnd(hwnd)
                self._mfcApp = True

                app = QApplication.instance()
                if app:
                    app.setStyle(style)
                    if palette:
                        app.setPalette(palette)
                    if stylesheet:
                        app.setStylesheet(stylesheet)

                    # initialize the logger
                    if not self.headless:
                        self.logger()

                return True
        return False

    def createToolMacro(self, tool, macro=''):
        """ Method to create macros for a tool, should be overloaded per core
        """
        blurdev.osystem.createShortcut(
            tool.displayName(),
            tool.sourcefile(),
            icon=tool.icon(),
            description=tool.toolTip(),
        )

        return True

    def defaultEnvironmentPath(self):
        return os.path.normpath(
            os.environ['BDEV_MASTER_TOOLS_ENV_CONFIG']
            % {'filepath': blurdev.resourcePath()}
        )

    def disableKeystrokes(self):
        # disable the client keystrokes
        self._keysEnabled = False

    def dispatch(self, signal, *args):
        """ Dispatches a string based signal through the system from an application
        """
        if self.signalsBlocked():
            return

        # emit a defined pyqtSignal
        if (
            hasattr(self, signal)
            and type(getattr(self, signal)).__name__ == 'pyqtBoundSignal'
        ):
            getattr(self, signal).emit(*args)

        # otherwise emit a custom signal
        else:
            self.emit(SIGNAL(signal), *args)

        # emit linked signals
        if signal in self._linkedSignals:
            for trigger in self._linkedSignals[signal]:
                self.dispatch(trigger)

    def emitEnvironmentActivated(self):
        if not self.signalsBlocked():
            self.environmentActivated.emit()

            # This records the last time a user deliberately changed the
            # environment.  If the environment has a timeout, it will use
            # this timestamp to enforce the timeout.
            pref = blurdev.prefs.find('blurdev/core', coreName=self.objectName())
            pref.recordProperty(
                'environment_set_timestamp', QDateTime.currentDateTime()
            )
            pref.save()

    def emitDebugLevelChanged(self):
        if not self.signalsBlocked():
            self.debugLevelChanged.emit()

    def enableKeystrokes(self):
        # enable the client keystrokes
        self._keysEnabled = True

    def flashWindow(self, window=None, dwFlags=None, count=1, timeout=0, hwnd=None):
        """ Flashes the application depending on the os.

        On Windows this calls FlashWindowEx. See this documentation.
        http://docs.activestate.com/activepython/2.7/pywin32/win32gui__FlashWindowEx_meth.html
        https://msdn.microsoft.com/en-us/library/ms679348(v=vs.85).aspx

        Args:
            window (QWidget|None): This widget will be flashed. Attempts to get the hwnd from
                this widget. Note: This is ignored if hwnd is passed in.
            dwFlags (win32con.FLASHW_*): A enum value used to control the flashing behavior.
                See https://msdn.microsoft.com/en-us/library/ms679348(v=vs.85).aspx for more
                details. Defaults to win32con.FLASHW_TIMERNOFG.
            count (int): The number of times to flash the window. Defaults to 1.
            timeout (int): The rate at which the window is to be flashed in milliseconds.
                if zero is passed, the default cursor blink rate is used.

        Returns:
            bool: Was anything attempted. On windows this always returns True.
        """
        if blurdev.settings.OS_TYPE == 'Windows':
            from win32gui import FlashWindowEx

            if dwFlags is None:
                import win32con

                dwFlags = win32con.FLASHW_TIMERNOFG
            if hwnd is None:
                if window is None:
                    if self.isMfcApp():
                        hwnd = self.hwnd()
                    else:
                        hwnd = self.rootWindow().winId().__int__()
                else:
                    hwnd = window.winId().__int__()

            FlashWindowEx(hwnd, dwFlags, count, timeout)
            return True
        return False

    def runOnDccStartup(self):
        """ When starting a DCC like 3ds Max, execute this code on startup.

        This provides a location for defining additional startup behavior when a DCC is initalized.
        Currently it is used to check if trax should be imported on startup and if the studio.internal scene callbacks should be initalized.

        This module is safe to call without trax or blur3d being installed.
        """
        # Don't run studio callbacks in this dcc when in quiet mode(rendering) or if its
        # disabled by the environment variable BDEV_TRAX_ON_DCC_STARTUP.
        enableTraxOnDccStartup = os.environ.get(
            'BDEV_TRAX_ON_DCC_STARTUP', 'true'
        ).lower()
        if not self.quietMode() and enableTraxOnDccStartup == 'true':
            try:
                # A full trax install is required to work with the blur specific blur3d api
                import trax

                if trax.isValid:
                    # Initializing the pipe layer of blur3d.
                    # On import trax.api will be imported and studio specific signals will be connected.
                    # See the studio/internal/__init__.py for more information.
                    import studio.internal
            # This is to prevent errors if modules do not exist.
            except ImportError:
                pass

    def errorCoreText(self):
        """ Returns text that is included in the error email for the active core. Override in subclasses to provide extra data.
            If a empty string is returned this line will not be shown in the error email.
        """
        return ''

    def event(self, event):
        if event.type() == self.qProcessID:
            # process the next item in the queue
            self.processQueueItem()
            return True
        return False

    def eventFilter(self, object, event):

        # Events that enable client keystrokes
        if event.type() in (QEvent.FocusOut, QEvent.HoverLeave, QEvent.Leave):
            self.enableKeystrokes()

        # Events that disable client keystrokes
        if event.type() in (
            QEvent.FocusIn,
            QEvent.MouseButtonPress,
            QEvent.Enter,
            QEvent.ToolTip,
            QEvent.HoverMove,
            QEvent.KeyPress,
        ):
            self.disableKeystrokes()

        return QObject.eventFilter(self, object, event)

    def linkSignals(self, signal, trigger):
        """ Creates a dependency so that when the inputed signal is dispatched, the dependent trigger signal is also dispatched.  This will only work
            for trigger signals that do not take any arguments for the dispatch.
        """
        if not signal in self._linkedSignals:
            self._linkedSignals[signal] = [trigger]
        elif not trigger in self._linkedSignals[signal]:
            self._linkedSignals[signal].append(trigger)

    def shouldReportException(self, exctype, value, traceback_):
        """ Allow the core to control if the Python Logger shows the ErrorDialog or a email is sent.

        Use this to prevent a exception from prompting the user to open the Python Logger, and
        prevent sending a error email. This is called after parent eventhandler's are called and
        the traceback will still be printed to the logger after this function is run.

        This function returns two boolean values, the first controls if a error email should be sent.
        The second controls if the ErrorDialog should be shown.

        Args:
            exctype (type): The Exception class.
            value : The Exception instance.
            traceback_ (traceback): The traceback object.

        Returns:
            sendEmail: Should the exception be reported in a error email.
            showPrompt: Should the ErrorDialog be shown if the Python Logger isnt already visible.
        """
        return True, True

    def init(self):
        """ Initializes the core system
        """
        ret = self.initCore()
        self.initGui()
        return ret

    def initCore(self):
        """Work method to initialize the core system -- breaking the initialization apart allows the
        gui-dependant initialization to be delayed in applications where that is necessary by
        overloading init().
        """
        # register protected modules
        # do not want to affect this module during environment switching
        self.protectModule('blurdev')
        # we should never remove main. If we do in specific cases it will prevent external tools from
        # running if they use "if __name__ == '__main__':" as __name__ will return None
        self.protectModule('__main__')

        # initialize the tools environments
        blurdev.tools.toolsenvironment.ToolsEnvironment.loadConfig(
            self.defaultEnvironmentPath()
        )

        # 		# Gets the override filepath, it is defined this way, instead of
        # 		# being defined in the class definition, so that we can change this
        # 		# path, or remove it entirely for offline installs.
        # 		self.environment_override_filepath = os.environ.get('BDEV_ENVIRONMENT_OVERRIDE_FILEPATH', '')

        # initialize the application
        app = QApplication.instance()
        output = None

        if app:
            if self.isMfcApp():
                # disable all UI effects as this is quite slow in MFC applications
                app.setEffectEnabled(Qt.UI_AnimateMenu, False)
                app.setEffectEnabled(Qt.UI_FadeMenu, False)
                app.setEffectEnabled(Qt.UI_AnimateCombo, False)
                app.setEffectEnabled(Qt.UI_AnimateTooltip, False)
                app.setEffectEnabled(Qt.UI_FadeTooltip, False)
                app.setEffectEnabled(Qt.UI_AnimateToolBox, False)
                app.aboutToQuit.connect(self.recordToolbars)
                app.installEventFilter(self)
            self.addLibraryPaths(app)

        # create a new application
        else:
            from blurdev.cores.application import CoreApplication, Application

            # Check for headless environment's
            if blurdev.settings.OS_TYPE == 'Linux':
                if os.environ.get('DISPLAY') == None:
                    output = CoreApplication([])
                    self._headless = True
            if output == None:
                output = Application([])
            self.addLibraryPaths(output)

        # restore the core settings
        self.restoreSettings()
        self.connectAppSignals()
        return output

    def initGui(self):
        """Initialize the portions of the core that require GUI initialization to have completed.
        """
        self.restoreToolbars()

    def applyEnvironmentTimeouts(self):
        """
        Checks the current environment to see if has a timeout and if it has
        exceeded that timeout.  If so, it will reset the environment to the
        default environment.

        """
        env = blurdev.tools.toolsenvironment.ToolsEnvironment.activeEnvironment()
        threshold_time = env.timeoutThreshold()
        pref = blurdev.prefs.find('blurdev/core', coreName=self.objectName())
        last_timestamp = pref.restoreProperty('environment_set_timestamp', None)

        if not last_timestamp:
            return

        if last_timestamp < threshold_time:
            env = blurdev.tools.toolsenvironment.ToolsEnvironment.defaultEnvironment()
            print 'Environment timeout exceeded, Resetting to default environment:', env.objectName()
            env.setActive()
            pref.recordProperty(
                'environment_set_timestamp', QDateTime.currentDateTime()
            )
            pref.save()

    def applyStudioOverrides(self):
        """
        Checks a studio environment override file.  If there

        """
        # Checks for the studio environment override file
        override_dict = self.getEnvironmentOverride()
        if not override_dict:
            return

        env = override_dict['environment']
        timestamp = override_dict['timestamp']
        pref = blurdev.prefs.find('blurdev/core', coreName=self.objectName())
        last_timestamp = pref.restoreProperty(
            'last_environment_override_timestamp', None
        )
        if last_timestamp and last_timestamp >= timestamp:
            return
        blurdev.tools.toolsenvironment.ToolsEnvironment.findEnvironment(env).setActive()
        pref.recordProperty(
            'last_environment_override_timestamp', QDateTime.currentDateTime()
        )
        pref.save()

    def isMfcApp(self):
        return self._mfcApp

    @property
    def headless(self):
        """ If true, no Qt gui elements should be used because python is running a QCoreApplication. """
        return self._headless

    def hwnd(self):
        if self.objectName() == 'assfreezer':
            return int(self.rootWindow().winId())
        return self._hwnd

    def ideeditor(self, parent=None):
        from blurdev.ide.ideeditor import IdeEditor

        return IdeEditor.instance(parent)

    def isKeystrokesEnabled(self):
        return self._keysEnabled

    def lastFileName(self):
        return self._lastFileName

    def logger(self, parent=None):
        """ Creates and returns the logger instance
        """
        from blurdev.gui.windows.loggerwindow import LoggerWindow

        return LoggerWindow.instance(parent)

    def lovebar(self, parent=None):
        from blurdev.tools.toolslovebar import ToolsLoveBarDialog

        return ToolsLoveBarDialog.instance(parent)

    def macroName(self):
        """
        Returns the name to display for the create macro action in treegrunt
        """
        return 'Create Desktop Shortcut...'

    def mainWindowGeometry(self):
        """ QWinWidget doesn't properly center its children.

        In MFC apps this function returns the size of the main window. Note: Qt doesn't include the
        titlebar so the position may be off by that ammount.
        """
        if self.headless:
            raise Exception('You are showing a gui in a headless environment. STOP IT!')
        return QRect()

    def maxDelayPerCycle(self):
        return self._maxDelayPerCycle

    def newScript(self):
        """
        Creates a new script window for editing
        """
        from blurdev.ide.ideeditor import IdeEditor

        IdeEditor.createNew()

    def openScript(self, filename=''):
        """
        Opens the an existing script in a new window for editing
        """
        if not filename:
            # make sure there is a QApplication running
            if QApplication.instance():
                filename = str(
                    QFileDialog.getOpenFileName(
                        None,
                        'Select Script File',
                        self._lastFileName,
                        'Python Files (*.py);;Maxscript Files (*.ms);;All Files (*.*)',
                    )
                )
                if not filename:
                    return

        if filename:
            self._lastFileName = filename
            from blurdev.ide.ideeditor import IdeEditor

            IdeEditor.edit(filename=filename)

    def postQueueEvent(self):
        """
        Insert a call to processQueueItem on the next event loop
        """
        QApplication.postEvent(self, QEvent(self.qProcessID))

    def processQueueItem(self):
        """
        Call the current queue item and post the next queue event if it exists
        """
        if self._itemQueue:
            if self._maxDelayPerCycle == -1:
                self._runQueueItem()
            else:
                t = time.time()
                t2 = t
                while self._itemQueue and (t2 - t) < self._maxDelayPerCycle:
                    t2 = time.time()
                    self._runQueueItem()
            if self._itemQueue:
                # if there are still items in the queue process the next item
                self.postQueueEvent()

    def _runQueueItem(self):
        """
        Process the top item on the queue, catch the error generated if the underlying c/c++ object has been deleted, and alow the queue to continue processing.
        """
        try:
            item = self._itemQueue.pop(0)
            item[0](*item[1], **item[2])
        except RuntimeError, check:
            if str(check) != 'underlying C/C++ object has been deleted':
                if self._itemQueue:
                    self.postQueueEvent()
                raise
        except Exception, value:
            if self._itemQueue:
                self.postQueueEvent()
            raise

    def protectModule(self, moduleName):
        """
        Registers the inputed module name for protection from tools environment switching
        """
        key = str(moduleName)
        if key not in self._protectedModules:
            self._protectedModules.append(str(moduleName))

    def protectedModules(self):
        """
        Returns the modules that should not be affected when a tools environment changes
        """
        return self._protectedModules

    def pyular(self, parent=None):
        from blurdev.gui.widgets.pyularwidget import PyularDialog

        return PyularDialog.instance(parent)

    def quietMode(self):
        """
        Use this to decide if you should provide user input.
        """
        return False

    def registerPaths(self):
        """
        Registers the paths that are needed based on this core
        """
        env = blurdev.tools.toolsenvironment.ToolsEnvironment.activeEnvironment()

        # Canonical way to check 64-bitness of python interpreter
        # http://docs.python.org/2/library/platform.html#platform.architecture
        is_64bits = hasattr(sys, 'maxsize') and sys.maxsize > (2 ** 32)
        # Add Python24 specific libraries
        if sys.version_info[:2] == (2, 4):
            path = 'code/python/lib_python24'
            env.registerPath(env.relativePath(path))
        # Add Python26 specific libraries
        elif sys.version_info[:2] == (2, 6):
            path = 'code/python/lib_python26'
            if is_64bits:
                path = 'code/python/lib_python26_64'
            env.registerPath(env.relativePath(path))
        # Add Python27 specific libraries
        elif sys.version_info[:2] == (2, 7):
            path = 'code/python/lib_python27'
            if is_64bits:
                path = 'code/python/lib_python27_64'
            env.registerPath(env.relativePath(path))

    def recordSettings(self):
        """
        Subclasses can reimplement this to add data before it is saved
        """
        pref = self.recordCoreSettings()
        pref.save()

    def recordCoreSettings(self):
        pref = blurdev.prefs.find('blurdev/core', coreName=self.objectName())

        # record the tools environment
        envName = (
            blurdev.tools.toolsenvironment.ToolsEnvironment.activeEnvironment().objectName()
        )
        if envName != os.environ.get('BDEV_TOOL_ENVIRONMENT'):
            pref.recordProperty('environment', envName)

        # record the debug
        pref.recordProperty('debugLevel', blurdev.debug.debugLevel())

        # record the tools style
        pref.recordProperty('style', self._stylesheet)

        return pref

    def recordToolbars(self):
        if self.headless:
            # If running headless, the toolbars were not created, and prefs don't need to be saved
            return
        pref = blurdev.prefs.find('blurdev/toolbar', coreName=self.objectName())

        # record the toolbar
        child = pref.root().findChild('toolbardialog')

        # remove the old instance
        if child:
            child.remove()

        self.recordToolbarXML(pref)
        from blurdev.tools.toolslovebar import ToolsLoveBarDialog

        if ToolsLoveBarDialog._instance:
            ToolsLoveBarDialog._instance.recordSettings()

        pref.save()

    def recordToolbarXML(self, pref):
        from blurdev.tools.toolstoolbar import ToolsToolBarDialog

        if ToolsToolBarDialog._instance:
            ToolsToolBarDialog._instance.toXml(pref.root())

    def refreshStyleSheet(self):
        """ Reload the current stylesheet to force a update of the display of widgets. """
        app = QApplication.instance()
        if app and isinstance(
            app, QApplication
        ):  # Don't set stylesheet if QCoreApplication
            app.setStyleSheet(app.styleSheet())

    def createEnvironmentOverride(self, env=None, timestamp=None):
        from blurdev.XML import XMLDocument

        if env is None:
            env = (
                blurdev.tools.toolsenvironment.ToolsEnvironment.defaultEnvironment().objectName()
            )
        if timestamp is None:
            timestamp = QDateTime.currentDateTime()

        fp = self.environment_override_filepath
        if not fp:
            return

        doc = XMLDocument()
        root = doc.addNode('environment_overrides')
        root.setAttribute('version', 1.0)
        el = root.addNode('environment_override')
        el.setAttribute('environment', unicode(env))
        el.setAttribute('timestamp', unicode(timestamp.toString('yyyy-MM-dd hh:mm:ss')))
        try:
            doc.save(fp)
        except Exception:
            pass

    def getEnvironmentOverride(self):
        from blurdev.XML import XMLDocument

        doc = XMLDocument()
        self.environment_override_filepath = os.environ.get(
            'BDEV_ENVIRONMENT_OVERRIDE_FILEPATH', ''
        )
        try:
            if not self.environment_override_filepath:
                return None
            if not os.path.exists(self.environment_override_filepath):
                return None
            if not doc.load(self.environment_override_filepath):
                return None

            root = doc.root()
            if not root:
                return None

            element = root.findChild('environment_override')
            if not element:
                return None

            attrs = element.attributeDict()
            if not attrs:
                return None

            if not attrs.get('environment'):
                return None

            try:
                timestamp = attrs.get('timestamp')
                if not timestamp:
                    return None
                attrs['timestamp'] = QDateTime.fromString(
                    timestamp, 'yyyy-MM-dd hh:mm:ss'
                )
            except Exception:
                return None

            return attrs

        except Exception:
            return None

    def restoreSettings(self):
        self.blockSignals(True)
        TEMPORARY_TOOLS_ENV = blurdev.tools.TEMPORARY_TOOLS_ENV
        ToolsEnvironment = blurdev.tools.toolsenvironment.ToolsEnvironment

        pref = blurdev.prefs.find('blurdev/core', coreName=self.objectName())

        env = ToolsEnvironment.findEnvironment(os.environ.get('BDEV_TOOL_ENVIRONMENT'))
        if not env.isEmpty():
            env.setActive()
        else:
            # If the environment variable BLURDEV_PATH is defined create a custom environment instead of using the loaded environment
            environPath = os.environ.get('BLURDEV_PATH')
            if environPath:
                env = ToolsEnvironment.findEnvironment(
                    TEMPORARY_TOOLS_ENV, path=environPath
                )
                if env.isEmpty():
                    devel = (
                        os.environ.get('BDEV_ENVIRONMENT_DEVEL', 'False').lower()
                        == 'true'
                    )
                    offline = (
                        os.environ.get('BDEV_ENVIRONMENT_OFFLINE', 'False').lower()
                        == 'true'
                    )
                    environFile = os.environ.get('BDEV_ENVIRONMENT_ENVIRON_FILE', '')
                    env = ToolsEnvironment.createNewEnvironment(
                        TEMPORARY_TOOLS_ENV,
                        environPath,
                        development=devel,
                        offline=offline,
                        environmentFile=environFile,
                    )
                    env.setEmailOnError([os.environ.get('BLURDEV_ERROR_EMAIL')])
                    env.setTemporary(True)
                env.setActive()
            else:
                # restore the active environment
                env = pref.restoreProperty('environment')
                if env:
                    ToolsEnvironment.findEnvironment(env).setActive()

        # restore the active debug level
        level = pref.restoreProperty('debugLevel')
        if level is not None:
            blurdev.debug.setDebugLevel(level)

        # restore the active style
        self.setStyleSheet(
            os.environ.get('BDEV_STYLESHEET') or pref.restoreProperty('style'),
            recordPrefs=False,
        )

        self.blockSignals(False)

        self.applyEnvironmentTimeouts()
        self.applyStudioOverrides()
        # Ensure the core has its paths registered
        self.registerPaths()

        return pref

    def restoreToolbars(self):
        if self.headless:
            # If running headless, do not try to create gui elements
            return
        pref = blurdev.prefs.find('blurdev/toolbar', coreName=self.objectName())
        # restore the toolbar
        child = pref.root().findChild('toolbardialog')
        if child:
            self.toolbar().fromXml(pref.root())
        pref = blurdev.prefs.find('tools/Lovebar', coreName=self.objectName())
        if pref.restoreProperty('isVisible'):
            self.showLovebar(parent=self.rootWindow())

    def rootWindow(self):
        """
        Returns the currently active window
        """
        # for MFC apps there should be no root window
        if self.isMfcApp():
            from blurdev.gui.winwidget import WinWidget

            return WinWidget.newInstance(self.hwnd())

        window = None
        if QApplication.instance():
            window = QApplication.instance().activeWindow()
            # Ignore QSplashScreen's, they should never be considered the root window.
            if isinstance(window, QSplashScreen):
                return None
            # If the application does not have focus try to find A top level widget
            # that doesn't have a parent and is a QMainWindow or QDialog
            if window == None:
                windows = []
                dialogs = []
                for w in QApplication.instance().topLevelWidgets():
                    if w.parent() == None:
                        if isinstance(w, QMainWindow):
                            windows.append(w)
                        elif isinstance(w, QDialog):
                            dialogs.append(w)
                if windows:
                    window = windows[0]
                elif dialogs:
                    window = dialogs[0]

            # grab the root window
            if window:
                while window.parent():
                    parent = window.parent()
                    if isinstance(parent, QSplashScreen):
                        return window
                    else:
                        window = parent
        return window

    def runDelayed(self, function, *args, **kargs):
        """
        Alternative to a for loop that will not block the ui. Each item added
        with this method will be processed during a single application event
        loop. If you add 5 items with runDelayed it will process the first item,
        update the ui, process the second item, update the ui, etc. This is
        usefull if you have a large amount of items to process, but processing
        of a individual item does not take a long time. Also it does not need
        to happen immediately.

        :param function: The function to call when ready to process.

        Any additional arguments or keyword arguments passed to this function
        will be passed along to the provided function

        | #A simplified code example of what is happening.
        | queue = []
        | for i in range(100): queue.append(myFunction)
        | while True:	# program event loop
        | 	updateUI()	# update the programs ui
        |	if queue:
        |		item = queue.pop(0)	# remove the first item in the list
        |		item()	# call the stored function

        """
        self._runDelayed(function, False, *args, **kargs)

    def runDelayedReplace(self, function, *args, **kargs):
        """
        Same as the runDelayed, but will check if the queue contains a matching function, *args, and **kargs. If found it will remove it and append it at the end of the queue.
        """
        self._runDelayed(function, True, *args, **kargs)

    def isDelayed(self, function, *args, **kwargs):
        """
        Is the supplied function and arguments are in the runDelayed queue
        """
        if (function, args, kargs) in self._itemQueue:
            return True
        return False

    def _runDelayed(self, function, replace, *args, **kargs):
        """
        Alternative to a for loop that will not block the ui. Each item added
        with this method will be processed during a single application event loop.
        If you add 5 items with runDelayed it will process the first item, update
        the ui, process the second item, update the ui, etc. This is usefull if
        you have a large amount of items to process, but processing of a
        individual item does not take a long time. Also it does not need to
        happen immediately.

        :param function: The function to call when ready to process.
        :param bool replace: If true, it will attempt to remove the first item in the queue with matching function, *args, **kargs

        Any additional arguments or keyword arguments passed to this function
        will be passed along to the provided function


        | #A simplified code example of what is happening.
        | queue = []
        | for i in range(100): queue.append(myFunction)
        | while True:	# program event loop
        | 	updateUI()	# update the programs ui
        |	if queue:
        |		item = queue.pop(0)	# remove the first item in the list
        |		item()	# call the stored function

        """
        isProcessing = bool(self._itemQueue)
        queueItem = (function, args, kargs)
        if replace:
            if queueItem in self._itemQueue:
                self._itemQueue.remove(queueItem)
        self._itemQueue.append((function, args, kargs))
        if not isProcessing:
            # start the queue processing if it was empty
            self.postQueueEvent()

    def runMacro(self, command):
        """
        Runs a macro command
        """
        print '[blurdev.cores.core.Core.runMacro] virtual method not defined'
        return False

    def runStandalone(
        self,
        filename,
        debugLevel=None,
        basePath='',
        environ=None,
        paths=None,
        architecture=None,
    ):
        blurdev.osystem.startfile(
            filename, debugLevel, basePath, architecture=architecture
        )

    def runScript(
        self,
        filename='',
        scope=None,
        argv=None,
        toolType=None,
        toolName=None,
        architecture=None,
    ):
        """
        Runs an inputed file in the best way this core knows how

        :param str filename:
        :param dict scope: The scope to run the script in (ie. locals(), globals())
        :param list argv: Commands to pass to the script at run time
        :param toolType: determines the tool type for this tool

        """
        if not filename:
            # make sure there is a QApplication running
            if QApplication.instance():
                filename = str(
                    QFileDialog.getOpenFileName(
                        None,
                        'Select Script File',
                        self._lastFileName,
                        'Python Files (*.py);;Maxscript Files (*.ms);;All Files (*.*)',
                    )
                )
                if not filename:
                    return

        if not argv:
            argv = []

        if not filename:
            return False

        # build the scope
        if scope is None:
            scope = {}

        filename = str(filename)

        # run the script
        if filename and os.path.exists(filename):
            self._lastFileName = filename

            ext = os.path.splitext(filename)[1]

            # always run legacy external tools as standalone - they can cause QApplication conflicts
            if toolType == blurdev.tools.tool.ToolType.LegacyExternal:
                os.startfile(filename)

            # run a python file
            elif ext.startswith('.py'):
                # if running in external mode, run a standalone version for python files - this way they won't try to parent to the treegrunt
                if self.objectName() in ('external', 'treegrunt'):
                    self.runStandalone(filename, architecture=architecture)
                else:
                    # create a local copy of the sys variables as they stand right now
                    path_bak = list(sys.path)
                    try:
                        argv_bak = sys.argv
                    except AttributeError:
                        argv_bak = None

                    # if the path does not exist, then register it
                    blurdev.tools.toolsenvironment.ToolsEnvironment.registerScriptPath(
                        filename
                    )

                    scope['__name__'] = '__main__'
                    scope['__file__'] = filename
                    sys.argv = [filename] + argv
                    scope['sys'] = sys

                    # create a tool stopwatch used to debug
                    env = blurdev.activeEnvironment()
                    if env.stopwatchEnabled:
                        if toolName == None:
                            toolName = filename
                        env.stopwatch = blurdev.debug.Stopwatch(toolName)
                    execfile(filename, scope)
                    if env.stopwatchEnabled:
                        env.stopwatch.stop()

                    # restore the system information
                    sys.path = path_bak
                    if argv_bak:
                        sys.argv = argv_bak

                return True

            # run a fusion script
            elif ext.startswith('.eyeonscript'):

                # Moved import here because even attempting this import causes
                # win32 errors in Motionbuilder.
                try:
                    import PeyeonScript as eyeon
                except ImportError:
                    eyeon = None

                if eyeon:
                    fusion = eyeon.scriptapp('Fusion')
                    if fusion:
                        comp = fusion.GetCurrentComp()
                        if comp:
                            comp.RunScript(str(filename))
                        else:
                            QMessageBox.critical(
                                None,
                                'No Fusion Comp',
                                'There is no comp running in your Fusion.',
                            )
                    else:
                        QMessageBox.critical(
                            None,
                            'Fusion Not Found',
                            'You need to have Fusion running to run this file.',
                        )
                else:
                    QMessageBox.critical(
                        None,
                        'PeyonScript Missing',
                        'Could not import Fusion Python Libraries.',
                    )
                return True

            # run an external link
            elif ext.startswith('.lnk'):
                os.startfile(filename)
                return True

            # report an unknown format
            else:
                print '[blurdev.cores.core.Core.runScript] Cannot run scripts of type (*%s)' % ext

        return False

    def sdkBrowser(self, parent=None):
        from blurdev.gui.windows.sdkwindow import SdkWindow

        return SdkWindow.instance(parent)

    def setLastFileName(self, filename):
        return self._lastFileName

    def setHwnd(self, hwnd):
        self._hwnd = hwnd

    def setMaxDelayPerCycle(self, seconds):
        """
        Run delayed will process as many items as it can within this time
        frame every event loop.  Seconds is a float value for seconds. If
        seconds is -1 it will only process 1 item per event loop. This value
        does not limit the cycle, it just prevents a new queue item from being
        called if the total time exceeds this value. If your queue items will
        take almost the full time, you may want to set this value to -1.

        """
        self._maxDelayPerCycle = seconds

    def emailAddressMd5Hash(self, text, address=None):
        """ Turns the text into a md5 string and inserts it in the address.
        
        This is useful for controlling how messages are threaded into conversations on gmail.
        
        Args:
            text (str): This text will be converted into a md5 hash.
            address (str or None): The md5 hash will be inserted using str.format on the "hash" key.
                If None, it will use the value stored in the BDEV_ERROR_EMAIL environment variable.
        
        Returns:
            str: The formatted address.
        """
        import hashlib

        m = hashlib.md5()
        m.update(text)
        if address is None:
            address = os.environ.get('BDEV_ERROR_EMAIL')
        return address.format(hash=m.hexdigest())

    def sendEmail(
        self, sender, targets, subject, message, attachments=None, refId=None
    ):
        """ Sends an email.

        Args:
            sender (str): The source email address.
            targets (str or list): A single email string, or a list of email address(s) to send 
                the email to.
            subject (str): The subject of the email.
            message (str): The body of the message. Treated as html
            attachments (list or None): File paths for files to be attached.
            refId (str or None): If not None "X-Entity-Ref-ID" is added to the header with this
                value. For gmail passing a empty string appears to be the same as passing real data.
        """
        from email import Encoders
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase

        output = MIMEMultipart()
        output['Subject'] = str(subject)
        output['From'] = str(sender)
        if refId is not None:
            output['X-Entity-Ref-ID'] = refId

        # convert to string
        if isinstance(targets, (tuple, list)):
            output['To'] = ', '.join(targets)
        else:
            output['To'] = str(targets)

        output['Date'] = str(
            QDateTime.currentDateTime().toString('ddd, d MMM yyyy hh:mm:ss')
        )
        output['Content-type'] = 'Multipart/mixed'
        output.preamble = 'This is a multi-part message in MIME format.'
        output.epilogue = ''

        # Build Body
        msgText = MIMEText(str(message), 'html')
        msgText['Content-type'] = 'text/html'

        output.attach(msgText)

        # Include Attachments
        if attachments:
            for a in attachments:
                fp = open(str(a), 'rb')
                txt = MIMEBase('application', 'octet-stream')
                txt.set_payload(fp.read())
                fp.close()

                Encoders.encode_base64(txt)
                txt.add_header(
                    'Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(a),
                )
                output.attach(txt)

        try:
            # TODO: Environment compatibility
            smtp = smtplib.SMTP('mail.blur.com', timeout=1)
            # smtp.starttls()
            # smtp.connect(os.environ.get('BDEV_SEND_EMAIL_SERVER', 'mail.blur.com'))
            smtp.sendmail(str(sender), output['To'].split(','), str(output.as_string()))
            smtp.close()

        except:
            # TODO: Proper logging

            import inspect

            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])

            import traceback

            traceback.print_exc()

            print 'Module {0} @ {1} failed to send email\n{2}\n{3}\n{4}\n{5}'.format(
                module.__name__, module.__file__, sender, targets, subject, message
            )

            raise

    def setObjectName(self, objectName):
        if objectName != self.objectName():
            QObject.setObjectName(self, objectName)
            blurdev.prefs.clearCache()
            # make sure we have the proper settings restored based on the new application
            self.restoreSettings()

    def readStyleSheet(self, stylesheet='', path=None):
        """ Returns the contents of the requested stylesheet.

        Args:
            stylesheet (str): the name of the stylesheet. Attempt to load stylesheet.css shipped
                with blurdev. Ignored if path is provided.
            path (str): Return the contents of this file path.

        Returns:
            str: The contents of stylesheet or blank if stylesheet was not found.
            valid: A stylesheet was found and loaded.
        """
        if path == None:
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'resource',
                'stylesheet',
                '{}.css'.format(stylesheet),
            )
        if os.path.isfile(path):
            with open(path) as f:
                return f.read(), True
        return '', False

    def reloadStyleSheet(self):
        self.setStyleSheet(self.styleSheet())

    def setStyleSheet(self, stylesheet, recordPrefs=True):
        """ Accepts the name of a stylesheet included with blurdev, or a full
            path to any stylesheet.  If given None, it will remove the
            stylesheet.
        """
        app = QApplication.instance()
        if app and isinstance(
            app, QApplication
        ):  # Don't set stylesheet if QCoreApplication
            if stylesheet is None or stylesheet == 'None':
                app.setStyleSheet('')
                self._stylesheet = None
            elif os.path.isfile(stylesheet):
                with open(stylesheet) as f:
                    app.setStyleSheet(f.read())
                self._stylesheet = stylesheet
            else:
                # Try to find an installed stylesheet with the given name
                sheet, valid = self.readStyleSheet(stylesheet)
                if valid:
                    self._stylesheet = stylesheet
                app.setStyleSheet(sheet)
                path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'resource',
                    'stylesheet',
                    '{}.css'.format(stylesheet),
                )
                if os.path.isfile(path):
                    with open(path) as f:
                        app.setStyleSheet(f.read())
                    self._stylesheet = stylesheet

        if self.objectName() != 'blurdev':
            # Storing the stylesheet as an environment variable for other external tools.
            os.environ['BDEV_STYLESHEET'] = str(stylesheet)

            if recordPrefs:
                # Recording preferences.
                self.recordSettings()
        # Notify widgets of the stylesheet change
        self.styleSheetChanged.emit(str(stylesheet))

    def styleSheet(self):
        """ Returns the name of the current stylesheet.
        """
        return self._stylesheet

    def styleSheets(self):
        """ Returns a list of installed stylesheet names.
        """
        import glob

        cssdir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'resource',
            'stylesheet',
        )
        cssfiles = glob.glob(os.path.join(cssdir, '*.css'))
        # Only return the filename without the .css extension
        return [os.path.splitext(os.path.basename(fp))[0] for fp in cssfiles]

    def quitQtOnShutdown(self):
        """ If true is returned, all windows will be closed and QApplication.instance().quit() will be
        called. This can be overridden in cores to prevent shutdown.
        """
        return True

    def shutdown(self):
        # record the settings
        self.recordToolbars()
        self.recordSettings()

        if self.quitQtOnShutdown():
            if QApplication.instance():
                QApplication.instance().closeAllWindows()
                QApplication.instance().quit()
        else:
            # The app is probably nuke, maya or Motionbuilder, so closing all windows, and killing
            # the app is not what we want to do. This saves prefs and closes any of the instance
            # windows if they are active

            # Make sure to close the Toolbar and Lovebar
            self.shutdownToolbars()
            # Make sure to close Treegrunt
            from blurdev.gui.dialogs.treegruntdialog import TreegruntDialog

            TreegruntDialog.instanceShutdown()
            # Make sure to close the Logger window
            from blurdev.gui.windows.loggerwindow import LoggerWindow

            LoggerWindow.instanceShutdown()

    def shutdownToolbars(self):
        """ Closes the toolbars and save their prefs if they are used

        This is abstracted from shutdown, so specific cores can control how they shutdown
        """
        from blurdev.tools.toolstoolbar import ToolsToolBarDialog
        from blurdev.tools.toolslovebar import ToolsLoveBarDialog

        ToolsToolBarDialog.instanceShutdown()
        ToolsLoveBarDialog.instanceShutdown()

    def showIdeEditor(self):
        from blurdev.ide.ideeditor import IdeEditor

        IdeEditor.instance().edit()

    def showToolbar(self, parent=None):
        from blurdev.tools.toolstoolbar import ToolsToolBarDialog

        ToolsToolBarDialog.instance(parent).show()

    def showLovebar(self, parent=None):
        from blurdev.tools.toolslovebar import ToolsLoveBarDialog

        ToolsLoveBarDialog.instance(parent).show()

    def showPyular(self, parent=None):
        self.pyular(parent).show()

    def showTreegrunt(self):
        treegrunt = self.treegrunt()
        treegrunt.show()
        treegrunt.raise_()
        treegrunt.setWindowState(
            treegrunt.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
        )

    def showLogger(self):
        """
        Creates the python logger and displays it
        """
        logger = self.logger()
        logger.show()
        logger.activateWindow()
        logger.raise_()
        logger.console().setFocus()

    def supportsDocking(self):
        return self._supportsDocking

    def unprotectModule(self, moduleName):
        """
        Removes the inputed module name from protection from tools environment switching
        """
        key = str(moduleName)
        while key in self._protectedModules:
            self._protectedModules.remove(key)

    def uuid(self):
        """ Application specific unique identifier

        Returns:
            None:
        """
        return None

    def toolbar(self, parent=None):
        from blurdev.tools.toolstoolbar import ToolsToolBarDialog

        return ToolsToolBarDialog.instance(parent)

    def toolTypes(self):
        """
        Determines what types of tools that the treegrunt system should be looking at
        """
        ToolType = blurdev.tools.tool.ToolType
        if self.objectName() == 'multiprocessing':
            import blurdev.external as external

            if external.External().parentCore == 'fusion':
                return ToolType.Fusion
        return ToolType.External | ToolType.Fusion | ToolType.LegacyExternal

    def treegrunt(self, parent=None):
        """ Creates and returns the logger instance
        """
        from blurdev.gui.dialogs.treegruntdialog import TreegruntDialog

        return TreegruntDialog.instance(parent)

    def useAppUserModelID(self):
        """ Returns a boolean value controlling if calling blurdev.setAppUserModelID will do anyting. """
        # Core subclasses Can simply set _useAppUserModelID to True or False if they want to blanket
        # enable or disable setAppUserModelID.
        if self._useAppUserModelID == None:
            # By default allow all core names. If a specific core name needs to be excluded, it
            # should be added to this list.
            return self.objectName() not in ('assfreezer', 'designer')
        return self._useAppUserModelID

    def setUseAppUserModelID(self, value):
        self._useAppUserModelID = value
