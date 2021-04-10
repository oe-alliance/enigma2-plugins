from Components.Pixmap import MultiPixmap
 

class KTmultiPixmap(MultiPixmap):
    def __init__(self):
        MultiPixmap.__init__(self)
        self.pixmapFiles = []

    def applySkin(self, desktop, screen):
        if self.skinAttributes is not None:
            for (attrib, value) in self.skinAttributes:
                if attrib == "pixmaps":
                    pixmaps = value.split(',')
                    for p in pixmaps:
                        self.pixmapFiles.append(p)
                    break
        return MultiPixmap.applySkin(self, desktop, screen)
