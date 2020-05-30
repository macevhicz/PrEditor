import blurdev
import blurdev.tools.tool
from blurdev.cores.core import Core


class KatanaCore(Core):
    """
    This class is a reimplimentation of the blurdev.cores.core.Core class for running blurdev within Nuke sessions
    """

    # ignore_messages = set(['Cancelled', 'No nodes selected'])

    def __init__(self, *args, **kargs):
        kargs['objectName'] = 'katana'
        super(KatanaCore, self).__init__(*args, **kargs)
        # Disable AppUserModelID. See blurdev.setAppUserModelID for more info.
        self._useAppUserModelID = False

    def toolTypes(self):
        """
        Overloads the toolTypes method from the Core class to show tool types that are related to
        Nuke applications
        """
        output = blurdev.tools.tool.ToolType.Katana
        return output