from collections import defaultdict
import importlib
import six

# fileScreens is a simple database controlling how Series2Folder interacts
# with other classes that view or manipulate the filesystem.

# It is intended to do two jobs:
#  * In background mode, if any screen in either self.session.current_dialog
#    or self.session.dialog_stack is an instance of any class in any
#    value part of fileScreens, any background run of Series2Folder
#    will be deferred until none of those screens is in the current
#    set of active screens.
#
#  * When run manually, the keys in fileScreens are the names of the
#  refresh
#      methods to run in the listed classes in the value tuple in
#      order to refresh the selection list after Series2Folder does
#      the manual update.

# fileScreenTemplates is used to create fileScreens.  It is a tuple
# of tuples in the form:
#    (moduleName, tuple of screenClassNames, refreshMethodName)
# If refreshMethodName is None, then the entry is only used for
# preventing Series2Folder from running when the screen is active.

fileScreens = defaultdict(tuple)

__fileScreenTemplates = (
    ("Screens.MovieSelection", ("MovieSelection", ), "reloadList"),
    ("Plugins.Extensions.EnhancedMovieCenter.MovieSelection", ("EMCSelection", ), "triggerReloadList"),
    ("Plugins.Extensions.AdvancedMovieselection.MovieSelection", ("MovieSelection", ), "reloadList"),
    ("Plugins.Extensions.SerienFilm.MovieSelection", ("MovieSelection", ), "reloadList"),
    ("Plugins.Extensions.FileCommander.plugin", ("FileCommanderScreen", "FileCommanderScreenFileSelect"), None),
    ("Plugins.Extensions.Filebrowser.plugin", ("FilebrowserScreen",), None),
)

for moduleName, classNames, refreshMethod in __fileScreenTemplates:
    for className in classNames:
        try:
            mod = importlib.import_module(moduleName)
            fileScreens[refreshMethod] += (getattr(mod, className), )
        except (ImportError, AttributeError):
            pass

# activeFileScreens() is a convenience function for accessing
# fileScreens.
# When called with allScreens as True, it returns a list of all
# fileScreen entries that are currently active (for plugin background
# mode).
# When called with allScreens as False, it returns alist of all
# currently active fileScreen entries that have a non-None
# refreshMethodName (for plugin manual mode).

def activeFileScreens(session, allScreens):
    current_dialog = session.current_dialog
    activeScreens = []
    if current_dialog:
        for dialog in (current_dialog, ) + tuple(dse[0] for dse in reversed(session.dialog_stack)):
            activeScreens += [(dialog, action) for action, screenClasses in six.iteritems(fileScreens) if (allScreens or action is not None) and isinstance(dialog, screenClasses)]
    return activeScreens
