from PyQt4 import QtGui, QtCore
from diagramscene import DiagramItem, DiagramTextItem
from FsmState import FsmState
from FsmTransition import FsmTransition

class FsmScene(QtGui.QGraphicsScene):
    InsertState, InsertLine, InsertText, MoveItem  = range(4)

    itemInserted = QtCore.pyqtSignal(DiagramItem)

    textInserted = QtCore.pyqtSignal(QtGui.QGraphicsTextItem)

    itemSelected = QtCore.pyqtSignal(QtGui.QGraphicsItem)
    
    mouseMoved = QtCore.pyqtSignal(QtCore.QPointF)

    def __init__(self, itemMenu, parent=None):
        super(FsmScene, self).__init__(parent)

        self.gridSize = 50
        self.stateCreatedIdx = 0
        self.myItemMenu = itemMenu
        self.myMode = self.MoveItem
        self.myItemType = DiagramItem.Step
        self.line = None
        self.textItem = None
        self.myItemColor = QtCore.Qt.white
        self.myTextColor = QtCore.Qt.black
        self.myLineColor = QtCore.Qt.black
        self.myFont = QtGui.QFont()

    # Efficiently draws a grid in the background.
    # For more information: http://www.qtcentre.org/threads/5609-Drawing-grids-efficiently-in-QGraphicsScene?p=28905#post28905
    def drawBackground(self, painter, rect):
        left = int(rect.left()) - (int(rect.left()) % self.gridSize)
        right = int(rect.right())
        top = int(rect.top()) - (int(rect.top()) % self.gridSize)
        bottom = int(rect.bottom())

        
        lines = [];
        
        for x in range(left, right, self.gridSize):
            lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()));
        for y in range(top, bottom, self.gridSize):
            lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y));
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.setPen(QtGui.QPen(QtCore.Qt.gray, 0))
        painter.drawLines(lines);

    def setLineColor(self, color):
        self.myLineColor = color
        if self.isItemChange(FsmTransition):
            item = self.selectedItems()[0]
            item.setColor(self.myLineColor)
            self.update()

    def setTextColor(self, color):
        self.myTextColor = color
        if self.isItemChange(DiagramTextItem):
            item = self.selectedItems()[0]
            item.setDefaultTextColor(self.myTextColor)

    def setItemColor(self, color):
        self.myItemColor = color
        if self.isItemChange(DiagramItem):
            item = self.selectedItems()[0]
            item.setBrush(self.myItemColor)

    def setFont(self, font):
        self.myFont = font
        if self.isItemChange(DiagramTextItem):
            item = self.selectedItems()[0]
            item.setFont(self.myFont)

    def setMode(self, mode):
        self.myMode = mode

    def setItemType(self, type):
        self.myItemType = type

    def editorLostFocus(self, item):
        cursor = item.textCursor()
        cursor.clearSelection()
        item.setTextCursor(cursor)

        if item.toPlainText():
            self.removeItem(item)
            item.deleteLater()

    def mousePressEvent(self, mouseEvent):
        pos = mouseEvent.scenePos().toPoint() / self.gridSize * self.gridSize
        if (mouseEvent.button() != QtCore.Qt.LeftButton):
            return

        if self.myMode == self.InsertState:
            item = FsmState(self.myItemMenu, 'S{}'.format(self.stateCreatedIdx))
            self.stateCreatedIdx += 1
            #item.setBrush(self.myItemColor)
            self.addItem(item)
            item.setPos(pos)
            #self.itemInserted.emit(item)
        # elif self.myMode == self.InsertItem:
        #     item = DiagramItem(self.myItemType, self.myItemMenu)
        #     item.setBrush(self.myItemColor)
        #     self.addItem(item)
        #     item.setPos(mouseEvent.scenePos())
        #     self.itemInserted.emit(item)
        elif self.myMode == self.InsertLine:
            self.line = QtGui.QGraphicsLineItem(QtCore.QLineF(mouseEvent.scenePos(),
                                        mouseEvent.scenePos()))
            self.line.setPen(QtGui.QPen(self.myLineColor, 2))
            self.addItem(self.line)
        elif self.myMode == self.InsertText:
            textItem = DiagramTextItem()
            textItem.setFont(self.myFont)
            textItem.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            textItem.setZValue(1000.0)
            textItem.lostFocus.connect(self.editorLostFocus)
            textItem.selectedChange.connect(self.itemSelected)
            self.addItem(textItem)
            textItem.setDefaultTextColor(self.myTextColor)
            textItem.setPos(pos)
            self.textInserted.emit(textItem)

        super(FsmScene, self).mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        self.mouseMoved.emit(mouseEvent.scenePos())
        if self.myMode == self.InsertLine and self.line:
            newLine = QtCore.QLineF(self.line.line().p1(), mouseEvent.scenePos())
            self.line.setLine(newLine)
        else: #if self.myMode == self.MoveItem:
            super(FsmScene, self).mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        if self.line and self.myMode == self.InsertLine:
            startItems = self.items(self.line.line().p1())
            if len(startItems) and startItems[0] == self.line:
                startItems.pop(0)
            endItems = self.items(self.line.line().p2())
            if len(endItems) and endItems[0] == self.line:
                endItems.pop(0)

            self.removeItem(self.line)
            self.line = None

            if len(startItems) and len(endItems) and \
                    isinstance(startItems[0], FsmState) and \
                    isinstance(endItems[0], FsmState) and \
                    startItems[0] != endItems[0]:
                startItem = startItems[0]
                endItem = endItems[0]
                arrow = FsmTransition(startItem, endItem)
                arrow.setColor(self.myLineColor)
                startItem.addArrow(arrow)
                endItem.addArrow(arrow)
                arrow.setZValue(-1000.0)
                self.addItem(arrow)
                arrow.updatePosition()

        self.line = None
        
        super(FsmScene, self).mouseReleaseEvent(mouseEvent)
        #we should realign all selected States to grid
        #if self.myMode == self.MoveItem:
        for el in self.selectedItems():
            if isinstance(el, FsmState):
                pos = el.scenePos().toPoint() / self.gridSize * self.gridSize
                el.setPos(pos)
        
    def isItemChange(self, type):
        for item in self.selectedItems():
            if isinstance(item, type):
                return True
        return False


if __name__ == '__main__':
    import sys
    from MainWindow import MainWindow
    from PyQt4.QtTest import QTest
    from PyQt4.QtCore import Qt
    
    app = QtGui.QApplication(sys.argv)


    mainWindow = MainWindow()
    mainWindow.setGeometry(100, 100, 800, 500)
    mainWindow.show()

    QTest.mouseClick(mainWindow.addStateButton, Qt.LeftButton)
    QTest.mouseClick(mainWindow.view.viewport(), Qt.LeftButton, Qt.NoModifier, QtCore.QPoint(400,200))
    QTest.mouseClick(mainWindow.view.viewport(), Qt.LeftButton, Qt.NoModifier, QtCore.QPoint(100,250))
    QTest.mouseClick(mainWindow.linePointerButton, Qt.LeftButton)
    QTest.mousePress(mainWindow.view.viewport(), Qt.LeftButton, Qt.NoModifier, QtCore.QPoint(400,200))
    QTest.mouseMove(mainWindow.view.viewport(), QtCore.QPoint(100,250))
    QTest.mouseRelease(mainWindow.view.viewport(), Qt.LeftButton, Qt.NoModifier, QtCore.QPoint(100,250))
        
    sys.exit(app.exec_()) 





