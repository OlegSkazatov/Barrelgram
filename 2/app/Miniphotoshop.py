import sys
from io import BytesIO

from PIL import Image, ImageFont
from PIL.ImageDraw import ImageDraw
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QSpinBox, QColorDialog, QTableWidgetItem, \
    QAbstractItemView, QInputDialog
from PyQt5.QtCore import Qt
from PyQt5 import uic
# import pywintypes
import win32clipboard
import sqlite3
import datetime
import numpy as np

NONE = -1  # Константы, показывающие выбранный в данный момент инструмент
CROP = 1
PAN = 2
AREA = 3
LEVELS = 4
TEXT = 5
TRANSFORMATION = 6

IMAGEPANNED = "Вырезана область"  # Константы значений колонки type в БД
IMAGECROPPED = "Изображение обрезано"
INSTRUMENTCHANGED = "Изменён инструмент"
TEXTADDED = "Добавлен текст"
IMAGETRANSFORMED = "Изображение трансформировано"
AREASELECTED = "Выделена область"
LEVELSCHANGED = "Изменены цветовые уровни"
IMAGESAVED = "Сохранение"
APPLICATIONLAUNCHED = "Программа запущена"
FILEOPENED = "Открыт файл"
APPLICATIONCLOSED = "Выход из программы"

fontsPath = {  # Словарь с названиями файлов шрифтов
    "Arial": "fonts/arial.ttf",
    "Attractive-Heavy": "Attractive-Heavy.ttf",
    "Bodoni": "Bodoni.ttf",
    "Gagalin": "Gagalin.otf",
    "Mozer-SemiBold": "Mozer-SemiBold.otf",
    "Times New Roman": "Times New Roman.ttf",
    "Uni_Sans": "Uni_Sans.ttf",
    "Comic Sans": "Comic_Sans.ttf"
}


# Класс записи для БД
class Action:
    def __init__(self, datetime, type, info, image=None):
        self.datetime = datetime
        self.type = type
        self.info = info
        self.image = image

    def convertToBinaryData(self, filename):  # Конвертация изображения в байтовый вид
        f = open(filename, 'rb')
        blobData = f.read()
        f.close()
        return blobData

    def sendtoDB(self):  # Добавление записи в БД
        try:
            con = sqlite3.connect('databases/log.db')
        except sqlite3.Error:
            return
        cursor = con.cursor()
        cursor.execute(
            'create table if not exists Actions(ID integer, time datetime, type string, info string, image blob)')
        i = None
        if self.image is not None:
            self.image.save("temp/i.jpg")
            i = self.convertToBinaryData("temp/i.jpg")
        a = cursor.execute("SELECT * FROM Actions").fetchall()
        if len(a) >= 200:
            cursor.execute("DELETE from Actions where id <= {}".format(len(a) - 199))
            cursor.execute("UPDATE Actions SET ID = ID - {}".format(len(a) - 199))
            con.commit()
        a.clear()
        a = cursor.execute("SELECT * FROM Actions").fetchall()
        id1 = len(a) + 1
        a.clear()
        data = [id1, self.datetime, self.type, self.info, i]
        cursor.execute("INSERT INTO Actions VALUES(?, ?, ?, ?, ?)", data)
        con.commit()
        con.close()


# Простой класс, хранящий параметры прямоугольной области
class Area:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def setX(self, x):
        self.x = x

    def setY(self, y):
        self.y = y

    def setWidth(self, w):
        self.width = w

    def setHeight(self, h):
        self.height = h

    def copy(self):
        return Area(self.x, self.y, self.width, self.height)

    def __str__(self):
        return "Area({}, {}, {}, {})".format(self.x, self.y, self.width, self.height)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and \
               self.width == other.width and self.height == other.height


# Далее идут классы окон
# MainWindow - Главное окно
# Workspace - рабочее пространство
# LogWindow - окно просмотра лога
# TransformWindow, LevelsWindow, TextWindow - дополнительные окна инструментов
class LogWindow(QWidget):
    def __init__(self, main):
        super().__init__()
        self.initUI(main)

    def initUI(self, main):
        uic.loadUi('ui/viewLog.ui', self)
        self.main = main
        try:
            self.con = sqlite3.connect('databases/log.db')
        except sqlite3.Error:
            return
        self.cursor = self.con.cursor()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.updateTable()
        self.button_SaveImage.setEnabled(False)
        self.button_ClearLog.clicked.connect(self.clearLog)
        self.button_DeleteLine.clicked.connect(self.deleteLine)
        self.button_GotoLine.clicked.connect(self.setActiveLine)
        self.button_SaveImage.clicked.connect(self.saveImage)
        self.table.cellClicked.connect(self.cellClickEvent)

    def updateTable(self):
        self.table.setRowCount(0)
        data = self.cursor.execute("SELECT * FROM Actions").fetchall()
        self.table.setRowCount(len(data))
        for i in range(len(data)):
            for j in range(1, 4):
                self.table.setItem(i, j - 1, QTableWidgetItem(data[i][j]))
            if "None" in str(data[i][4]):
                self.table.setItem(i, 3, QTableWidgetItem("Отсутствует"))
            else:
                self.table.setItem(i, 3, QTableWidgetItem("Доступно"))
        data.clear()

    def deleteLine(self):
        line = self.table.currentRow() + 1
        self.cursor.execute("DELETE from Actions where ID = {}".format(str(line)))
        self.cursor.execute("UPDATE Actions SET ID = ID - 1 where ID > {}".format(line))
        self.con.commit()
        self.updateTable()

    def setActiveLine(self):
        num, ok = QInputDialog.getInt(self, 'Переход', 'Введите номер записи:')
        if ok:
            self.table.setCurrentCell(num - 1, 0)

    def saveImage(self):
        binaryData = self.cursor.execute("SELECT image from Actions where ID = {}"
                                         .format(self.table.currentRow() + 1)).fetchall()[0][0]
        saveFname = QFileDialog.getSaveFileName(self, 'Сохранение', '',
                                                'Изображение (*.jpg);;Изображение (*.png);;'
                                                ' Изображение (*.bmp)')[0]
        file = open(saveFname, "wb")
        file.write(binaryData)
        file.close()

    def clearLog(self):
        self.cursor.execute("DELETE from Actions")
        self.con.commit()
        self.updateTable()

    def closeEvent(self, event):
        self.main.logWindow = None

    def cellClickEvent(self):
        if self.table.currentColumn() == 3 and self.table.currentItem().text() == "Доступно":
            self.button_SaveImage.setEnabled(True)
        else:
            self.button_SaveImage.setEnabled(False)


class TransformWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.initUI(parent)

    def initUI(self, parent):
        uic.loadUi('ui/transformWindow.ui', self)
        self.parent = parent
        self.label.hide()
        self.label_2.hide()
        self.button_Submit.hide()
        self.input_Width.hide()
        self.input_Height.hide()
        self.button_Area.clicked.connect(self.switchToArea)
        self.button_SizeInput.clicked.connect(self.inputSize)
        self.button_Submit.clicked.connect(self.submit)
        # Скрытие некоторых элементов, привязка собыитй

    def switchToArea(self):
        self.close()
        self.parent.button_InstrumentArea.setEnabled(True)
        self.parent.button_InstrumentArea.click()
        # При нажатии на выделение области в окне транформации происходит переключение на инструмент области

    def inputSize(self):
        self.label.show()
        self.label_2.show()
        self.button_Submit.show()
        self.input_Width.show()
        self.input_Height.show()
        self.input_Width.setValue(self.parent.selectedArea.width + 1)
        self.input_Height.setValue(self.parent.selectedArea.height + 1)
        # Ручной ввод параметров. Нужен если нужны фиксированные пропорции или расширение изображения

    def submit(self):
        w = self.input_Width.value()
        h = self.input_Height.value()
        self.parent.selectedArea.setWidth(w)
        self.parent.selectedArea.setHeight(h)
        self.parent.transform()
        # Подтверждение изменений

    def closeEvent(self, event):
        self.parent.transformWindow = None
        if self.parent.button_InstrumentTransform.isEnabled():
            self.parent.enableInstruments()
        # Событие закрытия окна


class TextWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.initUI(parent)

    def initUI(self, parent):
        uic.loadUi('ui/textWindow.ui', self)
        self.parent = parent
        self.button_TextColorSelect.clicked.connect(self.selectColor)
        self.button_OutlineColorSelect.clicked.connect(self.selectColor)
        self.button_AddText.clicked.connect(self.addText)
        self.button_Done.clicked.connect(self.apply)
        self.input_X.setMaximum(self.parent.image.size[0])
        self.input_Y.setMaximum(self.parent.image.size[1])
        self.textColor = QColor(255, 255, 255)
        self.color_Text.setStyleSheet("background-color: rgb{};".format(str(self.textColor.getRgb())))
        self.outlineColor = QColor(0, 0, 0)  # Показ цвета текста и обводки
        self.color_Outline.setStyleSheet("background-color: rgb{};".format(str(self.outlineColor.getRgb())))
        self.button_Done.setEnabled(False)

    def selectColor(self):
        color = QColorDialog.getColor()
        if self.sender() is self.button_TextColorSelect:
            self.textColor = color
            self.color_Text.setStyleSheet("background-color: rgb{};".format(str(self.textColor.getRgb())))
        elif self.sender() is self.button_OutlineColorSelect:
            self.outlineColor = color
            self.color_Outline.setStyleSheet("background-color: rgb{};".format(str(self.outlineColor.getRgb())))
        # Обновление цвета и его отображения

    def addText(self):
        self.parent.addText(self.input_Text.text(), "fonts/" + fontsPath[self.input_Font.currentText()],
                            color=self.textColor.getRgb(), size=self.input_TextSize.value(), x=self.input_X.value(),
                            y=self.input_Y.value(), bold_size=self.input_OutlineSize.value(),
                            bold_color=self.outlineColor.getRgb())
        self.button_Done.setEnabled(True)
        # Непосредственное добавление текста

    def apply(self):
        self.parent.backupImage = self.parent.image.copy()
        self.parent.updateImage()
        self.close()
        info = "Текст: '{}'\nШрифт: {}\nРазмер шрифта: {}\nЦвет: {}\nРазмер обводки: {}\nЦвет обводки: {}".format \
            (self.input_Text.text(), self.input_Font.currentText(), str(self.input_TextSize.value()),
             str(self.textColor.getRgb()), str(self.input_OutlineSize.value()), str(self.outlineColor.getRgb()))
        self.parent.autosave()
        a = Action(datetime.datetime.now(), TEXTADDED, info, self.parent.image.copy())
        a.sendtoDB()
        # Подтверждение изменений

    def closeEvent(self, event):
        self.parent.textWindow = None
        self.parent.enableInstruments()
        # Событие закрытия окна


class LevelsWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.initUI(parent)

    def initUI(self, parent):
        uic.loadUi('ui/levelsWindow.ui', self)
        self.parent = parent
        valueChangedConnect = [self.value_R, self.value_G, self.value_B, self.slider_R, self.slider_G, self.slider_B]
        for el in valueChangedConnect:
            el.valueChanged.connect(self.valueChange)
            if el.__class__ is QSpinBox:
                el.valueChanged.connect(self.apply)
        self.button_Apply.clicked.connect(self.apply)
        # Привязка событий

    def valueChange(self):
        if self.sender() is self.value_R:
            self.slider_R.setValue(self.value_R.value())
        elif self.sender() is self.value_G:
            self.slider_G.setValue(self.value_G.value())
        elif self.sender() is self.value_B:
            self.slider_B.setValue(self.value_B.value())
        elif self.sender() is self.slider_R:
            self.value_R.setValue(self.slider_R.value())
        elif self.sender() is self.slider_G:
            self.value_G.setValue(self.slider_G.value())
        elif self.sender() is self.slider_B:
            self.value_B.setValue(self.slider_B.value())
        # Обработка событий изменения значений, для синхронизации числового значения и ползунка

    def apply(self):
        r, g, b = self.value_R.value(), self.value_G.value(), self.value_B.value()
        final = self.sender() is self.button_Apply
        self.parent.setLevels(r, g, b, final=final)
        # Подтверждение изменений

    def closeEvent(self, event):
        self.parent.levelsWindow = None
        self.parent.enableInstruments()
        self.parent.setLevels(0, 0, 0, final=False)
        # Событие закрытия окна


class WorkSpace(QWidget):
    def __init__(self, fname, main):
        super().__init__()
        self.initUI(fname, main)

    def initUI(self, fname, main):
        uic.loadUi('ui/workspace.ui', self)
        self.fname = fname  # Путь к файлу
        self.main = main  # Передача экземпляра класса главного окна для получения его методов и аттрибутов
        self.saveFname = ""  # Путь сохранения файлов
        self.setWindowTitle(self.fname.split("/")[-1])
        self.image = Image.open(fname)  # Картинка
        self.displayImage = self.image.copy()  # Отображаемая картинка
        self.i = ImageQt(self.image.copy())
        self.pixmap = QPixmap.fromImage(self.i)
        self.x = self.image.size[0]
        self.y = self.image.size[1]
        self.x_default = self.pixmap.size().width()
        self.y_default = self.pixmap.size().height()
        if self.x > 1420 or self.y > 760:  # Если изображение не влезает в окно, то оно сжимается
            kx = self.x / 1420
            ky = self.y / 760
            k = max([kx, ky])
            self.image = self.image.resize((int(self.x / k), int(self.y / k)))
            self.displayImage = self.displayImage.resize((int(self.x / k), int(self.y / k)))
            self.x = int(self.x / k)
            self.y = int(self.y / k)
            self.i = ImageQt(self.image.copy())
            self.pixmap = QPixmap.fromImage(self.i)
        self.imageLabel.resize(self.x, self.y)
        self.fullImageArea = Area(0, 0, self.x - 1, self.y - 1)  # Значение полных размеров изображения
        self.selectedArea = Area(0, 0, self.x - 1, self.y - 1)  # Значение выделенной области
        self.backupImage = self.image.copy()
        self.imageLabel.setPixmap(self.pixmap)  # Отображение
        self.instrument = NONE
        self.imageList = [self.image.copy()]
        self.imageListId = 0
        for button in self.instruments.buttons():
            button.clicked.connect(self.instrumentSelect)
        self.button_InstrumentCrop.clicked.connect(self.crop)
        self.button_InstrumentPan.clicked.connect(self.pan)
        self.button_InstrumentArea.clicked.connect(self.area)
        self.button_InstrumentLevels.clicked.connect(self.levels)
        self.button_InstrumentText.clicked.connect(self.text)
        self.button_InstrumentTransform.clicked.connect(self.transform)
        self.button_CancelAreaSelection.clicked.connect(self.deselectArea)
        self.button_AreaDone.clicked.connect(self.selectArea)
        self.button_TransformDone.clicked.connect(self.transformDone)
        self.button_CancelTransform.clicked.connect(self.cancelTransform)
        self.button_Save.clicked.connect(self.save)
        self.button_SaveAs.clicked.connect(self.saveAs)
        self.button_Back.clicked.connect(self.back)
        self.button_Forward.clicked.connect(self.forward)
        self.button_AreaDone.hide()
        self.button_CancelAreaSelection.hide()
        self.button_TransformDone.hide()
        self.button_CancelTransform.hide()
        self.button_Back.setEnabled(False)
        self.button_Forward.setEnabled(False)
        self.leftMouseButtonPressed = False  # Для более удобного получения состояния ЛКМ
        self.transformWindow = None  # Переменные для вспомогательных окон. Пока окна не открыты, равны None
        self.textWindow = None
        self.levelsWindow = None

    def instrumentSelect(self):
        # Изменение аттрибута instrument
        ins = "none"
        if self.sender() is self.button_InstrumentCrop:
            self.instrument = CROP
            ins = "Обрезка"
        elif self.sender() is self.button_InstrumentPan:
            self.instrument = PAN
            ins = "Вырезка"
        elif self.sender() is self.button_InstrumentArea:
            self.instrument = AREA
            ins = "Выделение области"
            self.button_AreaDone.setEnabled(True)
        elif self.sender() is self.button_InstrumentLevels:
            self.instrument = LEVELS
            ins = "Уровни"
        elif self.sender() is self.button_InstrumentText:
            self.instrument = TEXT
            ins = "Добавление текста"
        elif self.sender() is self.button_InstrumentTransform:
            self.instrument = TRANSFORMATION
            ins = "Трансформация"
        self.disableInactiveInstruments(self.sender())  # Предотвращение пользователя от нажатия
        # на другие инструменты, во время работы с одним инструментом
        a = Action(datetime.datetime.now(), INSTRUMENTCHANGED, "Инструмент: " + ins, image=None)
        a.sendtoDB()

    def crop(self):  # Метод обрезки
        if self.fullImageArea == self.selectedArea:
            self.errorLabel.setText("Область не была выделена или было выделено всё изображение")
            self.enableInstruments()
            return
        x = self.selectedArea.x
        y = self.selectedArea.y
        w = self.selectedArea.width
        h = self.selectedArea.height
        self.image = self.image.crop((x, y, x + w, y + h))
        x1, y1 = self.image.size
        self.imageLabel.resize(x1, y1)
        a = Action(datetime.datetime.now(), IMAGECROPPED, str(self.selectedArea), image=self.image.copy())
        a.sendtoDB()
        self.selectedArea.setX(0)
        self.selectedArea.setY(0)
        self.selectedArea.setWidth(x1 - 1)
        self.selectedArea.setHeight(y1 - 1)
        self.fullImageArea = self.selectedArea.copy()
        self.backupImage = self.image.copy()
        self.deselectArea()
        self.removeGap()
        self.instrument = NONE
        self.autosave()

    def pan(self):  # Метод вырезания. Добавляет вырезанную область в буфер обмена
        self.removeGap()
        self.enableInstruments()
        output = BytesIO()
        x = self.selectedArea.x
        y = self.selectedArea.y
        w = self.selectedArea.width
        h = self.selectedArea.height
        im = self.image.crop((x, y, x + w, y + h))
        im.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        self.send_to_clipboard(win32clipboard.CF_DIB, data)
        a = Action(datetime.datetime.now(), IMAGEPANNED,
                   str(self.selectedArea), image=self.image.copy().crop((x, y, w, h)))
        a.sendtoDB()
        self.deselectArea()
        self.removeGap()
        self.instrument = NONE

    def area(self):  # Переключение на выделение области
        self.createGap()
        self.updateImage()
        self.setMouseTracking(True)
        self.imageLabel.setMouseTracking(True)
        self.button_AreaDone.show()
        self.button_CancelAreaSelection.show()

    def levels(self):  # Переключение на изменение цветовых параметров. Открытие вспомогательного окна.
        if self.levelsWindow is not None:
            return
        self.levelsWindow = LevelsWindow(self)
        self.main.windows.append(self.levelsWindow)
        self.levelsWindow.show()

    def text(self):  # Переключение на добавление текста. Открытие вспомогательного окна.
        if self.textWindow is not None:
            return
        self.textWindow = TextWindow(self)
        self.main.windows.append(self.textWindow)
        self.textWindow.show()

    def addText(self, text, font, size=16, color=(0, 0, 0), x=0, y=0, bold_size=0, bold_color=(0, 0, 0)):
        # Метод добавления текста
        self.image = self.backupImage.copy()  # Удаление предыдущего варианта расположения данного текста
        draw = ImageDraw(self.image)
        font = ImageFont.truetype(font, size)
        if bold_size != 0:  # Добавление обводки. В PIL нету такого метода, так что всё вручную.
            for adj in range(bold_size):
                draw.text((x - adj, y), text, font=font, fill=bold_color)
                draw.text((x + adj, y), text, font=font, fill=bold_color)
                draw.text((x, y + adj), text, font=font, fill=bold_color)
                draw.text((x, y - adj), text, font=font, fill=bold_color)
                draw.text((x - adj, y + adj), text, font=font, fill=bold_color)
                draw.text((x + adj, y + adj), text, font=font, fill=bold_color)
                draw.text((x - adj, y - adj), text, font=font, fill=bold_color)
                draw.text((x + adj, y - adj), text, font=font, fill=bold_color)
        draw.text((x, y), text, color, font=font)
        self.displayImage = self.image.copy()
        self.updateImage()

    def transform(self):  # Переключение на изменение пропорций.
        # Открытие вспомогательного окна, если область не выделена
        if self.fullImageArea == self.selectedArea:
            if self.transformWindow is not None:
                return
            self.transformWindow = TransformWindow(self)
            self.removeGap()
            self.main.windows.append(self.transformWindow)
            self.transformWindow.show()
            return
        w = self.selectedArea.width
        h = self.selectedArea.height
        self.image = self.image.resize((w, h))
        self.imageLabel.resize(w, h)
        self.selectedArea.setX(0)
        self.selectedArea.setY(0)
        self.selectedArea.setWidth(self.selectedArea.width - 1)
        self.selectedArea.setHeight(self.selectedArea.height - 1)
        self.button_AreaDone.hide()
        self.button_TransformDone.show()
        self.button_CancelAreaSelection.hide()
        self.button_CancelTransform.show()
        self.button_InstrumentTransform.setEnabled(False)
        self.removeGap()

    def updateImage(self):  # Обновление отображаемой картинки после изменений
        self.imageLabel.resize(self.displayImage.size[0], self.displayImage.size[1])
        self.i = ImageQt(self.displayImage.copy())
        self.pixmap = QPixmap.fromImage(self.i)
        self.imageLabel.setPixmap(self.pixmap)

    def autosave(self):  # Добавление изображения в список для дальнейшей отмены изменений
        self.imageList = self.imageList[:self.imageListId] + self.imageList[self.imageListId + 1:] \
                         + [self.imageList[self.imageListId]]
        self.imageList.append(self.backupImage.copy())
        while len(self.imageList) > 20:
            self.imageList.__delitem__(0)
        self.imageListId = len(self.imageList) - 1
        self.button_Forward.setEnabled(False)
        if self.imageListId != 0:
            self.button_Back.setEnabled(True)

    def back(self):
        self.button_Forward.setEnabled(True)
        self.imageListId -= 1
        if self.imageListId == 0:
            self.button_Back.setEnabled(False)
        self.image = self.imageList[self.imageListId].copy()
        self.backupImage = self.image.copy()
        self.removeGap()
        self.updateImage()
        self.selectedArea = Area(0, 0, self.displayImage.size[0] - 1, self.displayImage.size[1] - 1)
        self.fullImageArea = self.selectedArea.copy()

    def forward(self):
        self.button_Back.setEnabled(True)
        self.imageListId += 1
        if self.imageListId == len(self.imageList) - 1:
            self.button_Forward.setEnabled(False)
        self.image = self.imageList[self.imageListId].copy()
        self.backupImage = self.image.copy()
        self.removeGap()
        self.updateImage()
        self.selectedArea = Area(0, 0, self.displayImage.size[0] - 1, self.displayImage.size[1] - 1)
        self.fullImageArea = self.selectedArea.copy()

    def createGap(self, rect=True):  # Создание видимых границ вокруг выделенной области
        x = self.selectedArea.x
        y = self.selectedArea.y
        w = self.selectedArea.width
        h = self.selectedArea.height
        drawer = ImageDraw(self.displayImage)
        drawer.line((x, y, x + w, y), fill=(120, 0, 0), width=1)
        drawer.line((x, y, x, y + h), fill=(120, 0, 0), width=1)
        drawer.line((x, y + h, x + w, y + h), fill=(120, 0, 0), width=1)
        drawer.line((x + w, y, x + w, y + h), fill=(120, 0, 0), width=1)
        if not rect:
            return
        if w % 2 == 0:
            drawer.rectangle([x + w // 2 - 5, y, x + w // 2 + 4, y + 3], fill=(0, 0, 0), outline=(0, 120, 0))
            drawer.rectangle([x + w // 2 - 5, y + h - 1, x + w // 2 + 4, y + h - 4], fill=(0, 0, 0),
                             outline=(0, 120, 0))
        else:
            drawer.rectangle([x + w // 2 - 4, y, x + w // 2 + 4, y + 3], fill=(0, 0, 0), outline=(0, 120, 0))
            drawer.rectangle([x + w // 2 - 4, y + h - 1, x + w // 2 + 4, y + h - 4], fill=(0, 0, 0),
                             outline=(0, 120, 0))
        if h % 2 == 0:
            drawer.rectangle([x, y + h // 2 - 5, x + 3, y + h // 2 + 4], fill=(0, 0, 0), outline=(0, 120, 0))
            drawer.rectangle([x + w - 1, y + h // 2 - 5, x + w - 5, y + h // 2 + 4], fill=(0, 0, 0),
                             outline=(0, 120, 0))
        else:
            drawer.rectangle([x, y + h // 2 - 4, x + 4, y + h // 2 + 4], fill=(0, 0, 0), outline=(0, 120, 0))
            drawer.rectangle([x + w - 1, y + h // 2 - 4, x + w - 5, y + h // 2 + 4], fill=(0, 0, 0),
                             outline=(0, 120, 0))

    def removeGap(self):  # Отключение границ выделенной области
        self.displayImage = self.image.copy()
        self.updateImage()

    def selectArea(self):  # Подтверждение выделения области
        self.removeGap()
        self.createGap(rect=False)
        self.updateImage()
        self.instrument = NONE
        self.button_AreaDone.setEnabled(False)
        self.enableInstruments()
        a = Action(datetime.datetime.now(), AREASELECTED, str(self.selectedArea), image=None)
        a.sendtoDB()

    def deselectArea(self):  # Отмена выделения области
        self.selectedArea = self.fullImageArea.copy()
        self.removeGap()
        self.updateImage()
        self.instrument = NONE
        self.button_AreaDone.hide()
        self.button_CancelAreaSelection.hide()
        self.enableInstruments()

    def send_to_clipboard(self, clip_type, data):  # Добавление изображения в буфер обмена
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(clip_type, data)
        win32clipboard.CloseClipboard()

    def disableInactiveInstruments(self, active):  # Отключение кнопок неактивных инструментов
        for button in self.instruments.buttons():
            if button is active:
                continue
            button.setEnabled(False)

    def transformDone(self):  # Подтверждение изменения пропорций
        self.fullImageArea = self.selectedArea.copy()
        self.enableInstruments()
        self.button_CancelTransform.hide()
        self.button_TransformDone.hide()
        self.backupImage = self.image.copy()
        self.autosave()
        self.instrument = NONE
        self.x_default = self.pixmap.size().width()
        self.y_default = self.pixmap.size().height()
        if self.transformWindow is None:
            return
        self.transformWindow.close()
        self.transformWindow = None
        a = Action(datetime.datetime.now(), IMAGETRANSFORMED, str(self.selectedArea), image=self.image.copy())
        a.sendtoDB()

    def cancelTransform(self):  # Отмена изменения пропорций
        self.image = self.backupImage.copy()
        self.imageLabel.resize(self.backupImage.size[0], self.backupImage.size[1])
        self.removeGap()
        self.selectedArea = self.fullImageArea.copy()
        self.enableInstruments()
        self.button_CancelTransform.hide()
        self.button_TransformDone.hide()
        self.instrument = NONE

    def enableInstruments(self):  # Включение кнопок всех инструментов
        for button in self.instruments.buttons():
            button.setEnabled(True)

    def setLevels(self, r, g, b, final=False):  # Изменение яркости RGB каналов.
        narray = np.array(self.backupImage.copy(), dtype=np.int16)
        x = self.selectedArea.x
        y = self.selectedArea.y
        w = self.selectedArea.width
        h = self.selectedArea.height
        narray[y:y + h, x:x + w + 1, 0] += r
        narray[y:y + h, x:x + w + 1, 1] += g
        narray[y:y + h, x:x + w + 1, 2] += b
        narray[narray > 255] = 255
        narray[narray < 0] = 0
        self.image = Image.fromarray(np.uint8(narray))
        self.removeGap()
        self.createGap(rect=False)
        self.updateImage()
        if final:
            self.backupImage = self.image.copy()
            self.levelsWindow.close()
            self.levelsWindow = None
            self.enableInstruments()
            self.autosave()
            info = str(self.selectedArea) + "R: {}\nG: {}\nB: {}".format(str(r), str(g), str(b))
            a = Action(datetime.datetime.now(), LEVELSCHANGED, info, image=self.image.copy())
            a.sendtoDB()

    def save(self):  # Сохранение в выбранный путь. Если путь не выбран, вызывается метод его выбора
        if self.saveFname == "":
            self.saveAs()
            return
        self.image.save(self.saveFname)
        a = Action(datetime.datetime.now(), IMAGESAVED, "Путь: " + self.saveFname, image=self.image.copy())
        a.sendtoDB()

    def saveAs(self):  # Выбор пути для сохранения
        fname = QFileDialog.getSaveFileName(self, 'Сохранение', '',
                                            'Изображение (*.jpg);;Изображение (*.png);;'
                                            ' Изображение (*.bmp)')[0]
        try:
            self.image.save(fname)
            self.saveFname = fname
        except ValueError:  # Если пользователь не выбрал путь
            return
        a = Action(datetime.datetime.now(), IMAGESAVED, "Путь: " + self.saveFname, image=self.image.copy())
        a.sendtoDB()

    def mouseMoveEvent(self, event):  # Изменение курсора при приближнии к границам выделенной области,
        # если выбран инструмент выбора области
        if self.instrument == AREA:
            x = self.selectedArea.x + 180
            y = self.selectedArea.y + 140
            w = self.selectedArea.width
            h = self.selectedArea.height
            if (abs(x - event.x()) <= 10 and event.y() in range(y, y + h)) or \
                    (abs(x + w - event.x()) <= 10 and event.y() in range(y, y + h)):
                QApplication.setOverrideCursor(Qt.SplitHCursor)
                self.moveBorder(event)
            elif (abs(y - event.y()) <= 10 and event.x() in range(x, x + w)) or \
                    (abs(y + h - event.y()) <= 10 and event.x() in range(x, x + w)):
                QApplication.setOverrideCursor(Qt.SplitVCursor)
                self.moveBorder(event)
            else:
                QApplication.setOverrideCursor(Qt.ArrowCursor)

    def moveBorder(self, event):  # Движение границ выделенной области
        if not self.leftMouseButtonPressed:
            return
        x = self.selectedArea.x + 180
        y = self.selectedArea.y + 140
        w = self.selectedArea.width
        h = self.selectedArea.height
        if (abs(x - event.x()) <= 10 and event.y() in range(y, y + h)) and 180 <= event.x() <= x + w:
            self.selectedArea.setX(self.selectedArea.x + event.x() - x)
            self.selectedArea.setWidth(self.selectedArea.width - event.x() + x)
            self.removeGap()
            self.createGap()
            self.updateImage()
            return
        if (abs(x + w - event.x()) <= 10 and event.y() in range(y, y + h)) and x <= event.x() <= 180 \
                + self.fullImageArea.width:
            self.selectedArea.setWidth(self.selectedArea.width + event.x() - x - w)
            self.removeGap()
            self.createGap()
            self.updateImage()
            return
        if (abs(y - event.y()) <= 10 and event.x() in range(x, x + w)) and 140 <= event.y() <= y + h:
            self.selectedArea.setY(self.selectedArea.y + event.y() - y)
            self.selectedArea.setHeight(self.selectedArea.height - event.y() + y)
            self.removeGap()
            self.createGap()
            self.updateImage()
            return
        if (abs(y + h - event.y()) <= 10 and event.x() in range(x, x + w)) and y <= event.y() <= 140 \
                + self.fullImageArea.height:
            self.selectedArea.setHeight(self.selectedArea.height + event.y() - y - h)
            self.removeGap()
            self.createGap()
            self.updateImage()
            return

    def mousePressEvent(self, event):  # Изменение параметра leftMouseButtonPressed на True
        if event.button() == Qt.LeftButton:
            self.leftMouseButtonPressed = True
            self.errorLabel.setText("")

    def mouseReleaseEvent(self, event):  # Изменение параметра leftMouseButtonPressed на False
        if event.button() == Qt.LeftButton:
            self.leftMouseButtonPressed = False

    def keyPressEvent(self, event):  # Реализация Ctrl + Z
        if int(event.modifiers()) == Qt.CTRL:
            if event.key() == Qt.Key_Z:
                if self.button_Back.isEnabled():
                    self.back()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi('ui/mainWindow.ui', self)
        self.windows = [self]  # Список всех активных окон приложения
        self.button_Exit.clicked.connect(self.exit)
        self.button_Open.clicked.connect(self.openFile)
        self.button_ViewLog.clicked.connect(self.viewLog)
        self.logWindow = None
        a = Action(datetime.datetime.now(), APPLICATIONLAUNCHED, "", image=None)
        a.sendtoDB()

    def openFile(self):  # Открытие файлов
        fname = QFileDialog.getOpenFileName(self, 'Выбрать изображение', '',
                                            'Изображение (*.jpg);;Изображение (*.png);;'
                                            ' Изображение (*.bmp);;Все файлы (*)')[0]
        try:
            Image.open(fname)
        except AttributeError:  # Убирает AttributeError если пользователь не выбрал файл
            return
        wspace = WorkSpace(fname, self)
        wspace.show()
        self.windows.append(wspace)
        a = Action(datetime.datetime.now(), FILEOPENED, "Путь: " + fname, image=Image.open(fname))
        a.sendtoDB()

    def viewLog(self):
        if self.logWindow is not None:
            return
        try:
            con = sqlite3.connect('databases/log.db')
        except sqlite3.Error:
            return
        cursor = con.cursor()
        cursor.execute(
            'create table if not exists Actions(ID integer, time datetime, type string, info string, image blob)')
        self.logWindow = LogWindow(self)
        self.windows.append(self.logWindow)
        self.logWindow.show()

    def exit(self):  # Закрытие всех окон и выход из приложения
        for el in self.windows:
            el.close()
        a = Action(datetime.datetime.now(), APPLICATIONCLOSED, "", image=None)
        a.sendtoDB()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()  # Создаём и отображаем главное окно
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
