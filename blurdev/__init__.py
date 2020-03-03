""" The blurdev package is the core library methods for tools development at Blur Studio

    The blurdev package is also the primary environment manager for blur tools.
    It contains useful sub-packages for various tasks, such as media encoding,
    and includes a Qt gui library.

"""

from __future__ import absolute_import

__DOCMODE__ = False  # this variable will be set when loading information for documentation purposes

# track the install path
import os
import sys
import copy
import types
import re
import weakref

from deprecated import deprecated

from Qt.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
)
from Qt.QtCore import Qt, QDateTime

# TODO: It is probably unnecessary to import most of these subpackages in the root package.
import blurdev.version

__version__ = blurdev.version.to_string(prepend_v=False)
import blurdev.settings
import blurdev.enum
import blurdev.debug
import blurdev.osystem
import blurdev.media
import blurdev.XML
import blurdev.prefs
import blurdev.tools
import blurdev.ini
from blurdev.resource_finder import ResourceFinder as Resources


installPath = os.path.dirname(__file__)
"""Stores the full filepath of the blurdev installation directory."""

application = None  # create a managed QApplication
_appHasExec = False
"""
The blurdev managed QApplication returned from :meth:`Core.init` as part
of the :mod:`blurdev.cores` system.
"""

core = None  # create a managed Core instance
"""
The blurdev managed :class:`Core` object from the :mod:`blurdev.cores` module.
"""
# Weakref.ref does not accept None, and None is not callable. Passing the lambda
# ensures the same functionality even if no tool has been launched yet.
lastLaunched = weakref.ref(lambda: None)
"""
This is set any time blurdev.launch is called. It contains the Dialog or Window
object. This is for debugging, and there is no guarantee that the object has not
been deleted.
"""

# To show a splashscreen as soon as possible, the blurdev.protocols system
# may store a splashscreen here. This will be None unless the protocol
# system sets it, and it will be cleared the first time blurdev.launch
# is called. blurdev.gui.splashscreen.randomSplashScreen checks this value
protocolSplash = None


def activeEnvironment(coreName=None):
    """ Returns the current active Tools Environment as part of the blurdev.tools system.

    Args:
        coreName (str or None, optional): If None(default) it will return the currently
            active treegrunt environment for this instance of python. Otherwise it will
            return the treegrunt environment stored in prefs for coreName.
    """
    if coreName is not None:
        # Update the saved preference so the next time the core is loaded it will
        # use the requested environment if the environment is valid.
        pref = blurdev.prefs.find('blurdev/core', reload=True, coreName=coreName)
        envName = pref.restoreProperty('environment')
        return blurdev.tools.ToolsEnvironment.findEnvironment(envName)
    return blurdev.tools.ToolsEnvironment.activeEnvironment()


def bindMethod(object, name, method):
    """
    Properly binds a new python method to an existing C++ object as a 
    dirty alternative to sub-classing when not possible. Object must
    be a instance, not a class.
    """
    # Passing (method.__func__, object) should work in python 2 and 3.
    object.__dict__[name] = types.MethodType(method.__func__, object)


@deprecated(
    version='2.28.0', reason='Use cute.functions.ensureWindowIsVisible instead.'
)
def ensureWindowIsVisible(widget):
    import cute

    return cute.functions.ensureWindowIsVisible(widget)


def findDevelopmentEnvironment():
    return blurdev.tools.ToolsEnvironment.findDevelopmentEnvironment()


def findTool(name, environment=''):
    if not environment:
        env = blurdev.tools.ToolsEnvironment.activeEnvironment()
    else:
        env = blurdev.tools.ToolsEnvironment.findEnvironment(environment)
    if env:
        return env.index().findTool(name)
    return blurdev.tools.Tool()


def runtime(*args):
    """ Return the full path to this file in blurdev's runtime folder.

    Returns:
        The os.path.join of all the blurdev runtimes folder and any passed in args.
    """
    return os.path.join(installPath, 'runtimes', *args)


def init():
    os.environ['BDEV_EMAILINFO_BLURDEV_VERSION'] = blurdev.version.to_string()
    pythonw_print_bugfix()
    blurdev.settings.init()
    blurdev.ini.LoadConfigData()
    global core, application
    # create the core and application
    if not core:
        from blurdev.cores import Core

        objectName = None
        _exe = os.path.basename(sys.executable).lower()
        # Treat designer as a seperate core so it gets its own prefrences.
        if 'designer' in _exe:
            objectName = 'designer'
        elif 'assfreezer' in _exe:
            objectName = 'assfreezer'
        core = Core(objectName=objectName)
        application = core.init()


def launch(
    ctor,
    modal=False,
    coreName='external',
    instance=False,
    args=None,
    kwargs=None,
    splash=None,
    wrapClass=None,
    dockWidgetArea=Qt.RightDockWidgetArea,
):
    """
    This method is used to create an instance of a widget (dialog/window) to 
    be run inside the blurdev system.  Using this function call, blurdev will 
    determine what the application is and how the window should be 
    instantiated, this way if a tool is run as a standalone, a new 
    application instance will be created, otherwise it will run on top 
    of a currently running application.
    
    :param ctor: callable object that will return a widget instance, usually
                 a :class:`QWidget` or :class:`QDialog` or a function that
                 returns an instance of one.
    :param modal: If True, widget will be created as a modal widget (ie. blocks
                  access to calling gui elements).
    :param coreName: string to give to the core if the application is 
                     going to be rooted under this widget
    :param instance: If subclassed from blurdev.gui.Window or Dialog
                     it will show the existing instance instead of
                     creating a new instance. Ignored if modal == True.
    :param kwargs: A dict of keyword arguments to pass to the widget initialization
    :param wrapClass: launch() requires a subclass of QDialog, QMainWindow or DockWidget to work 
        correctly. If you pass in a widget, it will automatically get wrapped in a Dialog, unless
        you specify a class using this argument, in which case it will be wrapped by that.
    :param dockWidgetArea: If ctor is a QDockWidget
    """
    global lastLaunched
    global protocolSplash
    # create the app if necessary
    app = None
    from blurdev.cores.core import Core

    if application:
        application.setStyle(core.defaultStyle())

        # See ToolsEnvironment._resetIfSamePath for more info on why this is being set.
        current = blurdev.tools.ToolsEnvironment._resetIfSamePath
        try:
            blurdev.tools.ToolsEnvironment._resetIfSamePath = False
            core.setObjectName(coreName)
        finally:
            blurdev.tools.ToolsEnvironment._resetIfSamePath = current

    if instance and hasattr(ctor, 'instance') and not modal:
        # use the instance method if requested
        widget = ctor.instance()
    else:
        # Handle any url arguments that were passed in using the environment.
        urlArgs = os.environ.pop('BDEV_URL_ARGS', None)
        oldkwargs = copy.copy(kwargs)
        if urlArgs:
            import cPickle

            urlArgs = cPickle.loads(urlArgs)
            if kwargs is None:
                kwargs = urlArgs
            else:
                kwargs.update(urlArgs)

        def launchWidget(ctor, args, kwargs):
            # create the output instance from the class
            # If args or kwargs are defined, use those.  NOTE that if you pass any
            # args or kwargs, you will also have to supply the parent, which
            # blurdev.launch previously had always set to None.
            if args or kwargs:
                if args is None:
                    args = []
                if kwargs is None:
                    kwargs = {}
                widget = ctor(*args, **kwargs)
            else:
                global core
                widget = ctor(core.rootWindow())
            return widget

        try:
            widget = launchWidget(ctor, args, kwargs)
        except TypeError:
            # If url arguments are passed in that the tool doesn't accept, remove them.
            widget = launchWidget(ctor, args, oldkwargs)

    # Attach the protocolSplash.finish to the widget we are creating and
    # remove the reference so we don't keep using it.
    if protocolSplash is not None:
        protocolSplash.finish(widget)
        protocolSplash = None

    if splash:
        splash.finish(widget)

    # If the passed in ctor is not a QDialog, QMainWindow or QDockWidget, wrap it in a dialog
    # so that it displays correctly. It will get garbage collected and close otherwise
    if not isinstance(widget, (QMainWindow, QDialog, QDockWidget)):
        if wrapClass is not None:
            dlg = wrapClass(None)
        else:
            from blurdev.gui.dialog import Dialog

            dlg = Dialog(None)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        dlg.setLayout(layout)
        layout.addWidget(widget)
        dlg.setWindowTitle(widget.windowTitle())
        dlg.setWindowIcon(widget.windowIcon())
        widget = dlg

    # Store the last launched tool so a developer can easily find it to experiment with.
    lastLaunched = weakref.ref(widget)
    # check to see if the tool is running modally and return the result
    if modal:
        widget.exec_()
    else:
        if isinstance(widget, QDockWidget) and widget.parent() and dockWidgetArea:
            widget.parent().addDockWidget(dockWidgetArea, widget)
        widget.show()
        if instance:
            widget.raise_()
            widget.setWindowState(
                widget.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
            )
        # run the application if this item controls it and it hasnt been run before
        startApplication(widget.windowIcon())
    return widget


def startApplication(windowIcon=None):
    """ Starts blurdev.application if it hasn't already been started. """
    global _appHasExec
    if application and not _appHasExec:
        if windowIcon:
            application.setWindowIcon(windowIcon)
        _appHasExec = True
        application.exec_()


def quickReload(modulename):
    """
    Searches through the loaded sys modules and looks up matching module names 
    based on the imported module.
    
    """
    expr = re.compile(modulename.replace('.', '\.').replace('*', '[A-Za-z0-9_]*'))

    # reload longer chains first
    keys = sys.modules.keys()
    keys.sort()
    keys.reverse()

    for key in keys:
        module = sys.modules[key]
        if expr.match(key) and module != None:
            print('reloading', key)
            reload(module)


def packageForPath(path):
    splt = os.path.normpath(path).split(os.path.sep)
    index = 1

    filename = os.path.join(path, '__init__.py')
    package = []
    while os.path.exists(filename):
        package.append(splt[-index])
        filename = os.path.join(os.path.sep.join(splt[:-index]), '__init__.py')
        index += 1

    package.reverse()
    return '.'.join(package)


def prefPath(relpath, coreName=''):
    # use the core
    if not coreName and core:
        coreName = core.objectName()
    basepath = os.path.join(
        blurdev.osystem.expandvars(os.environ['BDEV_PATH_PREFS']), 'app_%s/' % coreName
    )
    return os.path.normpath(os.path.join(basepath, relpath))


def pythonw_print_bugfix():
    """
    When running pythonw print statements and file handles tend to have problems
    so, if its pythonw and stderr and stdout haven't been redirected, redirect them
    to os.devnull.
    """
    if os.path.basename(sys.executable) == 'pythonw.exe':
        if sys.stdout == sys.__stdout__:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr == sys.__stderr__:
            sys.stderr = open(os.devnull, 'w')


def registerScriptPath(filename):
    blurdev.tools.ToolsEnvironment.registerScriptPath(filename)


def relativePath(path, additional=''):
    """
    Replaces the last element in the path with the passed in additional path.
    :param path: Source path. Generally a file name.
    :param additional: Additional folder/file path appended to the path.
    :return str: The modified path
    """
    return os.path.join(os.path.dirname(path), additional)


def resetWindowPos():
    """
        Reset any top level widgets(windows) to 0,0 use this to find windows that are offscreen.
    """
    for widget in QApplication.instance().topLevelWidgets():
        if widget.isVisible():
            geo = widget.geometry()
            width = geo.width()
            height = geo.height()
            geo.setX(8)
            geo.setY(30)
            geo.setWidth(width)
            geo.setHeight(height)
            widget.setGeometry(geo)


def resourcePath(relpath=''):
    """
    Returns the full path to the file inside the blurdev\resource folder
    :param relpath: The additional path added to the blurdev\resource folder path.
    :return str: The modified path
    """
    return os.path.join(relativePath(__file__), 'resource', relpath)


def runTool(toolId, macro=""):
    """ Runs the tool with the given tool id.
    
    Finds the tool with the given tool id name for the activeEnvironment if it exists.
    You can pass a macro to the tool.exec_ call.
    
    Args:
        toolId(str): The tool Id for the tool. See Tool.objectName()
        macro(str): I have no idea what this is for. Looks like it was from when treegrunt 
                    was moved to blurdev.
    """
    # load the tool
    tool = blurdev.tools.ToolsEnvironment.activeEnvironment().index().findTool(toolId)
    if not tool.isNull():
        tool.exec_(macro)

    # let the user know the tool could not be found
    elif QApplication.instance():
        QMessageBox.critical(
            None,
            'Tool Not Found',
            '%s is not a tool in %s environment.'
            % (toolId, blurdev.tools.ToolsEnvironment.activeEnvironment().objectName()),
        )


def setActiveEnvironment(envName, coreName=None):
    """ Set the active treegrunt environment to this name.

    Args:
        envName (str): The name of a valid treegrunt environment. Case sensitive.
        coreName (str or None, optional): Update the saved environment preference for the
            given coreName. Ignored if coreName matches the current coreName. This change
            will take effect the next time that core is loaded as long as some other
            instance of python doesn't update it after this call.

    Returns:
        bool: The environment was changed successfully. Returns False if the current
            environment is already envName, or if envName is not a valid environment.
    """
    env = blurdev.tools.ToolsEnvironment.findEnvironment(envName)
    if coreName is not None and coreName is not blurdev.core.objectName():
        # There is no need to update the environment this way if its the current environment.
        if not env.isEmpty():
            # Update the saved preference so the next time the core is loaded it will
            # use the requested environment if the environment is valid.
            pref = blurdev.prefs.find('blurdev/core', reload=True, coreName=coreName)
            if pref.restoreProperty('environment') == envName:
                # If the environment is already set to this, do not reset the timestamp
                return False
            pref.recordProperty('environment', envName)
            pref.recordProperty(
                'environment_set_timestamp', QDateTime.currentDateTime()
            )
            pref.save()
            return True
        # not a valid treegrunt environment
        return False
    return env.setActive()


def setAppUserModelID(appId, prefix='Blur'):
    """ Controls the Windows 7 taskbar grouping.
    
    Specifies a Explicit App User Model ID that Windows 7 uses to control grouping of windows on 
    the taskbar.  This must be set before any ui is displayed. The best place to call it is in the 
    first widget to be displayed __init__ method.
    
    Args:
        appId (str): The id of the application. Should use full camel-case.
            `http://msdn.microsoft.com/en-us/library/dd378459%28v=vs.85%29.aspx#how`_
        prefix (str): The prefix attached to the id.  For a blur tool called fooBar, the associated 
            appId should be "Blur.FooBar". Defaults to "Blur".
    """
    # If this function is run inside other applications, it can cause(unparented) new sub windows
    # to parent with this id instead of the parent application in windows.
    # To test: Create a window calling setAppUserModelID before showing it. Use a unique appId. Then
    # create a unparented window and show it. The unparented window will appear in a different
    # taskbar group.
    if not blurdev.core.useAppUserModelID():
        return False
    # Try/except is to prevent the NEED for blur.Stone.
    try:
        # Import blur.Stone here because It is not needed elsewhere
        import blur.Stone
    except ImportError:
        return False
    if hasattr(blur.Stone, 'qSetCurrentProcessExplicitAppUserModelID'):
        blur.Stone.qSetCurrentProcessExplicitAppUserModelID('%s.%s' % (prefix, appId))
        return True
    return False


def signalInspector(item, prefix='----', ignore=[]):
    """
    Connects to all signals of the provided item, and prints the name of 
    each signal.  When that signal is activated it will print the prefix, 
    the name of the signal, and any arguments passed. These connections 
    will persist for the life of the object.
    
    :param item: QObject to inspect signals on.
    :type item: :class:`Qt.QtCore.QObject`
    :param prefix: The prefix to display when a signal is emitted.
    :param ignore: A list of signal names to ignore
    :type ignore: list

    """

    def create(attr):
        def handler(*args, **kwargs):
            print(prefix, 'Signal:', attr, 'ARGS:', args, kwargs)

        return handler

    for attr in dir(item):
        if (
            type(getattr(item, attr)).__name__ == 'pyqtBoundSignal'
            and not attr in ignore
        ):
            print(attr)
            getattr(item, attr).connect(create(attr))


def startProgress(title='Progress', parent=None):
    from blurdev.gui.dialogs.multiprogressdialog import MultiProgressDialog

    return MultiProgressDialog.start(title)


# initialize the core
init()
