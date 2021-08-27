##
# 	\namespace	blurdev.ide.addons.svn.svnops
#
# 	\remarks	shortcut methods to all the actions that use the Qt interface to happen
#
# 	\author		eric@blur.com
# 	\author		Blur Studio
# 	\date		05/17/11
#

from __future__ import absolute_import
import pysvn
import os.path
import blurdev

from blurdev import osystem
from Qt.QtWidgets import QInputDialog, QLineEdit, QMessageBox


def add(filepath):
    """Adds the filepath using the SvnAddDialog gui

    Args:
        filepath (str):
    """
    ide = blurdev.core.rootWindow()

    # promp the user to select non-versioned files
    emptyMessage = (
        'There is nothing to add. '
        'All the files and folders are either under version control\nor have been '
        'ignored using the svn.ignore property\nor the global ignore '
        'configuration setting.'
    )
    from .svnfilesdialog import SvnFilesDialog

    filepaths, accepted = SvnFilesDialog.collect(
        ide, filepath, ['unversioned'], title='Add', emptyMessage=emptyMessage
    )

    # if the user selects the files, then add them
    if accepted and filepaths:
        # create the commit thread
        from .threads.addthread import AddThread

        thread = AddThread()
        thread.setFilepaths(filepaths)

        # run the commit action
        from .svnactiondialog import SvnActionDialog

        SvnActionDialog.start(ide, thread, title='Add')


def branch(filepath):
    url = findUrl(filepath)
    if not url:
        return False

    from .svncopydialog import SvnCopyDialog

    SvnCopyDialog.branch(source=url, target=url)


def browse(filepath='', url=''):
    """Allows the user to browse the repository

    Args:
        url (str) url to start from

    Returns:
        str: will be blank if the user does not complete selection
    """
    if filepath:
        url = findUrl(filepath)

    from .svnrepobrowserdialog import SvnRepoBrowserDialog

    SvnRepoBrowserDialog.browse(url)


def checkout(filepath):
    """Checkout a repository to the inputed filepath directory using the
    SvnCheckoutDialog gui

    Args:
        filepath (str):
    """
    ide = blurdev.core.rootWindow()

    from .svncheckoutdialog import SvnCheckoutDialog

    SvnCheckoutDialog.checkout(ide, filepath)


def cleanup(filepath):
    """Cleans the filepath at the inputed location using the SvnActionDialog
    interface to display feedback

    Args:
        filepath (str):
    """
    ide = blurdev.core.rootWindow()

    # create the cleanup thread
    from .threads.cleanupthread import CleanupThread

    thread = CleanupThread()
    thread.setFilepath(filepath)

    # create the action dialog
    from .svnactiondialog import SvnActionDialog

    SvnActionDialog.start(ide, thread, title='Cleanup')


def createFolder(url, folderName=''):
    """Creates a new folder at the given url with the inputed folder name if a blank
    folder name is supplied, the user will be prompted to enter one

    Args:
        url (str):
        folderName (str):

    Returns:
        bool: success
    """
    if not folderName:
        folderName, accepted = QInputDialog.getText(
            None, 'Create folder...', 'Folder name:'
        )
        folderName = str(folderName)

    if not folderName:
        return False

    client = pysvn.Client()
    urlpath = os.path.join(url, folderName)
    try:
        client.mkdir(urlpath, 'Created %s folder' % folderName, False, None)
        return True
    except Exception:
        return False


def commit(filepath):
    """Commits the filepath using the SvnCommitDialog gui

    Args:
        filepath (str):
    """
    ide = blurdev.core.rootWindow()
    from .svncommitdialog import SvnCommitDialog

    SvnCommitDialog.commit(ide, filepath)


def compare(filepath, old=None, new=None):
    """Prompts the user for changes to compare given the inputed filepath

    Args:
        filepath (str):
        old (int, optional): old revision
        new (int, optional): new revision

    Returns:
        bool: accepted
    """
    if old is None:
        revision = 'HEAD'
    else:
        revision = str(old)

    if new is not None:
        revision += ':%s' % new

    osystem.startfile(
        filepath,
        cmd=osystem.expandvars('$SVN_CMD_COMPARE')
        % {'revision': revision, 'filepath': '%(filepath)s'},
    )


def getMessage():
    from .svnrecentmessagedialog import SvnRecentMessageDialog

    return SvnRecentMessageDialog.getMessage()


def getRevisions(url):
    from .svnlogdialog import SvnLogDialog

    return SvnLogDialog.getRevisions(url)


def getUrl(url=''):
    """Prompts the user to select a url from the svn repository

    Args:
        url (str): url to start from

    Returns:
        str: will be blank if the user does not complete selection
    """
    from .svnrepobrowserdialog import SvnRepoBrowserDialog

    return SvnRepoBrowserDialog.getUrl(url)


def merge(filepath):
    from .svnmergewizard import SvnMergeWizard

    SvnMergeWizard.runWizard(filepath)


def findUrl(filepath):
    """Returns the url for the inputed filepath

    Args:
        filepath: str

    Returns:
        str: url
    """
    client = pysvn.Client()

    # check to see if this is already part of svn
    try:
        entry = client.info(filepath)
    except Exception:
        entry = None

    # create options for SVN filepaths
    if entry:
        return entry.url
    return ''


def rename(basepath):
    """Prompts the user for a new name for the inputed base path

    Args:
        basepath (str):

    Returns:
        str: new path
    """
    ide = blurdev.core.rootWindow()
    basepath = str(basepath)
    # prompt the user for the file rename
    text, accepted = QInputDialog.getText(
        ide,
        'SVN Rename',
        'Enter new name',
        QLineEdit.Normal,
        os.path.normpath(basepath).split(os.path.sep)[-1],
    )
    if accepted:
        splt = os.path.normpath(basepath).split(os.path.sep)
        splt[-1] = str(text)
        newpath = os.path.join(splt)

        # rename the path in svn
        client = pysvn.Client()
        client.move(basepath, newpath)

        return newpath
    return basepath


def remove(filepath):
    """Removes the inptued filepath from svn

    Args:
        filepath:

    Returns:
        bool: success
    """
    if (
        QMessageBox.question(
            None,
            'Removing path',
            'Are you sure you want to remove %s from svn?' % filepath,
            QMessageBox.Yes | QMessageBox.No,
        )
        == QMessageBox.Yes
    ):
        client = pysvn.Client()
        try:
            client.remove(filepath)
            return True
        except Exception:
            return False


def revert(filepath):
    """Prompts the user to revert changes using the SvnRevertDialog interface

    Args:
        filepath (str):
    """
    ide = blurdev.core.rootWindow()
    # promp the user to select non-versioned files
    emptyMessage = (
        'There is nothing to revert. '
        'All the files and folders are up-to-date and unmodified.'
    )
    from .svnfilesdialog import SvnFilesDialog

    filepaths, accepted = SvnFilesDialog.collect(
        ide,
        filepath,
        ['modified', 'added', 'conflicted'],
        title='Revert',
        emptyMessage=emptyMessage,
    )

    # if the user selects the files, then add them
    if accepted and filepaths:
        # create the commit thread
        from .threads.revertthread import RevertThread

        thread = RevertThread()
        thread.setFilepaths(filepaths)

        # run the commit action
        from .svnactiondialog import SvnActionDialog

        SvnActionDialog.start(ide, thread, title='Revert')


def showLog(filepath):
    from .svnlogdialog import SvnLogDialog

    SvnLogDialog.showLog(filepath)


def update(filepath):
    """Updates the filepath at the inputed location using the SvnActionDialog
    interface to display feedback

    Args:
        filepath (str):
    """
    ide = blurdev.core.rootWindow()

    # create the update thread
    from .threads.updatethread import UpdateThread

    thread = UpdateThread()
    thread.setFilepath(filepath)

    # create the action dialog
    from .svnactiondialog import SvnActionDialog

    SvnActionDialog.start(ide, thread, title='Update')
