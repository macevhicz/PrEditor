##
# 	\namespace	blurdev.ide.ideeditor
#
# 	\remarks	This is the main ide window
#
# 	\author		beta@blur.com
# 	\author		Blur Studio
# 	\date		08/19/10
#

from PyQt4.QtCore import pyqtSignal
from blurdev.gui import Window
from blurdev.ide.ideproject import IdeProject
import os


class IdeEditor(Window):
    documentTitleChanged = pyqtSignal()
    currentProjectChanged = pyqtSignal(IdeProject)

    _instance = None

    Registry = {
        '.ui': (
            os.environ['BDEV_QT_DESIGNER'],
            '',
            os.path.dirname(os.environ['BDEV_QT_DESIGNER']),
        ),
        '.schema': (
            os.environ['BDEV_CLASSMAKER'],
            '-s',
            os.path.dirname(os.environ['BDEV_CLASSMAKER']),
        ),
    }

    def __init__(self, parent=None):
        Window.__init__(self, parent)

        # load the ui
        import blurdev
        import blurdev.gui

        blurdev.gui.loadUi(__file__, self)

        # create custom properties
        self._closing = False
        self._searchText = ''
        self._searchFlags = 0
        self._searchDialog = None
        self._searchReplaceDialog = None
        self._searchFileDialog = None
        self._recentFiles = []
        self._recentFileMax = 10
        self._recentFileMenu = None
        self._loaded = False
        self._initfiles = []

        self.setAcceptDrops(True)

        from PyQt4.QtCore import QDir

        QDir.setCurrent(IdeProject.DefaultPath)

        # create the search dialog
        from blurdev.ide.finddialog import FindDialog

        self._searchDialog = FindDialog(self)

        # create a search replace dialog
        from blurdev.ide.findreplacedialog import FindReplaceDialog

        self._searchReplaceDialog = FindReplaceDialog(self)

        # create a template completer
        from blurdev import template

        from PyQt4.QtCore import Qt
        from PyQt4.QtGui import QListWidget

        self._templateCompleter = QListWidget(self)
        self._templateCompleter.addItems(template.templNames())
        self._templateCompleter.setWindowFlags(Qt.Popup)
        self._templateCompleter.installEventFilter(self)

        # create the filesystem model for the explorer tree
        from PyQt4.QtGui import QFileSystemModel

        # create the system model
        model = QFileSystemModel()
        model.setRootPath('')
        self.uiExplorerTREE.setModel(model)
        for i in range(1, 4):
            self.uiExplorerTREE.setColumnHidden(i, True)

        # bind the mimeData method
        import blurdev

        blurdev.bindMethod(self.uiProjectTREE, 'mimeData', self.projectMimeData)

        self.restoreSettings()
        self.refreshRecentFiles()
        self.setupIcons()

        blurdev.setAppUserModelID('BlurIDE')

        # make tree's resize to contents so they have a horizontal scroll bar
        for header in (
            self.uiProjectTREE.header(),
            self.uiOpenTREE.header(),
            self.uiExplorerTREE.header(),
        ):
            header.setStretchLastSection(False)
            header.setMovable(False)
            header.setResizeMode(header.ResizeToContents)

        # create connections
        self.uiProjectTREE.itemDoubleClicked.connect(self.editItem)
        self.uiProjectTREE.customContextMenuRequested.connect(self.showProjectMenu)
        self.uiProjectTREE.itemExpanded.connect(self.projectInitItem)
        self.uiOpenTREE.itemClicked.connect(self.editItem)
        self.uiExplorerTREE.doubleClicked.connect(self.editItem)
        self.uiExplorerTREE.customContextMenuRequested.connect(self.showExplorerMenu)
        self.uiWindowsAREA.subWindowActivated.connect(self.updateTitle)
        self.uiWindowsAREA.subWindowActivated.connect(self.checkOpen)
        self.documentTitleChanged.connect(self.refreshOpen)

        # connect file menu
        self.uiNewACT.triggered.connect(self.documentNew)
        self.uiNewFromWizardACT.triggered.connect(self.documentFromWizard)
        self.uiOpenACT.triggered.connect(self.documentOpen)
        self.uiCloseACT.triggered.connect(self.documentClose)
        self.uiCloseAllACT.triggered.connect(self.documentCloseAll)
        self.uiCloseAllExceptACT.triggered.connect(self.documentCloseAllExcept)
        self.uiSaveACT.triggered.connect(self.documentSave)
        self.uiSaveAsACT.triggered.connect(self.documentSaveAs)
        self.uiSaveAllACT.triggered.connect(self.documentSaveAll)
        self.uiExitACT.triggered.connect(self.close)

        # project menus
        self.uiNewProjectACT.triggered.connect(self.projectNew)
        self.uiOpenProjectACT.triggered.connect(self.projectOpen)
        self.uiOpenFavoritesACT.triggered.connect(self.projectFavorites)
        self.uiEditProjectACT.triggered.connect(self.projectEdit)
        self.uiCloseProjectACT.triggered.connect(self.projectClose)

        # connect edit menu
        self.uiUndoACT.triggered.connect(self.documentUndo)
        self.uiRedoACT.triggered.connect(self.documentRedo)
        self.uiCutACT.triggered.connect(self.documentCut)
        self.uiCopyACT.triggered.connect(self.documentCopy)
        self.uiPasteACT.triggered.connect(self.documentPaste)
        self.uiSelectAllACT.triggered.connect(self.documentSelectAll)
        self.uiSelectToMatchingBraceACT.triggered.connect(self.documentSelectMatching)
        self.uiInsertTemplateACT.triggered.connect(self.documentChooseTemplate)
        self.uiCommentAddACT.triggered.connect(self.documentCommentAdd)
        self.uiCommentRemoveACT.triggered.connect(self.documentCommentRemove)
        self._templateCompleter.itemClicked.connect(self.documentInsertTemplate)

        # connect search menu
        self.uiFindAndReplaceACT.triggered.connect(self.showSearchReplaceDialog)
        self.uiFindACT.triggered.connect(self.showSearchDialog)
        self.uiFindInFilesACT.triggered.connect(self.showSearchFilesDialog)
        self.uiFindNextACT.triggered.connect(self.documentFindNext)
        self.uiFindPrevACT.triggered.connect(self.documentFindPrev)
        self.uiReplaceACT.triggered.connect(self.documentReplace)
        self.uiReplaceAllACT.triggered.connect(self.documentReplaceAll)
        self.uiGotoACT.triggered.connect(self.documentGoTo)
        self.uiAddRemoveMarkerACT.triggered.connect(self.documentMarkerToggle)
        self.uiNextMarkerACT.triggered.connect(self.documentMarkerNext)
        self.uiClearMarkersACT.triggered.connect(self.documentMarkerClear)

        # connect run menu
        self.uiRunScriptACT.triggered.connect(self.documentExec)
        self.uiCleanRunACT.triggered.connect(self.documentExecClean)
        self.uiCleanPathsACT.triggered.connect(self.cleanEnvironment)

        # connect view menu
        self.uiDisplayWindowsACT.triggered.connect(self.displayWindows)
        self.uiDisplayTabsACT.triggered.connect(self.displayTabs)
        self.uiDisplayTileACT.triggered.connect(self.uiWindowsAREA.tileSubWindows)
        self.uiDisplayCascadeACT.triggered.connect(self.uiWindowsAREA.cascadeSubWindows)

        # connect tools menu
        self.uiDesignerACT.triggered.connect(self.showDesigner)
        self.uiTreegruntACT.triggered.connect(blurdev.core.showTreegrunt)
        self.uiShowLoggerACT.triggered.connect(blurdev.core.showLogger)

        # connect advanced menu
        self.uiConfigurationACT.triggered.connect(self.showConfig)

        # connect help menu
        self.uiHelpAssistantACT.triggered.connect(self.showAssistant)
        self.uiSdkBrowserACT.triggered.connect(self.showSdkBrowser)
        self.uiBlurDevSiteACT.triggered.connect(self.showBlurDevSite)

        # connect debug menu
        blurdev.core.debugLevelChanged.connect(self.refreshDebugLevels)

        self.uiNoDebugACT.triggered.connect(self.setNoDebug)
        self.uiDebugLowACT.triggered.connect(self.setLowDebug)
        self.uiDebugMidACT.triggered.connect(self.setMidDebug)
        self.uiDebugHighACT.triggered.connect(self.setHighDebug)

        # refresh the ui
        self.updateTitle(None)
        self.refreshDebugLevels()

    def checkOpen(self):
        # determine if there have been any changes
        if self.uiOpenTREE.topLevelItemCount() != len(
            self.uiWindowsAREA.subWindowList()
        ):
            self.refreshOpen()

    def createNewFolder(self):
        path = self.currentFilePath()
        if not path:
            return False

        import os

        if os.path.isfile(path):
            path = os.path.split(str(path))[0]

        from PyQt4.QtGui import QInputDialog, QMessageBox

        text, accepted = QInputDialog.getText(self, 'New Folder Name', '')
        if accepted:
            folder = os.path.join(path, str(text))
            try:
                os.mkdir(folder)
            except:
                QMessageBox.critical(
                    self, 'Error Creating Folder', 'Could not create folder: ', folder
                )

        item = self.uiProjectTREE.currentItem()
        if item:
            item.refresh()

    def cleanEnvironment(self):
        import blurdev

        blurdev.activeEnvironment().resetPaths()

    def currentDocument(self):
        window = self.uiWindowsAREA.activeSubWindow()
        if window:
            return window.widget()
        return None

    def currentProject(self):
        return IdeProject.currentProject()

    def currentBasePath(self):
        path = ''
        import os.path

        # load from the project
        if self.uiBrowserTAB.currentIndex() == 0:
            item = self.uiProjectTREE.currentItem()
            if item:
                path = item.filePath()
                if path:
                    path = os.path.split(str(path))[0]
        else:
            path = str(
                self.uiExplorerTREE.model().filePath(self.uiExplorerTREE.currentIndex())
            )
            if path:
                path = os.path.split(str(path))[0]

        return os.path.normpath(path)

    def currentFilePath(self):
        filename = ''

        # load a project file
        if self.uiBrowserTAB.currentIndex() == 0:
            item = self.uiProjectTREE.currentItem()
            if item:
                filename = item.filePath()

        # load an explorer file
        elif self.uiBrowserTAB.currentIndex() == 2:
            filename = str(
                self.uiExplorerTREE.model().filePath(self.uiExplorerTREE.currentIndex())
            )

        return filename

    def closeEvent(self, event):
        closedown = True
        for window in self.uiWindowsAREA.subWindowList():
            if not window.widget().checkForSave():
                closedown = False

        if closedown:
            self.recordSettings()
            Window.closeEvent(self, event)
        else:
            event.ignore()

    def displayTabs(self):
        self.uiWindowsAREA.setViewMode(self.uiWindowsAREA.TabbedView)
        self.uiDisplayTabsACT.setEnabled(False)
        self.uiDisplayWindowsACT.setEnabled(True)

    def displayWindows(self):
        self.uiWindowsAREA.setViewMode(self.uiWindowsAREA.SubWindowView)
        self.uiDisplayTabsACT.setEnabled(True)
        self.uiDisplayWindowsACT.setEnabled(False)

    def documents(self):
        return [subwindow.widget() for subwindow in self.uiWindowsAREA.subWindowList()]

    def documentClose(self):
        window = self.uiWindowsAREA.activeSubWindow()
        if window and window.widget().checkForSave():
            self._closing = True
            window.close()
            self._closing = False
            return True
        return False

    def documentCloseAll(self):
        for window in self.uiWindowsAREA.subWindowList():
            if window.widget().checkForSave():
                self._closing = True
                window.close()
                self._closing = False

    def documentCloseAllExcept(self):
        for window in self.uiWindowsAREA.subWindowList():
            if (
                window != self.uiWindowsAREA.activeSubWindow()
                and window.widget().checkForSave()
            ):
                self._closing = True
                window.close()
                self._closing = False

    def documentCut(self):
        doc = self.currentDocument()
        if doc:
            doc.cut()

    def documentCommentAdd(self):
        doc = self.currentDocument()
        if doc:
            doc.commentAdd()

    def documentCommentRemove(self):
        doc = self.currentDocument()
        if doc:
            doc.commentRemove()

    def documentCopy(self):
        doc = self.currentDocument()
        if doc:
            doc.copy()

    def documentExec(self):
        doc = self.currentDocument()
        if doc:
            doc.exec_()

    def documentExecClean(self):
        self.cleanEnvironment()
        doc = self.currentDocument()
        if doc:
            doc.exec_()

    def documentFindNext(self):
        doc = self.currentDocument()
        if not doc:
            return False

        doc.findNext(self.searchText(), self.searchFlags())
        return True

    def documentFindPrev(self):
        doc = self.currentDocument()
        if not doc:
            return False

        doc.findPrev(self.searchText(), self.searchFlags())
        return True

    def documentReplace(self):
        doc = self.currentDocument()
        if not doc:
            return False

        count = doc.replace(self.replaceText())
        return True

    def documentReplaceAll(self):
        doc = self.currentDocument()
        if not doc:
            return False

        count = doc.replace(self.replaceText(), all=True)

        # show the results in the messagebox
        from PyQt4.QtGui import QMessageBox

        QMessageBox.critical(self, 'Replace Results', '%i results replaced' % count)

    def documentFromWizard(self):
        from PyQt4.QtCore import QDir

        QDir.setCurrent(self.currentFilePath())

        from idewizardbrowser import IdeWizardBrowser

        if IdeWizardBrowser.createFromWizard():
            self.projectRefreshItem()

    def documentGoTo(self):
        doc = self.currentDocument()
        if doc:
            doc.goToLine()

    def documentChooseTemplate(self):
        from PyQt4.QtGui import QCursor

        self._templateCompleter.move(QCursor.pos())
        self._templateCompleter.show()

    def documentInsertTemplate(self, item):
        if not item:
            return

        doc = self.currentDocument()
        if doc:
            options = {}

            fname = doc.filename()
            options['selection'] = doc.selectedText()
            options['filename'] = fname

            # include package, module info for python files
            import os.path, blurdev

            if os.path.splitext(fname)[1].startswith('.py'):
                options['package'] = blurdev.packageForPath(os.path.split(fname)[0])
                mname = os.path.basename(fname).split('.')[0]

                if mname != '__init__':
                    options['module'] = mname
                else:
                    options['module'] = ''

            from blurdev import template

            text = template.templ(item.text(), options)
            if text:
                doc.removeSelectedText()
                doc.insert(text)

        self._templateCompleter.close()

    def documentMarkerToggle(self):
        doc = self.currentDocument()
        if doc:
            doc.markerToggle()

    def documentMarkerNext(self):
        doc = self.currentDocument()
        if doc:
            doc.markerNext()

    def documentMarkerClear(self):
        doc = self.currentDocument()
        if doc:
            doc.markerDeleteAll()

    def documentPaste(self):
        doc = self.currentDocument()
        if doc:
            doc.paste()

    def documentNew(self):
        from documenteditor import DocumentEditor

        editor = DocumentEditor(self)
        window = self.uiWindowsAREA.addSubWindow(editor)
        window.setWindowTitle(editor.windowTitle())
        window.installEventFilter(self)
        window.show()

    def documentOpen(self):
        from PyQt4.QtGui import QFileDialog
        import lexers

        filename = QFileDialog.getOpenFileName(
            self, 'Open file...', '', lexers.fileTypes()
        )
        if filename:
            self.load(filename)

    def documentOpenRecentTriggered(self, action):
        filename = unicode(action.data().toString())
        if filename:
            self.load(filename)

    def documentRedo(self):
        doc = self.currentDocument()
        if doc:
            doc.redo()

    def documentSave(self):
        doc = self.currentDocument()
        if doc:
            doc.save()

    def documentSaveAs(self):
        doc = self.currentDocument()
        if doc:
            if doc.saveAs():
                self.recordRecentFile(doc.filename())

    def documentSaveAll(self):
        for window in self.uiWindowsAREA.subWindowList():
            window.widget().save()

    def documentSelectAll(self):
        doc = self.currentDocument()
        if doc:
            doc.selectAll()

    def documentSelectMatching(self):
        doc = self.currentDocument()
        if doc:
            doc.selectToMatchingBrace()

    def documentUndo(self):
        doc = self.currentDocument()
        if doc:
            doc.undo()

    def dragEnterEvent(self, event):
        # allow drag & drop events for files
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

        # allow drag & drop events for tools
        source = event.source()
        if source and source.inherits('QTreeWidget'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # allow drag & drop events for files
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

        # allow drag & drop events for tools
        source = event.source()
        if source and source.inherits('QTreeWidget'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        # drop a file
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            import os.path

            for url in urls:
                text = str(url.toString())
                if text.startswith('file:///'):
                    filename = text.replace('file:///', '')

                    # if we're in linux, make sure to start with a '/'
                    from blurdev import settings

                    if settings.OS_TYPE != 'Windows' and not filename.startswith('/'):
                        filename = '/' + filename

                    self.load(filename)

        # drop a tool
        else:
            source = event.source()
            item = source.currentItem()

            tool = None
            try:
                tool = item.tool()
            except:
                pass

            if tool:
                self.setCurrentProject(IdeProject.fromTool(tool))

    def editItem(self):
        filename = str(self.currentFilePath())

        # load the file
        if filename:
            import os.path

            if not os.path.isfile(filename):
                return False

            from PyQt4.QtCore import Qt

            # when shift+doubleclick, run the file
            from PyQt4.QtGui import QApplication

            modifiers = QApplication.instance().keyboardModifiers()

            # run script
            if modifiers == Qt.ShiftModifier:
                self.runCurrentScript()

            # run standalone
            elif modifiers == (Qt.ShiftModifier | Qt.ControlModifier):
                self.runCurrentStandalone()

            # load in the editor
            else:
                self.load(filename)

        # focus an existing item
        elif self.uiBrowserTAB.currentIndex() == 1:
            self.uiWindowsAREA.subWindowList()[
                self.uiOpenTREE.indexOfTopLevelItem(self.uiOpenTREE.currentItem())
            ].setFocus()

    def eventFilter(self, object, event):
        if object == self._templateCompleter:
            from PyQt4.QtCore import Qt

            if event.type() == event.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self._templateCompleter.close()

                elif event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                    self.documentInsertTemplate(self._templateCompleter.currentItem())

            return False

        if not self._closing and event.type() == event.Close:
            if not object.widget().checkForSave():
                event.ignore()
                return True
        return False

    def initialize(self):
        """ initialize the settings once the application has loaded """

        # restore initial files
        for filename in self._initfiles:
            self.load(filename)

        # initialize the logger
        import blurdev

        blurdev.core.logger(self)

        # launch with a given filename
        if 'BIDE_FILENAME' in os.environ:
            self.load(os.environ['BIDE_FILENAME'])

    def load(self, filename, lineno=0):
        filename = str(filename)

        from PyQt4.QtCore import QFileInfo

        if not QFileInfo(filename).isFile():
            return False

        # record the file to the recent files
        self.recordRecentFile(filename)

        # make sure the file is not already loaded
        for window in self.uiWindowsAREA.subWindowList():
            if window.widget().filename() == filename:
                window.setFocus()
                return True

        import os

        ext = os.path.splitext(str(filename))[1]

        # run inside of a command context, provided ALT is not selected
        from PyQt4.QtCore import Qt
        from PyQt4.QtGui import QApplication

        mods = QApplication.instance().keyboardModifiers()

        cmd, key, path = IdeEditor.Registry.get(ext, ('', '', ''))

        # load using a command from the registry
        if mods != Qt.AltModifier and ext == '.sdk':
            # launch a blur SDK file
            import blurdev

            blurdev.core.sdkBrowser().showSdk(filename)

        elif mods != Qt.AltModifier and cmd:
            from PyQt4.QtCore import QProcess

            if key:
                args = [key, filename]
            else:
                args = [filename]
            QProcess.startDetached(cmd, args, path)

        # load a blurproject
        elif mods != Qt.AltModifier and ext == '.blurproj':
            self.setCurrentProject(IdeProject.fromXml(filename))

        # otherwise, load it standard
        else:
            from documenteditor import DocumentEditor

            window = self.uiWindowsAREA.addSubWindow(
                DocumentEditor(self, filename, lineno)
            )
            window.installEventFilter(self)
            window.setWindowTitle(os.path.basename(filename))
            window.show()
            if not self.uiWindowsAREA.viewMode() & self.uiWindowsAREA.TabbedView:
                window.move(10, 10)
                window.resize(
                    self.uiWindowsAREA.width() - 20, self.uiWindowsAREA.height() - 20
                )

    def projectMimeData(self, items):
        from PyQt4.QtCore import QMimeData, QUrl

        data = QMimeData()
        urls = []
        for item in items:
            fpath = item.filePath()
            if fpath:
                urls.append(QUrl('file:///' + fpath))

        data.setUrls(urls)
        return data

    def projectNew(self):
        from ideprojectdialog import IdeProjectDialog
        from ideproject import IdeProject

        proj = IdeProjectDialog.createNew()
        if proj:
            self.setCurrentProject(proj)

    def projectEdit(self):
        from ideprojectdialog import IdeProjectDialog
        from ideproject import IdeProject

        filename = self.currentProject().filename()
        if IdeProjectDialog.edit(filename):
            self.setCurrentProject(IdeProject.fromXml(filename))

    def projectFavorites(self):
        from ideprojectfavoritesdialog import IdeProjectFavoritesDialog

        proj = IdeProjectFavoritesDialog.getProject()
        if proj:
            self.setCurrentProject(proj)

    def projectInitItem(self, item):
        item.load()

    def projectOpen(self):
        from PyQt4.QtGui import QFileDialog

        filename = QFileDialog.getOpenFileName(
            self,
            'Blur IDE Project',
            '',
            'Blur IDE Project (*.blurproj);;XML Files (*.xml);;All Files (*.*)',
        )
        if filename:
            from ideproject import IdeProject

            proj = IdeProject.fromXml(filename)

            # load the project
            self.setCurrentProject(proj)
            self.uiBrowserTAB.setCurrentIndex(0)

    def documentOpenItem(self):
        import os.path

        path = str(self.currentFilePath())
        if os.path.isfile(path):
            self.load(path)

    def documentExploreItem(self):
        import os
        from blurdev import settings

        path = str(self.currentFilePath())
        if os.path.isfile(path):
            if os.name == 'nt':
                os.system('explorer /select,%s' % path.replace('/', '\\'))
                return
            else:
                path = os.path.split(path)[0]

        if os.path.exists(path):
            if settings.OS_TYPE == 'Windows':
                os.startfile(os.path.normpath(path))
            else:
                subprocess.call(os.path.normpath(path), shell=True)
        else:
            from PyQt4.QtGui import QMessageBox

            QMessageBox.critical(
                None, 'Missing Path', 'Could not find %s' % path.replace('/', '\\')
            )

    def projectRefreshItem(self):
        item = self.uiProjectTREE.currentItem()
        if not item:
            return False

        item.refresh()

    def projectClose(self):
        self.setCurrentProject(None)

    def recordSettings(self):
        import blurdev
        from blurdev import prefs

        pref = prefs.find('ide/interface')

        filename = ''
        proj = self.currentProject()
        if proj:
            filename = proj.filename()

        pref.recordProperty('currproj', filename)
        pref.recordProperty('recentFiles', self._recentFiles)

        from ideproject import IdeProject

        pref.recordProperty('proj_favorites', IdeProject.Favorites)
        pref.recordProperty('geom', self.geometry())
        pref.recordProperty('windowState', self.windowState().__int__())

        pref.recordProperty('MidiViewMode', self.uiWindowsAREA.viewMode())
        pref.recordProperty(
            'openFiles',
            [str(doc.filename()) for doc in self.documents() if doc.filename()],
        )

        if blurdev.core.objectName() == 'ide':
            blurdev.core.logger().recordPrefs()

        # record module properties
        from blurdev.ide import ideprefs

        pref.recordModule(ideprefs)

        # save the preferences
        pref.save()

    def recordRecentFile(self, filename):
        if filename in self._recentFiles:
            self._recentFiles.remove(filename)
        self._recentFiles.insert(0, filename)
        self._recentFiles = self._recentFiles[: self._recentFileMax]
        self.refreshRecentFiles()

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

    def refreshOpen(self):
        self.uiOpenTREE.blockSignals(True)
        self.uiOpenTREE.setUpdatesEnabled(False)
        self.uiOpenTREE.clear()

        from PyQt4.QtGui import QTreeWidgetItem

        for window in self.uiWindowsAREA.subWindowList():
            self.uiOpenTREE.addTopLevelItem(
                QTreeWidgetItem([str(window.windowTitle()).strip('*')])
            )

        self.uiOpenTREE.blockSignals(False)
        self.uiOpenTREE.setUpdatesEnabled(True)

    def refreshRecentFiles(self):
        # remove the recent file menu
        if self._recentFileMenu:
            self._recentFileMenu.triggered.disconnect(self.documentOpenRecentTriggered)
            self._recentFileMenu.close()
            self._recentFileMenu.setParent(None)
            self._recentFileMenu.deleteLater()
            self._recentFileMenu = None

        if self._recentFiles:
            # create a new recent file menu
            import os.path
            from PyQt4.QtGui import QMenu, QAction

            self._recentFileMenu = QMenu(self)
            self._recentFileMenu.setTitle('Recent Files')
            self._recentFileMenu.triggered.connect(self.documentOpenRecentTriggered)

            for index, filename in enumerate(self._recentFiles):
                action = QAction(self._recentFileMenu)
                action.setText('%i: %s' % (index + 1, os.path.basename(filename)))
                action.setData(filename)
                self._recentFileMenu.addAction(action)

            self.uiFileMENU.addMenu(self._recentFileMenu)

    def restoreSettings(self):
        import blurdev
        from blurdev import prefs

        pref = prefs.find('ide/interface')

        # load the recent files
        self._recentFiles = pref.restoreProperty('recentFiles', [])

        # update project options
        from ideproject import IdeProject

        self.setCurrentProject(IdeProject.fromXml(pref.restoreProperty('currproj')))

        # update project favorites
        from ideproject import IdeProject

        IdeProject.Favorites = pref.restoreProperty('proj_favorites', [])

        # update ui items
        from PyQt4.QtCore import QRect, Qt

        geom = pref.restoreProperty('geom', QRect())
        if geom and not geom.isNull():
            self.setGeometry(geom)

        try:
            self.setWindowState(Qt.WindowStates(pref.restoreProperty('windowState', 0)))
        except:
            from blurdev import debug

            debug.debugObject(self.restoreSettings, 'error restoring window state')

        # restore tabbed prefrence
        if (
            pref.restoreProperty('MidiViewMode', self.uiWindowsAREA.SubWindowView)
            == self.uiWindowsAREA.TabbedView
        ):
            self.displayTabs()
        else:
            self.displayWindows()

        # restore module settings
        from blurdev.ide import ideprefs

        pref.restoreModule(ideprefs)

        # record which files should load on open
        self._initfiles = pref.restoreProperty('openFiles', [])

    def runCurrentScript(self):
        filename = self.currentFilePath()
        if not filename:
            return False

        import blurdev

        blurdev.core.runScript(filename)
        return True

    def runCurrentStandalone(self):
        filename = self.currentFilePath()
        if not filename:
            return False

        import blurdev

        blurdev.core.runStandalone(filename, basePath=self.currentBasePath())

    def runCurrentStandaloneDebug(self):
        filename = self.currentFilePath()
        if not filename:
            return False

        import blurdev
        from blurdev import debug

        blurdev.core.runStandalone(
            filename, debugLevel=debug.DebugLevel.High, basePath=self.currentBasePath()
        )

    def searchFlags(self):
        return self._searchFlags

    def searchText(self):
        if not (self._searchDialog and self._searchReplaceDialog):
            return ''

        # refresh the search text
        if not (
            self._searchDialog.isVisible() or self._searchReplaceDialog.isVisible()
        ):
            doc = self.currentDocument()
            if doc:
                text = doc.selectedText()
                if text:
                    self._searchText = text

        return self._searchText

    def replaceText(self):
        if not self._searchReplaceDialog:
            return ''

        # refresh the replace results
        return self._searchReplaceDialog.replaceText()

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

    def setupIcons(self):
        from PyQt4.QtGui import QIcon
        import blurdev

        self.setWindowIcon(QIcon(blurdev.resourcePath('img/ide.png')))

        self.uiNoDebugACT.setIcon(QIcon(blurdev.resourcePath('img/debug_off.png')))
        self.uiDebugLowACT.setIcon(QIcon(blurdev.resourcePath('img/debug_low.png')))
        self.uiDebugMidACT.setIcon(QIcon(blurdev.resourcePath('img/debug_mid.png')))
        self.uiDebugHighACT.setIcon(QIcon(blurdev.resourcePath('img/debug_high.png')))

        self.uiNewACT.setIcon(QIcon(blurdev.resourcePath('img/ide/newfile.png')))
        self.uiNewFromWizardACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/newwizard.png'))
        )
        self.uiOpenACT.setIcon(QIcon(blurdev.resourcePath('img/ide/open.png')))
        self.uiCloseACT.setIcon(QIcon(blurdev.resourcePath('img/ide/close.png')))
        self.uiSaveACT.setIcon(QIcon(blurdev.resourcePath('img/ide/save.png')))
        self.uiSaveAsACT.setIcon(QIcon(blurdev.resourcePath('img/ide/saveas.png')))
        self.uiExitACT.setIcon(QIcon(blurdev.resourcePath('img/ide/quit.png')))

        self.uiUndoACT.setIcon(QIcon(blurdev.resourcePath('img/ide/undo.png')))
        self.uiRedoACT.setIcon(QIcon(blurdev.resourcePath('img/ide/redo.png')))
        self.uiCopyACT.setIcon(QIcon(blurdev.resourcePath('img/ide/copy.png')))
        self.uiCutACT.setIcon(QIcon(blurdev.resourcePath('img/ide/cut.png')))
        self.uiCommentAddACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/comment_add.png'))
        )
        self.uiCommentRemoveACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/comment_remove.png'))
        )
        self.uiPasteACT.setIcon(QIcon(blurdev.resourcePath('img/ide/paste.png')))
        self.uiConfigurationACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/preferences.png'))
        )

        self.uiNewProjectACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/newproject.png'))
        )
        self.uiOpenProjectACT.setIcon(QIcon(blurdev.resourcePath('img/ide/open.png')))
        self.uiCloseProjectACT.setIcon(QIcon(blurdev.resourcePath('img/ide/close.png')))
        self.uiEditProjectACT.setIcon(QIcon(blurdev.resourcePath('img/ide/edit.png')))
        self.uiOpenFavoritesACT.setIcon(QIcon(blurdev.resourcePath('img/favorite.png')))

        self.uiCleanPathsACT.setIcon(QIcon(blurdev.resourcePath('img/ide/clean.png')))
        self.uiRunScriptACT.setIcon(QIcon(blurdev.resourcePath('img/ide/run.png')))

        self.uiDisplayRulerACT.setIcon(QIcon(blurdev.resourcePath('img/ide/ruler.png')))
        self.uiDisplayTabsACT.setIcon(QIcon(blurdev.resourcePath('img/ide/tabbed.png')))
        self.uiDisplayCascadeACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/windowed.png'))
        )
        self.uiDisplayTileACT.setIcon(QIcon(blurdev.resourcePath('img/ide/tile.png')))
        self.uiDisplayWindowsACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/windowed.png'))
        )

        self.uiTreegruntACT.setIcon(
            QIcon(
                blurdev.relativePath(
                    blurdev.__file__, 'gui/dialogs/treegruntdialog/img/icon.png'
                )
            )
        )
        self.uiShowLoggerACT.setIcon(QIcon(blurdev.resourcePath('img/ide/console.png')))

        self.uiFindACT.setIcon(QIcon(blurdev.resourcePath('img/ide/find.png')))
        self.uiFindInFilesACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/folder_find.png'))
        )
        self.uiFindAndReplaceACT.setIcon(
            QIcon(blurdev.resourcePath('img/ide/find_replace.png'))
        )
        self.uiGotoACT.setIcon(QIcon(blurdev.resourcePath('img/ide/goto.png')))

        self.uiSdkBrowserACT.setIcon(QIcon(blurdev.resourcePath('img/ide/sdk.png')))
        self.uiHelpAssistantACT.setIcon(QIcon(blurdev.resourcePath('img/ide/qt.png')))
        self.uiDesignerACT.setIcon(QIcon(blurdev.resourcePath('img/ide/qt.png')))
        self.uiBlurDevSiteACT.setIcon(QIcon(blurdev.resourcePath('img/ide/help.png')))

    def show(self):
        Window.show(self)

        # If a filename was passed in on launch, open the file
        if not self._loaded:
            # call the initialize method
            self.initialize()

        self._loaded = True

    def showAssistant(self):
        from PyQt4.QtCore import QProcess

        QProcess.startDetached(os.environ['BDEV_QT_ASSISTANT'], [], '')

    def showBlurDevSite(self):
        import subprocess

        subprocess.call('http://blur-dev.googlecode.com', shell=True)

    def showProjectMenu(self):
        from PyQt4.QtGui import QMenu, QCursor, QIcon
        import blurdev

        menu = QMenu(self)
        menu.addAction(self.uiNewACT)
        act = menu.addAction('New Folder')
        act.triggered.connect(self.createNewFolder)
        act.setIcon(QIcon(blurdev.resourcePath('img/ide/newfolder.png')))
        menu.addAction(self.uiNewFromWizardACT)
        menu.addSeparator()
        act = menu.addAction('Open')
        act.triggered.connect(self.documentOpenItem)
        act.setIcon(QIcon(blurdev.resourcePath('img/ide/open.png')))
        menu.addAction('Explore').triggered.connect(self.documentExploreItem)
        act = menu.addAction('Refresh')
        act.triggered.connect(self.projectRefreshItem)
        act.setIcon(QIcon(blurdev.resourcePath('img/refresh.png')))
        menu.addSeparator()
        act = menu.addAction('Run...')
        act.triggered.connect(self.runCurrentScript)
        act.setIcon(QIcon(blurdev.resourcePath('img/ide/run.png')))
        menu.addAction('Run (Standalone)...').triggered.connect(
            self.runCurrentStandalone
        )
        menu.addAction('Run (Debug)...').triggered.connect(
            self.runCurrentStandaloneDebug
        )
        menu.addSeparator()
        menu.addAction(self.uiEditProjectACT)

        menu.popup(QCursor.pos())

    def showExplorerMenu(self):
        from PyQt4.QtGui import QMenu, QCursor

        menu = QMenu(self)
        menu.addAction(self.uiNewACT)
        menu.addAction('New Folder').triggered.connect(self.createNewFolder)
        menu.addAction(self.uiNewFromWizardACT)
        menu.addSeparator()
        menu.addAction('Open').triggered.connect(self.documentOpenItem)
        menu.addAction('Explore').triggered.connect(self.documentExploreItem)
        menu.addSeparator()
        menu.addAction('Run...').triggered.connect(self.runCurrentScript)
        menu.addAction('Run (Standalone)...').triggered.connect(
            self.runCurrentStandalone
        )
        menu.addAction('Run (Debug)...').triggered.connect(
            self.runCurrentStandaloneDebug
        )

        menu.popup(QCursor.pos())

    def showConfig(self):
        from blurdev.config import configSet

        configSet.edit()

    def showDesigner(self):
        from PyQt4.QtCore import QProcess

        QProcess.startDetached(os.environ['BDEV_QT_DESIGNER'], [], '')

    def showSdkBrowser(self):
        import blurdev

        blurdev.core.sdkBrowser().show()

    def showSearchDialog(self):
        self._searchDialog.search(self.searchText())

    def showSearchReplaceDialog(self):
        self._searchReplaceDialog.search(self.searchText())

    def showSearchFilesDialog(self):
        if not self._searchFileDialog:
            from blurdev.ide.findfilesdialog import FindFilesDialog

            self._searchFileDialog = FindFilesDialog.instance(self)
            self._searchFileDialog.fileDoubleClicked.connect(self.load)
        self._searchFileDialog.show()

    def setCurrentProject(self, project):
        # check to see if we should prompt the user before changing projects
        change = True
        import os.path

        if (
            project
            and IdeProject.currentProject()
            and os.path.normcase(project.filename())
            != os.path.normcase(IdeProject.currentProject().filename())
        ):
            from PyQt4.QtGui import QMessageBox

            change = (
                QMessageBox.question(
                    self,
                    'Change Projects',
                    'Are you sure you want to change to the %s project?'
                    % project.text(0),
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
            )

        if change:
            self.uiProjectTREE.blockSignals(True)
            self.uiProjectTREE.setUpdatesEnabled(False)

            IdeProject.setCurrentProject(project)
            self.uiProjectTREE.clear()
            self.uiProjectTREE.addTopLevelItem(project)
            self.uiProjectTREE.blockSignals(False)
            self.uiProjectTREE.setUpdatesEnabled(True)

            self.currentProjectChanged.emit(project)

    def setSearchText(self, text):
        self._searchText = text

    def setSearchFlags(self, flags):
        self._searchFlags = flags

    def shutdown(self):
        # close out of the ide system
        from PyQt4.QtCore import Qt

        # if this is the global instance, then allow it to be deleted on close
        if self == IdeEditor._instance:
            self.setAttribute(Qt.WA_DeleteOnClose, True)
            IdeEditor._instance = None

        # clear out the system
        self.close()

    def updateTitle(self, window):
        import blurdev
        from blurdev import version

        proj = self.currentProject()
        if proj:
            projtext = 'Project: %s' % proj.text(0)
        else:
            projtext = 'Project: <None>'

        if window:
            path = window.widget().filename().replace('/', '\\')
            self.setWindowTitle(
                '%s | %s - [%s] - %s'
                % (
                    str(blurdev.core.objectName()).capitalize(),
                    projtext,
                    path,
                    version.toString(),
                )
            )
        else:
            self.setWindowTitle(
                '%s | %s - %s'
                % (
                    str(blurdev.core.objectName()).capitalize(),
                    projtext,
                    version.toString(),
                )
            )

    @staticmethod
    def createNew():
        window = IdeEditor.instance()
        window.documentNew()
        window.show()

    @staticmethod
    def instance(parent=None, filename=None):
        # create the instance for the logger
        if not IdeEditor._instance:
            # determine default parenting
            import blurdev

            parent = None
            if not blurdev.core.isMfcApp():
                parent = blurdev.core.rootWindow()

            # create the logger instance
            inst = IdeEditor(parent)

            # protect the memory
            from PyQt4.QtCore import Qt

            inst.setAttribute(Qt.WA_DeleteOnClose, False)

            # cache the instance
            IdeEditor._instance = inst

        return IdeEditor._instance

    @staticmethod
    def edit(filename=None):
        window = IdeEditor.instance()
        window.show()

        # set the filename
        if filename:
            window.load(filename)
