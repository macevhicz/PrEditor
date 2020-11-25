import os
import blurdev as _blurdev
import distutils.spawn

__all__ = [
    'createShortcutBlurIDE',
    'createShortcutPythonLogger',
    'createShortcutTreegrunt',
    'createShortcutTool',
]


def _blurdev_exe(pyw=True):
    """ Gets the path to blurdevw or blurdev executable.

    Uses ``distutils.spawn.find_executable`` so the path is consistent with the system.
    If blurdevw is not found with this, ``_scrips_path`` is used for the base path and
    the .exe file extension is added if running on windows.

    Args:
        pyw (bool, optional): If True then blurdevw is returned, if false blurdev is
            returned. On windows blurdevw.exe is used to run python without showing a
            command prompt window like blurdev would, the same way that pythonw.exe
            works. On linux both work the same way.
    """
    exe_base = 'blurdevw' if pyw else 'blurdev'
    # Check if we can just call blurdevw directly because it is in the PATH env var.
    exe = distutils.spawn.find_executable(exe_base)
    if exe:
        # blurdevw is in PATH, so strip off the directory path, preserving any extension
        return exe
    if _blurdev.settings.OS_TYPE == 'Windows':
        exe_base += '.exe'
    return _scrips_path(exe_base)


def _scrips_path(*relative):
    """ Build the full path to the scripts folder of python.
    Uses blurdev.osystem.pythonPath so this points to the python directory defined in
    the registry, not a virtualenv path (at least on windows).

    Args: *relative: Passed as additional arguments to os.path.join to build the final
        path.

    Returns: path (str): The complete path to the scripts or bin folder with any
        relative paths.
    """
    python_exe = _blurdev.osystem.pythonPath(pyw=True, architecture=64)
    if _blurdev.settings.OS_TYPE == 'Windows':
        relative = ['Scripts'] + list(relative)
    else:
        relative = ['bin'] + list(relative)
    return os.path.join(os.path.dirname(python_exe), *relative)


def createShortcutPythonLogger(
    path=None,
    name='Python Logger',
    target=None,
    description='Opens the Python Logger.',
    common=0,
):
    """ Creates a shortcut that launches the Python Logger as a standalone application.

    Args:
        path (str or None, optional): Where to create the shortcut. If None(default) it
            will create the shortcut on the users Desktop.
        name (str, optional): The name of the shortcut. Defaults to 'Python Logger'
        target (str or None, optional): the target for the shortcut. If None(default)
            this will default the blurdev-logger executable.
        description (str, optional): This text is shown as the comment for the shortcut.
        common (int): If auto generating the path, this controls which desktop the path
            is generated for. 1 is the public shared desktop, while 0(default) is the
            users desktop.
    """
    _blurdev.osystem.createShortcut(
        name,
        '',
        target=_scrips_path('blurdev-logger.exe') if target is None else target,
        path=path,
        icon=_blurdev.resourcePath(r'img\PythonLogger.ico'),
        description=description,
        common=common,
    )


def createShortcutBlurIDE(
    path=None, name='Blur IDE', target=None, description='Opens Blur IDE.', common=0
):
    """ Creates a shortcut that launches the Blur IDE as a standalone application.

    Args:
        path (str or None, optional): Where to create the shortcut. If None(default) it
            will create the shortcut on the users Desktop.
        name (str, optional): The name of the shortcut. Defaults to 'Blur IDE'
        target (str or None, optional): the target for the shortcut. If None(default)
            this will default the blurIDE executable. description (str, optional): This
            text is shown as the comment for the shortcut.
        common (int): If auto generating the path, this controls which desktop the path
            is generated for. 1 is the public shared desktop, while 0(default) is the
            users desktop.
    """
    _blurdev.osystem.createShortcut(
        name,
        '',
        target=_scrips_path('blurIDE.exe') if target is None else target,
        path=path,
        icon=_blurdev.resourcePath(r'img\ide.ico'),
        description=description,
        common=common,
    )


def createShortcutTreegrunt(
    path=None,
    name='Treegrunt',
    target=None,
    description='Opens Treegrunt tool launcher.',
    common=0,
):
    """ Creates a shortcut that launches Treegrunt as a standalone application.

    Args:
        path (str or None, optional): Where to create the shortcut. If None(default) it
            will create the shortcut on the users Desktop.
        name (str, optional): The name of the shortcut. Defaults to 'Treegrunt'
        target (str or None, optional): the target for the shortcut. If None(default)
            this will default the treegrunt executable.
        description (str, optional): This text is shown as the comment for the shortcut.
        common (int): If auto generating the path, this controls which desktop the path
            is generated for. 1 is the public shared desktop, while 0(default) is the
            users desktop.
    """
    _blurdev.osystem.createShortcut(
        name,
        '',
        target=_scrips_path('treegrunt.exe') if target is None else target,
        path=path,
        icon=_blurdev.resourcePath(r'img\treegrunt.ico'),
        description=description,
        common=common,
    )


def createShortcutTool(
    tool, path=None, target=None, common=0,
):
    """ Creates a shortcut that launches a treegrunt tool as a standalone application.

    Args:
        tool (blurdev.tools.tool.Tool): The tool this shortcut will launch.
        path (str or None, optional): Where to create the shortcut. If None(default) it
            will create the shortcut on the users Desktop.
        target (str or None, optional): the target for the shortcut. If None(default)
            this will default the treegrunt-tool executable.
        common (int): If auto generating the path, this controls which desktop the path
            is generated for. 1 is the public shared desktop, while 0(default) is the
            users desktop.
    """
    target = _blurdev_exe() if target is None else target
    _blurdev.osystem.createShortcut(
        tool.displayName(),
        ['launch', tool.objectName()],
        target=target,
        startin=os.path.dirname(target),
        path=path,
        icon=tool.icon(),
        description=tool.toolTip(),
        common=common,
        # Tool name could be "LegacyStudioMax::MegaMerge".
        iconFilename=tool.objectName().split(':')[-1],
    )
