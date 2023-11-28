import json
import sys

from PyQt5 import QtOpenGL, QtCore
from OpenGL.GL import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

from he.hecontroller import HeController
from he.hemodel import HeModel
from geometry.segments.line import Line
from geometry.point import Point
from compgeom.tesselation import Tesselation
from random import random, randint


class InputDialog(QDialog):
    def __init__(self, title="MeshDialog", labels=["Texto..."], dialogs=1):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)

        self.lineEdits = [None] * dialogs
        self.layout = QVBoxLayout()
        for i in range(dialogs):
            self.lineEdits[i] = QLineEdit()  
            self.layout.addWidget(QLabel("{}:".format(labels[i])))
            self.layout.addWidget(self.lineEdits[i])

        self.pushButton = QPushButton("Confirmar")
        self.pushButton.clicked.connect(self.accept)
        self.layout.addWidget(self.pushButton)

        self.setLayout(self.layout)


class MyCanvas(QtOpenGL.QGLWidget):

    def __init__(self):
        super(MyCanvas, self).__init__()
        self.malha = []
        self.color_v = 1.0
        self.m_model = None
        self.m_w = 0
        self.m_h = 0
        self.m_L = -1000.0
        self.m_R = 1000.0
        self.m_B = -1000.0
        self.m_T = 1000.0
        self.list = None
        self.m_buttonPressed = False
        self.m_pt0 = QtCore.QPointF(0.0, 0.0)
        self.m_pt1 = QtCore.QPointF(0.0, 0.0)
        self._last_mesh_spacing = 1.0
        self._temp = 100.0
        self._var = 1.2
        self.bezier_stage = -1
        self._punch = -1000.0
        self._punch_particles = 10
        self._mass = 7850.0
        self._density = 210000000000.0
        self.m_hmodel = HeModel()
        self.m_controller = HeController(self.m_hmodel)

    def initializeGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_LINE_SMOOTH)
        self.list = glGenLists(1)

    def resizeGL(self, _width, _height):
        self.m_w = _width
        self.m_h = _height

        if (self.m_model is None) or (self.m_model.isEmpty()):
            self.scaleWorldWindow(1.0)

        else:
            self.m_L, self.m_R, self.m_B, self.m_T = self.m_model.getBoundBox()
            self.scaleWorldWindow(1.1)

        glViewport(0, 0, self.m_w, self.m_h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def genRandomPoints(self):
        for i in range(12):
            value = randint(1, 5)
            p0 = Point(randint(-400 * value, 0), randint(0, 400 * value))
            p1 = Point(randint(-400 * value, 0), randint(0, 400 * value))
            segment = Line(p0, p1)
            self.m_controller.insertSegment(segment, 0.01)
            self.update()
            self.repaint()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glCallList(self.list)
        glDeleteLists(self.list, 1)
        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
        pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINE_STRIP)
        glVertex2f(pt0_U.x(), pt0_U.y())
        glVertex2f(pt1_U.x(), pt1_U.y())
        glEnd()

        if self.m_hmodel and not self.m_hmodel.isEmpty():
            patches = self.m_hmodel.getPatches()
            for pat in patches:
                pts = pat.getPoints()
                triangs = Tesselation.tessellate(pts)
                for j in range(len(triangs)):
                    r = random()
                    glColor3f(r, 0.1, 0.3)
                    glBegin(GL_TRIANGLES)
                    glVertex2d(pts[triangs[j][0]].getX(), pts[triangs[j][0]].getY())
                    glVertex2d(pts[triangs[j][1]].getX(), pts[triangs[j][1]].getY())
                    glVertex2d(pts[triangs[j][2]].getX(), pts[triangs[j][2]].getY())
                    glEnd()

            segments = self.m_hmodel.getSegments()
            for seg in segments:
                ptc = seg.getPointsToDraw()
                glColor3f(0.1, 0.1, 0.3)
                glBegin(GL_LINES)
                for i in range(2):
                    glVertex2f(ptc[i].getX(), ptc[i].getY())
                glEnd()

            points = self.m_hmodel.getPoints()
            for point in self.malha:
                glColor3f(3.0, 3.0, 3.0)
                glBegin(GL_POINTS)
                glVertex2f(point.getX(), point.getY())
                glEnd()
        glEndList()

    def setModel(self, _model):
        self.m_model = _model

    def fitWorldToViewport(self):
        if not self.m_model:
            return
        self.m_L, self.m_R, self.m_B, self.m_T = self.m_hmodel.getBoundBox()
        self.scaleWorldWindow(1.10)
        self.update()

    def scaleWorldWindow(self, _scaleFac):
        vpr = self.m_h / self.m_w
        cx = (self.m_L + self.m_R) / 2.0
        cy = (self.m_B + self.m_T) / 2.0
        sizex = (self.m_R - self.m_L) * _scaleFac
        sizey = (self.m_T - self.m_B) * _scaleFac

        if sizey > (vpr * sizex):
            sizex = sizey / vpr

        else:
            sizey = sizex * vpr

        self.m_L = cx - (sizex * 0.5)
        self.m_R = cx + (sizex * 0.5)
        self.m_B = cy - (sizey * 0.5)
        self.m_T = cy + (sizey * 0.5)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)

    def panWorldWindow(self, _panFacX, _panFacY):
        panX = (self.m_R - self.m_L) * _panFacX
        panY = (self.m_T - self.m_B) * _panFacY

        self.m_L += panX
        self.m_R += panX
        self.m_B += panY
        self.m_T += panY

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)

    def showDialog(self):
        if self.m_hmodel.isEmpty():
            return

        default = 1.0
        dialog = InputDialog(title="Definir grade", labels=["Quanto maior o valor, menor a grade"])
        dialog.exec()
        if dialog.result() == 1:
            try:
                default = float(dialog.lineEdits[0].text())
            except:
                default = 1.0
        self._last_mesh_spacing = default

        if not (self.m_hmodel.isEmpty()):
            patches = self.m_hmodel.getPatches()
            for pat in patches:
                pts = pat.getPoints()
                x_min = pts[0].getX()
                x_max = x_min
                y_min = pts[0].getY()
                y_max = y_min
                for i in range(1, len(pts)):
                    if pts[i].getX() < x_min:
                        x_min = pts[i].getX()
                    if pts[i].getX() > x_max:
                        x_max = pts[i].getX()
                    if pts[i].getY() < y_min:
                        y_min = pts[i].getY()
                    if pts[i].getY() > y_max:
                        y_max = pts[i].getY()
                x = []
                y = []
                x_min += default
                y_min += default
                while x_min < x_max:
                    x.append(x_min)
                    x_min += default
                while y_min < y_max:
                    y.append(y_min)
                    y_min += default
                for i in range(len(x)):
                    for j in range(len(y)):
                        if pat.isPointInside(Point(x[i], y[j])):
                            self.malha.append(Point(x[i], y[j]))

        self.update()
        self.repaint()

    def convertPtCoordsToUniverse(self, _pt):
        dX = self.m_R - self.m_L
        dY = self.m_T - self.m_B
        mX = _pt.x() * dX / self.m_w
        mY = (self.m_h - _pt.y()) * dY / self.m_h
        x = self.m_L + mX
        y = self.m_B + mY
        return QtCore.QPointF(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            pos = event.pos()
            self.m_L += pos.x()
            self.m_R -= pos.x()
            self.m_B += pos.y()
            self.m_T -= pos.y()
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
            self.update()
        elif (self.bezier_stage == -1):
            self.m_buttonPressed = True
            self.m_pt0 = event.pos()
        elif (self.bezier_stage == 0 ):
            self.bezier_stage = 1
            self.m_bz0 = event.pos()

        elif (self.bezier_stage == 1 ):
            self.bezier_stage = 2
            self.m_bz1 = event.pos()

        elif (self.bezier_stage == 2 ):
            self.m_bz2 = event.pos()
            self.quadratic_bezier()
            self.bezier_stage = 3

    def mouseMoveEvent(self, event):
        
        if event.button() == Qt.RightButton:
            return

        if self.m_buttonPressed:
            self.m_pt1 = event.pos()
            self.update()
        

    def mouseReleaseEvent(self, event):
        
        if self.bezier_stage != -1 :
            if self.bezier_stage == 3:
                self.bezier_stage = -1
            return

        if event.button() == Qt.RightButton:
            return

        pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
        pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
        # self.m_model.setCurve(pt0_U.x(), pt0_U.y(), pt1_U.x(), pt1_U.y())
        p0 = Point(pt0_U.x(), pt0_U.y())
        p1 = Point(pt1_U.x(), pt1_U.y())
        segment = Line(p0, p1)
        self.m_controller.insertSegment(segment, 0.01)
        self.update()
        self.repaint()
        self.m_buttonPressed = False
        self.m_pt0.setX(0)
        self.m_pt0.setY(0)
        self.m_pt1.setX(0)
        self.m_pt1.setY(0)

    def bezier(self, p0, p1, p2, i):
        X = p1.getX() + (1-i) ** 2 * (p0.getX() - p1.getX()) + i ** 2 * (p2.getX() - p1.getX())
        Y = p1.getY() + (1-i) ** 2 * (p0.getY() - p1.getY()) + i ** 2 * (p2.getY() - p1.getY())
        return Point(X, Y) 

    def quadratic_bezier(self):
        b0_U = self.convertPtCoordsToUniverse(self.m_bz0)
        b1_U = self.convertPtCoordsToUniverse(self.m_bz1)
        b2_U = self.convertPtCoordsToUniverse(self.m_bz2)
        p0 = Point(b0_U.x(), b0_U.y())
        p1 = Point(b1_U.x(), b1_U.y())
        p2 = Point(b2_U.x(), b2_U.y())
        fp = p0
        i=0.05
        while (i < 1.0) :
            bezier = self.bezier(p0,p2,p1,i)
            segment = Line(fp, bezier)
            self.m_controller.insertSegment(segment, 0.01)
            self.update()
            self.repaint()
            fp = bezier
            i += 0.05
        segment = Line(fp, p1)
        self.m_controller.insertSegment(segment, 0.01)
        self.update()
        self.repaint()
        

    def __get_point_index1(self, _coords, _x, _y):
        for i, coord in enumerate(_coords):
            if coord[0] == _x and coord[1] == _y:
                return i + 1
        return 0
    
    def export_to_json(self):
        lower_y = sys.maxsize
        upper_y = -sys.maxsize
        lower_x = sys.maxsize
        upper_x = -sys.maxsize

        _json = []
        for point in self.malha:
            if (point.getY() < lower_y):
                lower_y = point.getY()
            if (point.getY() > upper_y):
                upper_y = point.getY()
            if (point.getX() < lower_x):
                lower_x = point.getX()
            if (point.getX() > upper_x):
                upper_x = point.getX()
            _json.append({"x": point.getX(), "y": point.getY()})

        y_adjust = -1 * lower_y
        x_adjust = -1 * lower_x

        dem_output = {"coords": []}

        for point in _json:
            point["x"] = int(int(point["x"] + x_adjust) / self._last_mesh_spacing)
            point["y"] = int(int(point["y"] + y_adjust) / self._last_mesh_spacing)
            dem_output["coords"].append([point["x"], point["y"]])

        len_x = 1
        len_y = 1
        for point in _json:
            if point["x"] > len_x:
                len_x = point["x"]
            if point["y"] > len_y:
                len_y = point["y"]

        mdf_output =  [[-2.0 for x in range(len_x + 1)] for y in range(len_y + 1)]

        for point in _json:
            mdf_output[point["y"]][point["x"]] = -1.0

        self._temp -= self._var
        len_i = len(mdf_output)
        for i in range(len_i):
            self._temp += self._var
            self._temp = round(self._temp, 2)
            len_j = len(mdf_output[i])
            for j in range(len_j):
                if mdf_output[i][j] == -1.0:
                    if i == 0 or j == 0 or (i + 1) == len_i or (j + 1) == len_j:
                        mdf_output[i][j] = self._temp
                    else:
                        if i > 0 and mdf_output[i - 1][j] == -2.0:
                            mdf_output[i][j] = self._temp
                        if i + 1 < len_i and mdf_output[i + 1][j] == -2.0:
                            mdf_output[i][j] = self._temp
                        if j > 0 and mdf_output[i][j - 1] == -2.0:
                            mdf_output[i][j] = self._temp
                        if j + 1 < len_j and mdf_output[i][j + 1] == -2.0:
                            mdf_output[i][j] = self._temp

        connective =  [[0 for _ in range(5)] for _ in range(len(dem_output["coords"]))]
        len_i = len(mdf_output)
        for i in range(len_i):
            len_j = len(mdf_output[i])
            for j in range(len_j):
                if mdf_output[i][j] != -2.0:
                    actual_point = self.__get_point_index1(dem_output["coords"], j, i)
                    amount_of_connections = 0
                    if i > 0 and mdf_output[i - 1][j] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j, i - 1)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    if i + 1 < len_i and mdf_output[i + 1][j] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j, i + 1)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    if j > 0 and mdf_output[i][j - 1] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j - 1, i)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    if j + 1 < len_j and mdf_output[i][j + 1] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j + 1, i)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    connective[actual_point - 1][0] = amount_of_connections

        force = [[0.0 for _ in range(2)] for _ in range(len(dem_output["coords"]))]
        amount_force = self._punch_particles
        len_i = len(mdf_output)
        for i in range(len_i - 1, 0, -1):
            len_j = len(mdf_output[i])
            for j in range(len_j - 1, 0, -1):
                if mdf_output[i][j] != -2.0:
                    if amount_force > 0:
                        force[self.__get_point_index1(dem_output["coords"], j, i) - 1][0] = self._punch
                        amount_force -= 1
                    else:
                        break
            if amount_force <= 0:
                break

        resistence = [[0 for _ in range(2)] for _ in range(len(dem_output["coords"]))]
        amount_resistence = self._punch_particles
        len_i = len(mdf_output)
        for i in range(len_i):
            len_j = len(mdf_output[i])
            for j in range(len_j):
                if mdf_output[i][j] != -2.0:
                    if amount_resistence > 0:
                        resistence[self.__get_point_index1(dem_output["coords"], j, i) - 1][0] = 1
                        resistence[self.__get_point_index1(dem_output["coords"], j, i) - 1][1] = 1
                        amount_resistence -= 1
                    else:
                        break
            if amount_resistence <= 0:
                break

        dem_output["connective"] = connective
        dem_output["force"] = force
        dem_output["resistence"] = resistence
        dem_output["mass"] = self._mass
        dem_output["density"] = self._density

        with open("dem_input.json", "w") as file:
            json.dump(dem_output, file)

        with open("mdf_input.json", "w") as file:
            json.dump(mdf_output, file)

    def set_up_temp(self):
        dialog = InputDialog(title="Defina o calor", labels=["Defina o calor ao redor do Objeto", "Defina a variação de calor"], dialogs=2)
        dialog.exec()
        if dialog.result() == 1:
            try:
                self._temp = float(dialog.lineEdits[0].text())
                self._var = float(dialog.lineEdits[1].text())
            except:
                self._temp = 100.0
                self._var = 1.2

    def set_up_force(self):
        dialog = InputDialog(
            title="Defina a força",
            labels=[
                "Define a força aplicada",
                "Quantidade de particulas afetadas de inicio",
                "Defina a massa do objeto",
                "Defina a densidade do objeto"
            ],
            dialogs=4
        )
        dialog.exec()
        if dialog.result() == 1:
            try:
                self._punch = float(dialog.lineEdits[0].text())
                self._punch_particles = int(dialog.lineEdits[2].text())
                self._mass = float(dialog.lineEdits[3].text())
                self._density = float(dialog.lineEdits[4].text())
            except:
                self._punch = -1000.0
                self._punch_particles = 10
                self._mass = 7850.0
                self._density = 210000000000.0
                
    def set_up_bezier2(self):
    	self.bezier_stage = 0
