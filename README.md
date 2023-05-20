# PrEditor

A python Editor and console based on Qt.


# Examples

Common method for adding PrEditor to a Qt widget on startup. This will only create
the PrEditor gui if the user uses the action, but it will be able to show all
`sys.stdout` and `sys.stderr` output written after the `connect_preditor` call.
It will still continue to write to the original stdout/stderr so any existing
output features still work.

```py
# Capture sys.stdout and sys.stderr while still passing the output to
# the original outputs.
# Create your window or dialog
from Qt.QtWidgets import QMainWindow
import preditor

# Create your GUI instance
window = QMainWindow()

# Create a keyboard shortcut to launch preditor and start capturing sys.stdout
# and sys.stderr writes.
action = preditor.connect_preditor(window)
# Add the newly created action to the menu
window.menuBar().addAction(action)
```

Steps for initialization of a more complex application where you don't have
control over the initialization of the Gui(like Maya).

```py
# Step 1: Capture sys.stdout and sys.stderr output to a buffer as early as
# possible without creating the gui. Add this code to a plugin that gets loaded
# as early as possible. This can even be run before the gui is created.
import preditor.stream
preditor.stream.install_to_std()

# Step 2(optional, and rarely needed in host apps): If not already running in
# a QApplication instance, create one.
import preditor.gui.app
preditor.gui.app.App('test')

# Step 3: Add a way for the user to trigger calling this code to actually show
# the PrEditor gui.
import preditor
preditor.show()

# Step 4: When closing the application, calling this will ensure that the
# current PrEditor gui's state is saved. It's safe and fast to call this even
# if the gui was never created.
preditor.shutdown()
```

# Installing

`pip install preditor`

## cli

PrEditor is intended to be installed inside existing applications like Maya,
Houdini, Nuke etc, so it doesn't make sense to require installing packages like
click for those installs. If you are setting up a system wide install and want
to use the cli interface, you will need to install the cli optional dependencies.

`pip install preditor[cli,shortcut]`

### Creating shortcuts

If you want to be able to create desktop shortcuts from the cli to launch
PrEditor, you will also need to include the `shortcut` dependencies. Currently
this is only useful for windows.

`pip install preditor[cli,shortcut]`

# Plugins

PrEditor is can be extended using entry point plugins defined by other pip packages.

* `preditor.plug.about_module`: Used to add information about various packages
like version and install location to the output of `preditor.about_preditor()`.
This is what generates the text shown by Help menu -> About PrEditor. See
sub-classes of `AboutModule` in `preditor.about_module` and how those are
added in [setup.cfg](setup.cfg).

* `preditor.plug.editors`: Used to add new workbox editors to PrEditor. See
[workbox_text_edit.py](preditor/gui/workbox_text_edit.py) for an example of
implementing a workbox. See [workbox_mixin.py](preditor/gui/workbox_mixin.py)
for the full interface to implement all features of an editor.

* `preditor.plug.logging_handlers`: Used to add custom python logging handlers
to the LoggingLevelButton's handlers sub-menus. This allows you to install a
handler instance on a specific logging object.