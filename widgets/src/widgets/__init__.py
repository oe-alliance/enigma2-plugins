from os import listdir
from os.path import isdir, isfile
from os.path import abspath, splitext
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from xml.etree.cElementTree import parse

def importSingleWidget(session, widgetdir):
    print "importing widget from", widgetdir
    widgetname = widgetdir.split("/")[-1]
    module_name, ext = splitext(widgetname + ".widget.py") # Handles no-extension files, etc.
    if ext == '.py' and module_name != "__init__":                
        try:
            #import python part
            spam = __import__(module_name, globals(), locals(), [], -1)
            w = spam.widget.get_widget(session)
            w.setDir(widgetdir)
            #import skin
            skin = parse(widgetdir + "/" + "widget_skin.xml").getroot()
            return widgetname, w, skin, widgetdir, module_name
        
        except (ImportError, IOError), e:                
            print 'Could NOT import widget: %s' % (module_name)
            print 'Exception Caught\n%s' % e
    return False
    print "#" * 20
    
    

def importWidgets(session,):
    widgets = []
    dir = abspath(resolveFilename(SCOPE_PLUGINS) + "Extensions/Widgets/widgets/")
    for widgetdir in listdir(dir):
        abs_path = "/".join([dir, widgetdir])
        if isdir(abs_path):
            if isfile(abs_path + "/widget.py"):
                w = importSingleWidget(session, abs_path)
                if w is not None:
                    widgets.append(w)
            else:
                print "found NO widget.py", abs_path + "/widget.py"
                continue
    return widgets
