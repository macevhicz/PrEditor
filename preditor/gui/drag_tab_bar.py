from __future__ import absolute_import

from pathlib2 import Path
from functools import partial

from Qt.QtCore import QByteArray, QMimeData, QPoint, QRect, Qt
from Qt.QtGui import QColor, QCursor, QDrag, QPainter, QPalette, QPixmap, QRegion
from Qt.QtWidgets import (
    QApplication,
    QInputDialog,
    QFileDialog,
    QMenu,
    QSizePolicy,
    QStyle,
    QStyleOptionTab,
    QTabBar,
)

from preditor import osystem


class DragTabBar(QTabBar):
    """A QTabBar that allows you to drag and drop its tabs to other DragTabBar's
    while still allowing you to move tabs normally.

    In most cases you should use `install_tab_widget` to create and add this TabBar
    to a QTabWidget. It takes care of enabling usability features of QTabWidget's.

    Args:
        mime_type (str, optional): Only accepts dropped tabs that implement this
            Mime Type. Tabs dragged off of this TabBar will have this Mime Type
            implemented.

    Based on code by ARussel: https://forum.qt.io/post/420469
    """

    def __init__(self, parent=None, mime_type='DragTabBar'):
        super(DragTabBar, self).__init__(parent=parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self._mime_data = None
        self._context_menu_tab = -1
        self.mime_type = mime_type

        self.color_map = {
            "normal": "lightgrey",
            "linked": "turquoise",
            "dirty": "yellow",
            "missingLinked": "red",
        }
        self.fg_color_map = {
            "0": "white",
            "1": "black",
        }

    def get_color_name(self, index):
        state = "normal"
        toolTip = ""
        if self.parent():
            widget = self.parent().widget(index)
            if hasattr(widget, "text"):
                workbox = widget
                filename = workbox.__filename__()

                dirty = workbox.text() != workbox.__last_saved_text__()
                if dirty:
                    state = "dirty"
                    toolTip = "Workbox has unsaved changes"

                elif filename:
                    if Path(filename).is_file():
                        state = "linked"
                        toolTip = "Linked to file on disk"
                    else:
                        state = "missingLinked"
                        toolTip = "Linked file is missing"

        color_name = self.color_map.get(state)

        return color_name, toolTip

    def paintEvent(self, event):
        style = self.style()
        painter = QPainter(self)
        option = QStyleOptionTab()
        for index in range(self.count()):
            color_name, toolTip = self.get_color_name(index)
            self.setTabToolTip(index, toolTip)

            # Get colors
            color = QColor(color_name)
            fillColor = color.lighter(175)
            color = color.darker(250)

            # Pick white or black for text, based on lightness of fillColor
            fg_idx = int(fillColor.value() >= 128)
            fg_color_name = self.fg_color_map.get(str(fg_idx))
            fg_color = QColor(fg_color_name)

            self.initStyleOption(option, index)
            option.palette.setColor(QPalette.WindowText, fg_color)
            option.palette.setColor(QPalette.Window, color)
            option.palette.setColor(QPalette.Button, fillColor)
            style.drawControl(QStyle.CE_TabBarTab, option, painter)

    def mouseMoveEvent(self, event):  # noqa: N802
        if not self._mime_data:
            return super(DragTabBar, self).mouseMoveEvent(event)

        # Check if the mouse has moved outside of the widget, if not, let
        # the QTabBar handle the internal tab movement.
        event_pos = event.pos()
        global_pos = self.mapToGlobal(event_pos)
        bar_geo = QRect(self.mapToGlobal(self.pos()), self.size())
        inside = bar_geo.contains(global_pos)
        if inside:
            return super(DragTabBar, self).mouseMoveEvent(event)

        # The user has moved the tab outside of the QTabBar, remove the tab from
        # this tab bar and store it in the MimeData, initiating a drag event.
        widget = self._mime_data.property('widget')
        tab_index = self.parentWidget().indexOf(widget)
        self.parentWidget().removeTab(tab_index)
        pos_in_tab = self.mapFromGlobal(global_pos)
        drag = QDrag(self)
        drag.setMimeData(self._mime_data)
        drag.setPixmap(self._mime_data.imageData())
        drag.setHotSpot(event_pos - pos_in_tab)
        cursor = QCursor(Qt.OpenHandCursor)
        drag.setDragCursor(cursor.pixmap(), Qt.MoveAction)
        action = drag.exec_(Qt.MoveAction)
        # If the user didn't successfully add this to a new tab widget, restore
        # the tab to the original location.
        if action == Qt.IgnoreAction:
            original_tab_index = self._mime_data.property('original_tab_index')
            self.parentWidget().insertTab(
                original_tab_index, widget, self._mime_data.text()
            )

        self._mime_data = None

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.LeftButton and not self._mime_data:
            tab_index = self.tabAt(event.pos())

            # While we don't remove the tab on mouse press, capture its tab image
            # and attach it to the mouse. This also stores info needed to handle
            # moving the tab to a new QTabWidget, and undoing the move if the
            # user cancels the drop.
            tab_rect = self.tabRect(tab_index)
            pixmap = QPixmap(tab_rect.size())
            self.render(pixmap, QPoint(), QRegion(tab_rect))

            self._mime_data = QMimeData()
            self._mime_data.setData(self.mime_type, QByteArray())
            self._mime_data.setText(self.tabText(tab_index))
            self._mime_data.setProperty('original_tab_index', tab_index)
            self._mime_data.setImageData(pixmap)
            widget = self.parentWidget().widget(tab_index)
            self._mime_data.setProperty('widget', widget)

            # By default if there are no tabs, the tab bar is hidden. This
            # prevents users from re-adding tabs to the tab bar as only it
            # accepts the tab drops. This preserves the tab bar height
            # after it was drawn with a tab so it should automatically stay
            # the same visual height.
            if not self.minimumHeight():
                self.setMinimumHeight(self.height())

        super(DragTabBar, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._mime_data = None
        super(DragTabBar, self).mouseReleaseEvent(event)

    def dragEnterEvent(self, event):  # noqa: N802
        # if event.mimeData().hasFormat(self.mime_type):
        event.accept()

    def dragLeaveEvent(self, event):  # noqa: N802
        event.accept()

    def dragMoveEvent(self, event):  # noqa: N802
        # If this is not a tab of the same mime type, make the tab under the mouse
        # the current tab so users can easily drop inside that tab.
        if not event.mimeData().hasFormat(self.mime_type):
            event.accept()
            tab_index = self.tabAt(event.pos())
            if tab_index == -1:
                tab_index = self.count() - 1
            if self.currentIndex() != tab_index:
                self.setCurrentIndex(tab_index)

    def dropEvent(self, event):  # noqa: N802
        if not event.mimeData().hasFormat(self.mime_type):
            return
        if event.source().parentWidget() == self:
            return

        event.setDropAction(Qt.MoveAction)
        event.accept()
        counter = self.count()

        mime_data = event.mimeData()
        if counter == 0:
            self.parent().addTab(mime_data.property('widget'), mime_data.text())
        else:
            self.parent().insertTab(
                counter + 1, mime_data.property('widget'), mime_data.text()
            )

    def rename_tab(self):
        """Used by the tab_menu to rename the tab at index `_context_menu_tab`."""
        if self._context_menu_tab != -1:
            current = self.tabText(self._context_menu_tab)
            msg = 'Rename the {} tab to (new name must be unique):'.format(current)

            name, success = QInputDialog.getText(self, 'Rename Tab', msg, text=current)
            name = self.parent().get_next_available_tab_name(name=name)

            if success:
                self.setTabText(self._context_menu_tab, name)

    def tab_menu(self, pos, popup=True):
        """Creates the custom context menu for the tab bar. To customize the menu
        call super setting `popup=False`. This will return the menu for
        customization and you will then need to call popup on the menu.

        This method sets the tab index the user right clicked on in the variable
        `_context_menu_tab`. This can be used in the triggered QAction methods."""

        self._context_menu_tab = self.tabAt(pos)
        if self._context_menu_tab == -1:
            return
        menu = QMenu(self)
        menu.setFont(self.window().font())
        act = menu.addAction('Rename')
        act.triggered.connect(self.rename_tab)

        grouped_tab = self.parentWidget()
        workbox = grouped_tab.widget(self._context_menu_tab)

        # Show File-related actions depending if filename already set
        if hasattr(workbox, 'filename'):
            # if not (workbox.filename() and Path(workbox.filename()).is_file()):
            if not workbox.filename():
                act = menu.addAction('Link File')
                act.triggered.connect(partial(self.link_file, workbox))

                act = menu.addAction('Save and Link File')
                act.triggered.connect(partial(self.save_and_link_file, workbox))
            else:
                act = menu.addAction('Explore File')
                act.triggered.connect(partial(self.explore_file, workbox))

                act = menu.addAction('Unlink File')
                act.triggered.connect(partial(self.unlink_file, workbox))

                act = menu.addAction('Save As')
                act.triggered.connect(partial(self.save_and_link_file, workbox))

            act = menu.addAction('Copy Workbox Name')
            act.triggered.connect(partial(self.copy_workbox_name, workbox))

        if popup:
            menu.popup(self.mapToGlobal(pos))

        return menu

    def link_file(self, workbox):
        filename, _other = QFileDialog.getOpenFileName()
        if filename and Path(filename).is_file():
            workbox.__load__(filename)
            workbox._filename_pref = filename
            name = Path(filename).name
            self.setTabText(self._context_menu_tab, name)
            self.update()

    def save_and_link_file(self, workbox):
        workbox.saveAs()
        filename = workbox.filename()
        workbox._filename_pref = filename
        name = Path(filename).name
        self.setTabText(self._context_menu_tab, name)
        self.update()

    def explore_file(self, workbox):
        path = Path(workbox._filename_pref)
        if path.exists():
            osystem.explore(str(path))
        elif path.parent.exists():
            osystem.explore(str(path.parent))

    def unlink_file(self, workbox):
        workbox.updateFilename("")
        workbox._filename_pref = ""

        name = self.parent().get_next_available_tab_name()
        self.setTabText(self._context_menu_tab, name)

    def copy_workbox_name(self, workbox):
        name = workbox.__workbox_name__()
        QApplication.clipboard().setText(name)

    @classmethod
    def install_tab_widget(cls, tab_widget, mime_type='DragTabBar', menu=True):
        """Creates and returns a instance of DragTabBar and installs it on the
        QTabWidget. This enables movable tabs, and enables document mode.
        Document mode makes the tab bar expand to the size of the QTabWidget so
        drag drop operations are more intuitive.

        Args:
            tab_widget (QTabWidget): The QTabWidget to install the tab bar on.
            mime_data (str, optional): This TabBar will only accept tab drop
                operations with this mime type.
            menu (bool, optional): Install a custom context menu on the bar bar.
                Override `tab_menu` to customize the menu.
        """
        bar = cls(tab_widget, mime_type=mime_type)
        tab_widget.setTabBar(bar)
        tab_widget.setMovable(True)
        tab_widget.setDocumentMode(True)

        sizePolicy = tab_widget.sizePolicy()
        sizePolicy.setVerticalPolicy(QSizePolicy.Preferred)
        tab_widget.setSizePolicy(sizePolicy)

        if menu:
            bar.setContextMenuPolicy(Qt.CustomContextMenu)
            bar.customContextMenuRequested.connect(bar.tab_menu)

        return bar
