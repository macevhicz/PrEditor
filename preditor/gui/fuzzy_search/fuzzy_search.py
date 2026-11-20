from __future__ import absolute_import

from functools import partial

from Qt.QtCore import QEvent, QModelIndex, QPoint, Qt, QTimer, Signal
from Qt.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QLineEdit,
    QListView,
    QShortcut,
    QVBoxLayout,
    QWidget,
)

from ..group_tab_widget.grouped_tab_models import GroupTabFuzzyFilterProxyModel


class FuzzySearch(QFrame):
    canceled = Signal("QModelIndex")
    """Passes the original QModelIndex for the tab that was selected when the
    widget was first shown. This lets you reset back to the orignal state."""
    highlighted = Signal("QModelIndex")
    """Emitted when the user navitages to the given index, but hasn't selected."""
    selected = Signal("QModelIndex")
    """Emitted when the user selects a item."""

    focusLeft = Signal()

    def __init__(self, model, parent=None, **kwargs):
        super(FuzzySearch, self).__init__(parent=parent, **kwargs)

        self.y_offset = 100
        self.setMinimumSize(400, 200)
        self.uiCloseSCT = QShortcut(
            Qt.Key.Key_Escape,
            self,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        self.uiCloseSCT.activated.connect(self._canceled)

        self.uiUpSCT = QShortcut(
            Qt.Key.Key_Up, self, context=Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.uiUpSCT.activated.connect(partial(self.increment_selection, -1))
        self.uiDownSCT = QShortcut(
            Qt.Key.Key_Down, self, context=Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.uiDownSCT.activated.connect(partial(self.increment_selection, 1))

        lyt = QVBoxLayout(self)
        self.uiLineEDIT = QLineEdit(parent=self)
        self.uiLineEDIT.textChanged.connect(self.update_completer)
        self.uiLineEDIT.returnPressed.connect(self.activated)
        lyt.addWidget(self.uiLineEDIT)
        self.uiResultsLIST = QListView(self)
        self.uiResultsLIST.activated.connect(self.activated)
        self.proxy_model = GroupTabFuzzyFilterProxyModel(self)
        self.proxy_model.setSourceModel(model)
        self.uiResultsLIST.setModel(self.proxy_model)
        lyt.addWidget(self.uiResultsLIST)

        self.original_model_index = model.original_model_index
        self.uiResultsLIST.setCurrentIndex(self.original_model_index)

        # Scroll to current item. Use single shot, because since the list was
        # just filled in, the view may not have laid out its items yet.
        QTimer.singleShot(
            0,
            lambda: self.uiResultsLIST.scrollTo(
                self.original_model_index, QAbstractItemView.PositionAtCenter
            ),
        )

        self.uiResultsLIST.selectionModel().selectionChanged.connect(
            self.onSelectionChanged
        )

        self._lastTimestamp = None
        QApplication.instance().installEventFilter(self)

    def activated(self):
        current = self.uiResultsLIST.currentIndex()

        # Hide FuzzySearch before emitting signal, because the recently_used_workbox
        # functionality will only update the recents list if fuzzySearch is not
        # visible. This is so the recents list is not updated as user scrolls
        # through choices, but is if/when they make a selection).
        self.hide()
        self.selected.emit(current)

    def increment_selection(self, direction):
        current = self.uiResultsLIST.currentIndex()
        col = 0
        row = 0
        if current.isValid():
            col = current.column()
            row = current.row() + direction
        new = self.uiResultsLIST.model().index(row, col)
        self.uiResultsLIST.setCurrentIndex(new)

    def update_completer(self, wildcard):
        if wildcard:
            if not self.uiResultsLIST.currentIndex().isValid():
                new = self.uiResultsLIST.model().index(0, 0)
                self.uiResultsLIST.setCurrentIndex(new)
        else:
            self.uiResultsLIST.clearSelection()
            self.uiResultsLIST.setCurrentIndex(QModelIndex())
        self.proxy_model.setFuzzySearch(wildcard)
        self.highlighted.emit(self.uiResultsLIST.currentIndex())

    def _canceled(self):
        # Restore the original tab as the user didn't choose the new tab
        self.canceled.emit(self.original_model_index)
        self.hide()

    def reposition(self):
        pgeo = self.parent().geometry()
        geo = self.geometry()
        center = QPoint(pgeo.width() // 2, 0)
        geo.moveCenter(center)
        geo.setY(self.y_offset)
        self.setGeometry(geo)

    def popup(self):
        self.show()
        self.reposition()
        self.uiLineEDIT.setFocus(Qt.FocusReason.PopupFocusReason)

    def _contains(self, widget, container=None):
        if container is None:
            container = self
        # Walk up the parent chain manually: isAncestorOf() stops at window
        # boundaries, so it would treat combo box dropdowns and menus as outside.
        while widget is not None:
            if widget is container:
                return True
            widget = widget.parentWidget()
        return False

    def eventFilter(self, obj, event):
        if not self.isVisible():
            # never block the click
            return False

        if (
            event.type() == QEvent.MouseButtonPress
            and isinstance(obj, QWidget)
            and event.timestamp() != self._lastTimestamp
        ):
            # An ignored press is passed up to each parent widget in turn, and
            # the filter sees every step, so react only once per physical click
            # (ie this is why we are checking the timestamp)
            self._lastTimestamp = event.timestamp()

            # If click is outside of the FuzzySearch widget, we shall close it.
            if not self._contains(obj):
                self.focusLeft.emit()

        # never block the click
        return False

    def onSelectionChanged(self):
        """If the selection has changed, either by clicking an item or scrolling
        up/down via keyboard shortcuts, emit the 'highlight' signal.
        """
        idx = self.uiResultsLIST.currentIndex()
        self.highlighted.emit(idx)
