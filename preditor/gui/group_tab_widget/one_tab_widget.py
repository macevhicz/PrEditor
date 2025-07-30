from __future__ import absolute_import

import re
import string

from Qt.QtWidgets import QTabWidget


class OneTabWidget(QTabWidget):
    """A QTabWidget that shows the close button only if there is more than one
    tab. If something removes the last tab, it will add a default tab if the
    default_tab method is implemented on a subclass. This is also used to create
    the first tab on showEvent.

    Subclasses can implement a `default_tab()` method. This should return the
    widget to add and the title of the tab to create if implemented.
    """

    def __init__(self, *args, **kwargs):
        super(OneTabWidget, self).__init__(*args, **kwargs)
        self.tabCloseRequested.connect(self.close_tab)

    def get_name_pattern(self, name):
        part1 = r"^(?P<name>[^\d \n]+)"
        part2 = r"(?P<iteration>\d*)"
        part3 = r"(?P<extension>\.[a-zA-Z]{1,9})?$"
        pattern = part1 + part2 + part3
        pattern = re.compile(pattern)
        return pattern

    def get_name_components(self, name):
        pattern = self.get_name_pattern(name)
        match = pattern.match(name)
        if match:
            dic = match.groupdict()
            base_name = dic.get("name")

            iteration = dic.get("iteration", None)
            iteration = int(iteration) if iteration else None

            extension = dic.get("extension") or ""
        else:
            base_name = name
            iteration = None
            extension = ""

        # Trim any chars which were between name and iteration from base_name
        letters = string.ascii_lowercase + string.ascii_uppercase
        for idx in range(len(base_name), -1, -1):
            char = base_name[idx - 1]
            if char in letters:
                break
        base_name = base_name[:idx]

        return base_name, iteration, extension

    def conform_name(self, name):
        base_name, iteration, extension = self.get_name_components(name)
        iter_str = ""
        if iteration:
            iter_str = str(iteration).zfill(2)
        name = base_name + iter_str + extension
        return name

    def get_next_available_tab_name(self, name=None):
        existing_names = [self.tabText(i).lower() for i in range(self.count())]

        if name is None:
            name = self.default_tab_name

        base_name, iteration, extension = self.get_name_components(name)
        name = self.conform_name(name)

        if iteration is None:
            iteration = 0

        if name.lower() in existing_names:
            for _ in range(1000):
                iteration += 1
                new_iter_str = str(iteration).zfill(2)
                name = base_name + new_iter_str + extension
                if name.lower() not in existing_names:
                    break
        return name

    def addTab(self, *args, **kwargs):  # noqa: N802
        ret = super(OneTabWidget, self).addTab(*args, **kwargs)
        self.update_closable_tabs()
        self.tabBar().setFont(self.window().font())
        return ret

    def close_tab(self, index):
        self.removeTab(index)
        self.update_closable_tabs()

    def index_for_text(self, text):
        """Return the index of the tab with this text. Returns -1 if not found"""
        for i in range(self.count()):
            if self.tabText(i) == text:
                return i
        return -1

    def insertTab(self, *args, **kwargs):  # noqa: N802
        ret = super(OneTabWidget, self).insertTab(*args, **kwargs)
        self.update_closable_tabs()
        return ret

    def removeTab(self, index):  # noqa: N802
        super(OneTabWidget, self).removeTab(index)
        if hasattr(self, 'default_tab') and not self.count():
            self.addTab(*self.default_tab())
        self.update_closable_tabs()

    def showEvent(self, event):  # noqa: N802
        super(OneTabWidget, self).showEvent(event)
        # Force the creation of a default tab if defined
        if hasattr(self, 'default_tab') and not self.count():
            self.addTab(*self.default_tab())

    def update_closable_tabs(self):
        self.setTabsClosable(self.count() != 1)
