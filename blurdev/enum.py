import re
import sys
import inspect
from numbers import Number

# =============================================================================
# CLASSES
# =============================================================================


class _MetaEnumGroup(type):
    def __new__(cls, className, bases, classDict):
        newCls = type.__new__(cls, className, bases, classDict)
        newCls.__init_enums__()
        newCls._cls = cls
        return newCls

    def fromValue(self, value):
        value = int(value)
        for e in list(self):
            if int(e) == value:
                return e

    def keys(self):
        return [str(e) for e in self._ENUMERATORS]

    def values(self):
        return [int(e) for e in self._ENUMERATORS]

    def __getitem__(self, key):
        if isinstance(key, Number):
            return list(self)[int(key)]
        else:
            return getattr(self, str(key))

    def __iter__(self):
        for e in self._ENUMERATORS:
            yield e

    def __instancecheck__(cls, inst):
        if type(inst) == cls:
            return True
        if isinstance(inst, cls._cls):
            return True
        return False


# =============================================================================


class Enum(object):
    """A basic enumerator class.

    Enumerators are named values that act as identifiers.  Typically, a
    list of enumerators are component pieces of an `EnumGroup`.

    Example:
        class Suit(Enum):
            pass
        
        class Suits(EnumGroup):
            Hearts = Suit()
            Spades = Suit()
            Clubs = Suit()
            Diamonds = Suit()

    Enum objects can be combined and compared using binary "and" and "or"
    operations.

    Example:
        mySuits = Suits.Hearts | Suits.Spades
        
        if Suits.Hearts & mySuits:
            print "This is true!"
        
        if Suits.Clubs & mySuits:
            print "This is false!"

    Attributes:
        name: The name of the enumerator.
        number: The integer value representation of the enumerator.
        label: The enumerator's label.
        labelIndex: The enumerator's index within its parent EnumGroup.
    """

    _REMOVEREGEX = re.compile('[_ ]+')
    _CREATIONORDER = 0

    def __init__(self, number=None, label=None, **kwargs):
        """Initializes a new Enum object.

        In addition to the named arguments listed below, keyword arguments
        may be given that will be set as attributes on the Enum.

        Args:
            number(int): The integer representation of the Enum. The default
                is to have this number determined dynamically based on its
                place with the parent EnumGroup.
            label(str): The Enum's label. The default is to inherit the
                attribute name the Enum is associated with in its parent
                EnumGroup.
        """
        self._creationOrder = Enum._CREATIONORDER
        Enum._CREATIONORDER += 1
        self._name = None
        self._number = number
        self._label = label
        self._labelIndex = None
        self._cmpLabel = None
        self._cmpName = None
        self._enumGroup = None
        if kwargs:
            self.__dict__.update(kwargs)

    @property
    def name(self):
        """The name of the Enum."""
        return self._name

    @property
    def number(self):
        """The number representation of the Enum."""
        return self._number

    @property
    def label(self):
        """The Enum's label."""
        return self._label

    @property
    def labelIndex(self):
        """The Enum's index within its parent EnumGroup."""
        return self._labelIndex

    def _setName(self, name):
        if name == None:
            self._name = None
            self._cmpName = None
        else:
            self._name = name
            self._cmpName = self.toComparisonStr(name)

    def _setLabel(self, label):
        if label == None:
            self._label = None
            self._cmpLabel = None
        else:
            self._label = label
            self._cmpLabel = self.toComparisonStr(label)

    def __and__(self, other):
        return int(self) & int(other)

    def __rand__(self, other):
        return int(other) & int(self)

    def __or__(self, other):
        return int(self) | int(other)

    def __ror__(self, other):
        return int(other) | int(self)

    def __hash__(self):
        return self.number

    def __int__(self):
        return self.number

    def __str__(self):
        if self.label is None:
            return self.name
        return self.label

    def __cmp__(self, value):
        if not isinstance(value, Enum):
            return -1
        return self.number - value.number

    def __repr__(self):
        if self._enumGroup == None:
            enumGroupName = ""
        else:
            enumGroupName = self._enumGroup.__name__
        return '<{mdl}.{cls}.{name}>'.format(
            mdl=self.__class__.__module__,
            cls=self.__class__.__name__,
            name=str(self.name),
        )

    def __neq__(self, value):
        return not self.__eq__(value)

    def __eq__(self, value):
        if value == None:
            return False
        if isinstance(value, Enum):
            return self.number == value.number
        if isinstance(value, int):
            return self.number == value
        if isinstance(value, str) or isinstance(value, unicode):
            if self._compareStr(value):
                return True
        return False

    def _compareStr(self, inStr):
        cmpStr = self.toComparisonStr(inStr)
        return cmpStr in (self._cmpLabel, self._cmpName)

    @classmethod
    def toComparisonStr(cls, value):
        return cls._REMOVEREGEX.sub('', str(value).lower())


# =============================================================================


class EnumGroup(object):
    """A container class for collecting, organizing, and accessing Enums.

    An EnumGroup class is a container for Enum objects.  It provides
    organizational convenience, and in most cases handles the generation
    and assignment of Enum numbers, names, and labels.

    Example:
        class Suit(Enum):
            pass
        
        class Suits(EnumGroup):
            Hearts = Suit()
            Spades = Suit()
            Clubs = Suit()
            Diamonds = Suit()

    The above example outlines defining an enumerator, and grouping
    four of them inside of a group.  This provides a number of things,
    including references by attribute, name, and index.  Also provided
    is an "All" attribute, if one is not explicitly assigned, that
    compare true against any members of the group via the binary "and"
    operator.

    Example:
        # By attribute.
        Suits.Hearts
        
        # By name.
        Suits['Hearts']
        
        suitList = list(Suits)
        
        if Suits.Hearts & Suits.All:
            print "This is true!"

    Attributes:
        All: The sum of all members.
    """

    __metaclass__ = _MetaEnumGroup
    _ENUMERATORS = None
    All = 0

    def __init__(self):
        raise InstantiationError('Unable to instantiate static class EnumGroup.')

    @classmethod
    def append(cls, *args, **kwargs):
        """Appends additional enumerators to the EnumGroup.

        New members can be provided as ordered arguments where the
        each Enum's label is used to determine the attribute name, or
        by keyword arguments where the key is the attribute name and
        the Enum is the value.  When using an Enum's label to determine
        its name, any spaces in the label will be converted to underscores.

        Example:
            Suits.append(Suit(None, 'Funky'), Foo=Suit())

            # The "Funky" and "Foo" suits are now available.
            Suits.Funky
            Suits.Foo

        Raises:
            ValueError
        """
        if [e for e in (list(args) + kwargs.values()) if not isinstance(e, Enum)]:
            raise ValueError('Given items must be of class Enum.')
        if [e for e in args if not e.label]:
            raise ValueError('Enums given as ordered arguments must have a label.')
        for e in args:
            setattr(cls, cls._labelToVarName(e.label), e)
        for n, e in kwargs.iteritems():
            setattr(cls, n, e)
        cls.__init_enums__()

    @classmethod
    def join(self, separator=','):
        """Joins all child Enums together into a single string.

        The string representation of each Enum is joined using the
        given separator.

        Args:
            separator(str): The separator to use.  Default is ",".

        Returns:
            str: The joined enumerators.
        """
        return ','.join([str(e) for e in self._ENUMERATORS])

    @classmethod
    def __init_enums__(cls):
        enums = []
        orderedEnums = sorted(
            inspect.getmembers(cls, lambda o: isinstance(o, Enum),),
            key=lambda i: i[1]._creationOrder,
        )
        for name, value in orderedEnums:
            enums.append(value)
            value._enumGroup = cls
            value._setName(name)
            if value.label is None:
                value._setLabel(cls._varNameToLabel(name))
        enumNumbers = [enum.number for enum in enums if enum.number]
        num = 1
        for enum in enums:
            if enum._number == None:
                while num in enumNumbers:
                    num *= 2
                enum._number = num
                enumNumbers.append(num)
        enums.sort()
        labelIndex = 0
        for enum in enums:
            if enum._label != None:
                enum._labelIndex = labelIndex
                labelIndex += 1
        cls._ENUMERATORS = enums
        if isinstance(cls.All, int):
            cls.All = sum(enumNumbers)

    @classmethod
    def _varNameToLabel(cls, varName):
        label = str(varName)
        label = re.sub(r'[_]+', ' ', label)
        return label.capitalize()

    @classmethod
    def _labelToVarName(cls, label):
        name = str(label)
        name = re.sub(r'\s+', '_', name)
        return name


# =============================================================================


class enum(object):
    """DEPRECATED: Python based enumerator class.

    This class is deprecated and should be replaced by blurdev.enum.Enum and
    blurdev.enum.EnumGroup.

    A short example::

        >>> Colors = enum("Red", "Yellow", "Blue")
        >>> Color.Red
        1
        >>> Color.Yellow
        2
        >>> Color.Blue
        4
        >>> Color.labelByValue(Color.Blue)
        'Blue'
    """

    INDICES = xrange(sys.maxint)  # indices constant to use for looping

    def __call__(self, key):
        return self.value(key)

    def __getattr__(self, key):
        if key == '__name__':
            return 'enum'
        else:
            raise AttributeError, key

    def __init__(self, *args, **kwds):
        """ Takes the provided arguments adds them as properties of this object. For each argument you
        pass in it will assign binary values starting with the first argument, 1, 2, 4, 8, 16, ....
        If you pass in any keyword arguments it will store the value.
        
        Note: Labels automaticly add spaces for every capital letter after the first, so do not use
        spaces for args, or the keys of kwargs or you will not be able to access those parameters.
        
        :param *args: Properties with binary values are created
        :param **kwds: Properties with passed in values are created
        
        Example::
            >>> e = blurdev.enum.enum('Red', 'Green', 'Blue', White=7)
            >>> e.Blue
            4
            >>> e.White
            7
            >>> e.Red | e.Green | e.Blue
            7
        """
        super(enum, self).__init__()
        self._keys = list(args) + kwds.keys()
        self._compound = kwds.keys()
        self._descr = {}
        key = 1
        for i in range(len(args)):
            self.__dict__[args[i]] = key
            key *= 2

        for kwd, value in kwds.items():
            self.__dict__[kwd] = value

        if not ('All' in args or 'All' in kwds):
            out = 0
            for k in self._keys:
                if isinstance(self.__dict__[k], int):
                    out |= self.__dict__[k]
            self.__dict__['All'] = out

    def count(self):
        return len(self._keys)

    def description(self, value):
        """ Returns the description string for the provided value
        :param value: The binary value of the description you want
        """
        return self._descr.get(value, '')

    def matches(self, a, b):
        """ Does a binary and on a and b
        :param a: First item
        :param b: Second item
        :returns: boolean
        """
        return a & b != 0

    def hasKey(self, key):
        return key in self._keys

    def labels(self, byVal=False):
        """ Returns a list of all provided parameters.
        :param byVal: Sorts the labels by their values. Defaults to False
        :returns: A list of labels as strings
        """
        if byVal:
            return [
                ' '.join(re.findall('[A-Z]+[^A-Z]*', key))
                for key in sorted(self.keys(), key=lambda i: getattr(self, i))
            ]
        return [' '.join(re.findall('[A-Z]+[^A-Z]*', key)) for key in self.keys()]

    def labelByValue(self, value):
        """ Returns the label for a specific value. Labels automaticly add spaces
        for every capital letter after the first.
        :param value: The value you want the label for
        """
        return ' '.join(re.findall('[A-Z]+[^A-Z]*', self.keyByValue(value)))

    def isValid(self, value):
        """ Returns True if this value is stored in the parameters.
        :param value: The value to check
        :return: boolean. Is the value stored in a parameter.
        """
        return self.keyByValue(value) != ''

    def keyByIndex(self, index):
        """ Finds the key based on a index. This index contains the *args in the order they were passed in
        then any **kwargs's keys in the order **kwargs.keys() returned. This index is created when the class
        is initialized.
        :param index: The index to lookup
        :returns: The key for the provided index or a empty string if it was not found.
        """
        if index in range(self.count()):
            return self._keys[index]
        return ''

    def keyByValue(self, value):
        """ Return the parameter name for a specific value. If not found returns a empty string.
        :param value: The value to find the parameter name of.
        :returns: String. The parameter name or empty string.
        """
        for key in self._keys:
            if self.__dict__[key] == value:
                return key
        return ''

    def keys(self):
        """ Returns a list of parameter names
        """
        return self._keys

    def value(self, key, caseSensitive=True):
        """ Return the value for a parameter name
        :param key: The key to get the value for
        :param caseSensitive: Defaults to True
        :returns: The value for the key, or zero if it was not found
        """
        if caseSensitive:
            return self.__dict__.get(str(key), 0)
        else:
            key = str(key).lower()
            for k in self.__dict__.keys():
                if k.lower() == key:
                    return self.__dict__[k]
            return 0

    def values(self):
        """ Returns a list of all values for stored parameters
        """
        return [self.__dict__[key] for key in self.keys()]

    def valueByLabel(self, label, caseSensitive=True):
        """
        Return the binary value fromt the given label.
        :param label: The label you want the binary value of
        :param caseSensitive: Defaults to True
        :returns: the bindary value of the label as a int
        """
        return self.value(''.join(str(label).split(' ')), caseSensitive=caseSensitive)

    def valueByIndex(self, index):
        """ Returns the stored value for the index of a parameter.
        .. seealso:: :meth:`keyByValue`
        .. seealso:: :meth:`value`
        """
        return self.value(self.keyByIndex(index))

    def index(self, key):
        """ Return the index for a key.
        :param key: The key to find the index for
        :returns: Int, The index for the key or -1
        .. seealso:: :meth:`keyByValue`
        """
        if key in self._keys:
            return self._keys.index(key)
        return -1

    def indexByValue(self, value):
        """ Return the index for a value.
        :param value: The value to find the index for
        :returns: Int, the index of the value or -1
        .. seealso:: :meth:`keyByValue`
        """
        for index in range(len(self._keys)):
            if self.__dict__[self._keys[index]] == value:
                return index
        return -1

    def toString(self, value, default='None', sep=' '):
        """ For the provided value return the parameter name(s) seperated by sep. If you provide
        a int that represents two or more binary values, it will return all parameter names that
        binary value represents seperated by sep. If no meaningful value is found it will return
        the provided default.
        :param value: The value to return parameter names of
        :param default: If no parameter were found this is returned. Defaults to 'None'
        :param sep: The parameters are joined by this value. Defaults to a space.
        :return: Returns a string of values or the provided default
        .. seealso:: :meth:`fromString`
        """
        parts = []
        for key in self._keys:
            if not key in self._compound and value & self.value(key):
                parts.append(key)
        if parts:
            return sep.join(parts)
        return default

    def fromString(self, labels, sep=' '):
        """ Returns the value for a given string. This function binary or's the parameters, so it 
        may not work well when using **kwargs
        :param labels: A string of parameter names.
        :param sep: The seperator used to seperate the provided parameters.
        :returns: The found value
        .. seealso:: :meth:`value`
        .. seealso:: :meth:`toString`
        """
        parts = str(labels).split(sep)
        value = 0
        for part in parts:
            value |= self.value(part)
        return value

    def setDescription(self, value, descr):
        """ Used to set a description string for a value.
        :param value: The parameter value to set the description on
        :param descr: The description string to set on a parameter
        """
        self._descr[value] = descr

    matches = classmethod(matches)


# =============================================================================
# EXCEPTIONS
# =============================================================================


class InstantiationError(Exception):
    pass


# =============================================================================
