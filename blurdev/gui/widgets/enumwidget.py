##
# 	:namespace	python.blurdev.gui.widgets.enumwidget
#
# 	:remarks	The EnumWidget class is a simple expansion system for blurdev.enum.enum class types, allowing dynamic creation
# 				of checkboxes based on the options for a given enum, and supplying simple ways to calculate what the user settings
# 				are
#
# 	:author		beta@blur.com
# 	:author		Blur Studio
# 	:date		04/14/10
#

import re

from PyQt4.QtCore import pyqtSignal, pyqtProperty, Qt, QString
from PyQt4.QtGui import QWidget, QCheckBox, QGridLayout
from blurdev.gui import Dialog
from blurdev.enum import EnumGroup


class EnumWidget(QWidget):

    valueChanged = pyqtSignal(int)

    def __init__(self, parent, enumType=None, columnCount=1, value=0):
        """
            :remarks	Creates a dynamic widget for dealing with enumerated value types
            :param		parent			<QWidget>
            :param		enumType		<blurdev.enum.enum>
            :param		columnCount		<int>				number of columns to split the values into
            :param		value			<int>				current state of the widget
        """
        QWidget.__init__(self, parent)
        # set the custom propreties
        self._columnCount = columnCount  # number of columns to include in the grid
        self._value = value
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setEnumType(enumType)

    def columnCount(self):
        """ returns the number of columns for the grid """
        return self._columnCount

    def enumType(self):
        """ returns the enum class type set for this widget """
        return self._enumType

    def recalculateGrid(self):
        """	regenerates the grid layout with all the appropriate checkboxes """
        # collect the checkboxes and remove them
        for widget in self.findChildren(QCheckBox):
            self.layout().removeWidget(widget)
            widget.close()
        column = 0  # current column
        row = 0  # current row
        # generate the checkboxes
        if self._enumType:
            if isinstance(self._enumType, EnumGroup):
                keys = [et.name for et in self._enumType]
            else:
                keys = self._enumType.keys()
            for key in keys:
                # create a new row when the column requires it
                if column == self.columnCount():
                    column = 0
                    row += 1
                # create the value checkbox
                widget = QCheckBox(self)
                if isinstance(self._enumType, EnumGroup):
                    key = self._enumType[key]
                    widget.setObjectName(key.name)
                    if hasattr(key, 'description'):
                        widget.setToolTip(key.description)
                    enumVal = key
                    name = key.label
                else:
                    # TODO: remove once blurdev.enum.enum is no longer used
                    widget.setObjectName(key)
                    enumVal = self._enumType.value(key)
                    widget.setToolTip(self._enumType.description(enumVal))
                    name = key
                widget.setText(' '.join(re.findall('[A-Z]+[^A-Z]*', name)))
                widget.setChecked((self.value() & enumVal) == enumVal)
                widget.toggled.connect(self.recalculateValue)
                widget.setAttribute(Qt.WA_DeleteOnClose)
                self.layout().addWidget(widget, row, column)
                column += 1
        self.layout().setRowStretch(row + 1, 1)

    def recalculateValue(self):
        """ goes through the checkboxes and calculates the current state of the widget """
        value = 0
        for child in self.findChildren(QCheckBox):
            if child.isChecked():
                if isinstance(self._enumType, EnumGroup):
                    value |= self._enumType[unicode(child.objectName())]
                else:
                    # TODO: remove once blurdev.enum.enum is no longer used
                    value |= self._enumType.value(unicode(child.objectName()))

        self._value = value
        self.valueChanged.emit(value)

    def setColumnCount(self, count):
        """ sets the column count for this widget, recalculating the grid on completion """
        self._columnCount = count
        self.recalculateGrid()

    def setEnumType(self, enumType):
        self._enumType = enumType
        self.recalculateGrid()

    def setValue(self, value):
        """ sets the value for this widget """
        self._value = value
        self.blockSignals(True)
        for child in self.findChildren(QCheckBox):
            if isinstance(self._enumType, EnumGroup):
                enumVal = self._enumType[unicode(child.objectName())]
            else:
                # TODO: remove once blurdev.enum.enum is no longer used
                enumVal = self._enumType.value(unicode(child.objectName()))
            child.setChecked((value & enumVal) == enumVal)
        self.blockSignals(False)
        self.recalculateValue()

    def value(self):
        """ returns the current value state for this widget """
        return self._value

    pyColumnCount = pyqtProperty('int', columnCount, setColumnCount)
    pyEnumValue = pyqtProperty('int', value, setValue)
