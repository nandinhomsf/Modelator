from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from my_canvas import *
from my_model import *


class MyWindow(QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle("MyGLDrawer")
        self.canvas = MyCanvas()
        self.setCentralWidget(self.canvas)
        self.model = MyModel()
        self.canvas.setModel(self.model)
        tb = self.addToolBar("File")
        fit = QAction(QIcon("icons/fit.png"), "fit", self)
        tb.addAction(fit)
        rand = QAction(QIcon("icons/random"), "random", self)
        tb.addAction(rand)
        dialog = QAction(QIcon("icons/config.png"), "dialog", self)
        tb.addAction(dialog)
        temp = QAction(QIcon("icons/temp.png"), "temp", self)
        tb.addAction(temp)
        force = QAction(QIcon("icons/force.png"), "force", self)
        tb.addAction(force)
        export = QAction(QIcon("icons/export"), "export", self)
        tb.addAction(export)
        bezier = QAction(QIcon("icons/bezier.png"), "bezier", self)
        tb.addAction(bezier)
        tb.actionTriggered[QAction].connect(self.tbpressed)

    def tbpressed(self, a):
        if a.text() == "fit":
            self.canvas.fitWorldToViewport()
        elif a.text() == "dialog":
            self.canvas.showDialog()
        elif a.text() == "export":
            self.canvas.export_to_json()
        elif a.text() == "random":
            self.canvas.genRandomPoints()
        elif a.text() == "temp":
            self.canvas.set_up_temp()
        elif a.text() == "force":
            self.canvas.set_up_force()
        elif a.text() == "bezier":
            self.canvas.set_up_bezier2()

