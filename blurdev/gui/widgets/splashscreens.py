from __future__ import absolute_import
from Qt.QtGui import QMovie
from Qt.QtWidgets import QApplication, QSplashScreen

# =============================================================================
# CLASSES
# =============================================================================


class AnimatedSplashScreen(QSplashScreen):
    def __init__(self, filePath, *args, **kwargs):
        super(AnimatedSplashScreen, self).__init__(*args, **kwargs)
        self._movie = QMovie(filePath)

    @property
    def movie(self):
        return self._movie

    def show(self):
        self.movie.start()
        self.setPixmap(self.movie.currentPixmap())
        super(AnimatedSplashScreen, self).show()
        while True:
            self.setPixmap(self.movie.currentPixmap())
            self.repaint()
            QApplication.processEvents()
