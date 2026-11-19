from __future__ import absolute_import

import re
from enum import Enum

from Qt.QtCore import QSortFilterProxyModel, Qt
from Qt.QtGui import QStandardItem, QStandardItemModel


class FocusToNameMode(Enum):
    """Define modes for the Focus To Name Fuzzy Search

    Attributes:
        NORMAL (int): Display the workboxes in the order they appear in PrEditor
        RECENTS_ONLY (int): Display the recently used workboxes
        RECENTS_FIRST (int): Display the recently used workboxes, followed by the
            remaining workboxes in normal order.
    """

    NORMAL = 0
    RECENTS_ONLY = 1
    RECENTS_FIRST = 2

    def displayName(self):
        return self.name.replace('_', ' ').title()

    def toolTip(self):
        toolTipMap = {
            'NORMAL': "Display all tabs in order",
            'RECENTS_ONLY': "Display recent tabs in recent order",
        }
        return toolTipMap.get(self.name, "")


class GroupTabItemModel(QStandardItemModel):
    GroupIndexRole = Qt.ItemDataRole.UserRole + 1
    TabIndexRole = GroupIndexRole + 1

    def __init__(self, manager, *args, **kwargs):
        super(GroupTabItemModel, self).__init__(*args, **kwargs)
        self.manager = manager

    def workbox_indexes_from_model_index(self, index):
        """Returns the group_index and tab_index for the provided QModelIndex"""
        return (
            index.data(self.GroupIndexRole),
            index.data(self.TabIndexRole),
        )

    def pathFromIndex(self, index):
        parts = [""]
        while index.isValid():
            parts.append(self.data(index, Qt.ItemDataRole.DisplayRole))
            index = index.parent()
        if len(parts) == 1:
            return ""
        return "/".join([x for x in parts[::-1] if x])


class GroupTabTreeItemModel(GroupTabItemModel):
    def process(self):
        root = self.invisibleRootItem()
        current_group = self.manager.currentIndex()
        current_tab = self.manager.currentWidget().currentIndex()

        prev_group = -1
        all_widgets = self.manager.all_widgets()
        for _, group_name, tab_name, group_index, tab_index in all_widgets:
            if prev_group != group_index:
                group_item = QStandardItem(group_name)
                group_item.setData(group_index, self.GroupIndexRole)
                root.appendRow(group_item)
                prev_group = group_index

            tab_item = QStandardItem(tab_name)
            tab_item.setData(group_index, self.GroupIndexRole)
            tab_item.setData(tab_index, self.TabIndexRole)
            group_item.appendRow(tab_item)
            if group_index == current_group and tab_index == current_tab:
                self.original_model_index = self.indexFromItem(tab_item)


class GroupTabListItemModel(GroupTabItemModel):
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def process(self, group_tab_mode=FocusToNameMode.NORMAL, recent_workbox_ids=None):
        if recent_workbox_ids is None:
            recent_workbox_ids = []

        root = self.invisibleRootItem()
        current_group = self.manager.currentIndex()
        current_tab = self.manager.currentWidget().currentIndex()

        all_widget_infos = list(self.manager.all_widgets())

        # Organize the list of workboxes to display.
        # - Normal or Recents First - start with original list
        # - Recents Only - start with blank list
        if group_tab_mode == FocusToNameMode.NORMAL or not recent_workbox_ids:
            display_widget_infos = all_widget_infos
        else:
            box_infos_by_id = {
                box_info[0].__workbox_id__(): box_info for box_info in all_widget_infos
            }
            if group_tab_mode == FocusToNameMode.RECENTS_ONLY:
                display_widget_infos = []
            elif group_tab_mode == FocusToNameMode.RECENTS_FIRST:
                display_widget_infos = all_widget_infos

            # Since we are display recents, add them in reverse order, removing
            # from original position if doing Recents First
            recent_workbox_ids = list(reversed(recent_workbox_ids))
            for recent_workbox_id in recent_workbox_ids:
                box_info = box_infos_by_id.get(recent_workbox_id, None)
                if box_info:
                    if box_info in display_widget_infos:
                        display_widget_infos.remove(box_info)
                    display_widget_infos.insert(0, box_info)

        # Now create the items, and note self.original_model_index when we
        # encounter the current workbox's item.
        for info in display_widget_infos:
            _, group_name, tab_name, group_index, tab_index = info
            tab_item = QStandardItem('/'.join((group_name, tab_name)))
            tab_item.setData(group_index, self.GroupIndexRole)
            tab_item.setData(tab_index, self.TabIndexRole)
            root.appendRow(tab_item)
            if group_index == current_group and tab_index == current_tab:
                self.original_model_index = self.indexFromItem(tab_item)


class GroupTabFuzzyFilterProxyModel(QSortFilterProxyModel):
    """Implements a fuzzy search filter proxy model."""

    def __init__(self, parent=None):
        super(GroupTabFuzzyFilterProxyModel, self).__init__(parent=parent)
        self._fuzzy_regex = None

    def setFuzzySearch(self, search):
        search = '.*'.join(search)
        # search = '.*{}.*'.format(search)
        self._fuzzy_regex = re.compile(search, re.I)
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if self.filterKeyColumn() == 0 and self._fuzzy_regex:
            index = self.sourceModel().index(sourceRow, 0, sourceParent)
            data = self.sourceModel().data(index)
            ret = bool(self._fuzzy_regex.search(data))
            return ret

        return super(GroupTabFuzzyFilterProxyModel, self).filterAcceptsRow(
            sourceRow, sourceParent
        )

    def pathFromIndex(self, index):
        parts = [""]
        while index.isValid():
            parts.append(self.data(index, Qt.ItemDataRole.DisplayRole))
            index = index.parent()
        if len(parts) == 1:
            return ""
        return "/".join([x for x in parts[::-1] if x])
