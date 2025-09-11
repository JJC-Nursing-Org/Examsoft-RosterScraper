#!/usr/bin/env python3

# Jefferson A. Cherrington - last update: 09-09-25
# Examsoft Offline Roster Scraper v3.0, originally built for Joliet Junior College's Dept of Nursing
# Desc: converts already downloaded HTML file into CSV file,
# \\    because Examsoft does not currently have a simple export to CSV button.

# future updates: a date / time appender to file export (easy way to timestamp)
#                 a remembrance of where the program last saved and what its name was last (check for overwriting)

# Only needed for access to command line arguments
import os
import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QShowEvent
from PyQt6.QtWidgets import QApplication, QPushButton, QFileDialog, QLabel, QVBoxLayout, \
    QHBoxLayout, QGridLayout, QWidget, QStackedWidget, QStackedLayout, QLineEdit, QTextEdit

from rs_backend_v3 import OfflineRS

basedir = os.path.dirname(__file__)

obj = OfflineRS()

txt_version = "v3.0.00"

txt_updatedate = "09.09.2025"

txt_stuff = "script orig. written by Jefferson Cherrington" + "\n\n" + \
            "creates a CSV roster from a particularly formatted HTML file" + "\n" + \
            "(all scraping is done offline)" + "\n\n" + \
            "last updated: " + txt_updatedate + "\n"

arr_titles = ["Start Screen", "Import File", "Export Folder", "Export Filename", "Preview Output"]

sty_btn_continue = ".QPushButton{"\
                   "background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, " \
                   "stop:0 rgba(0, 0, 0, 20), stop:1 rgba(255, 255, 255, 60));" \
                   "border: 2px solid white; border-radius: 8.5px;" \
                   "padding: 5px;" \
                   "}" \
                   ".QPushButton:hover{" \
                   "background: rgba(0, 165, 180, 70);" \
                   "}"
sty_btn_exit = ".QPushButton{"\
               "background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, "\
               "stop:0 rgba(200, 0, 0, 50), stop:1 rgba(255, 255, 255, 80));"\
               "border: 2px solid white; border-radius: 8.5px;"\
               "padding: 5px;"\
               "}"\
               ".QPushButton:hover{"\
               "background: rgb(171, 7, 27);"\
               "}"
sty_btn_import = ".QPushButton{"\
                 "background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, "\
                 "stop:0 rgba(0, 0, 0, 20), stop:1 rgba(255, 255, 255, 60));"\
                 "border: 2px solid white; border-radius: 8.5px;"\
                 "padding: 5px;"\
                 "}"\
                 ".QPushButton:hover{"\
                 "background: rgba(0, 165, 180, 70);"\
                 "}"
sty_background = ".QWidget {background: qlineargradient(x1:0 y1:1, x2:0.5 y2:0, " \
                 "stop:0 #23002A, stop:1 #00066A);}"\
                 + "* {color: #FFFFFF;}"
sty_txtbox = ".QLineEdit{"\
               "background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, "\
               "stop:0 rgba(100, 100, 100, 60), stop:1 rgba(255, 255, 255, 90));"\
               "color: #FFF; border: 2px solid white; border-radius: 8.5px;"\
               "padding: 5px;"\
               "}"\
               ".QLineEdit:hover{"\
               "background: #B2B3B7; color: #000;}"\
               ".QLineEdit:focus{"\
               "background: #B2B3B7; color: #000;}"

sty_txtbox2 = ".QTextEdit{"\
               "background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, "\
               "stop:0 rgba(100, 100, 100, 60), stop:1 rgba(255, 255, 255, 90));"\
               "color: #FFF; border: 2px solid white; border-radius: 8.5px;"\
               "padding: 5px;"\
               "}"\
               ".QTextEdit:hover{"\
               "background: #B2B3B7; color: #000;}"\
               ".QTextEdit:focus{"\
               "background: #B2B3B7; color: #000;}"

sty_ico_import = (os.path.join(basedir, "assets", "search_icon.png"))


# Subclass QWidget to customize your application's frames
class startscreen_Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        btn_continue = QPushButton("continue ->")
        btn_continue.clicked.connect(self.switch_widget)
        btn_continue.setFont(QFont("Be Vietnam", 14))

        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        lbl_title.setFont(QFont("Be Vietnam [ExtraBold]", 40, 800))
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        lbl_version.setFont(QFont("Be Vietnam", 40))
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel(txt_stuff, self)
        lbl_stuff.setFont(QFont("Be Vietnam", 12))
        lbl_stuff.setStyleSheet("padding: 13px;")

        # this takes the labels for title and version and puts them in a horz. box layout
        layout_title = QHBoxLayout()
        layout_title.addWidget(lbl_title)
        layout_title.addWidget(lbl_version)
        layout_title.setSpacing(0)

        # this takes the horz. box layout and label for "stuff" and puts them in a vert. box layout
        layout_words = QVBoxLayout()
        layout_words.addLayout(layout_title)
        layout_words.addWidget(lbl_stuff)
        layout_words.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_words)

        layout_main.addWidget(btn_continue)

        widget_bkg = QWidget()
        widget_bkg.setStyleSheet(sty_background)
        widget_bkg.setLayout(layout_main)

        layout_fin = QStackedLayout()
        layout_fin.addWidget(widget_bkg)

        self.setLayout(layout_fin)
        self.setMinimumSize(QSize(400, 250))

    def switch_widget(self):
        # for stacked widgets, the first one needs to be max_widgets - 1 to move to the next one
        # (it decrements backwards)

        # this sets up screen 2
        stacked_widget.setCurrentIndex(3)
        stacked_widget.setWindowTitle("RosterScraper: " + arr_titles[1])


class import_loc_Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        btn_continue = QPushButton("continue ->")
        btn_continue.clicked.connect(self.switch_widget)
        btn_continue.setFont(QFont("Be Vietnam", 14))
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_import = QPushButton("")
        btn_import.setIcon(QIcon(sty_ico_import))
        btn_import.setIconSize(QSize(30, 30))
        btn_import.released.connect(self.import_location)
        btn_import.setStyleSheet(sty_btn_import)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        lbl_title.setFont(QFont("Be Vietnam [ExtraBold]", 20, 800))
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        lbl_version.setFont(QFont("Be Vietnam", 20))
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel("import location (HTML):", self)
        lbl_stuff.setFont(QFont("Be Vietnam", 20))
        lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QLineEdit("text goes here.")
        self.txtbox_location.setFont(QFont("Be Vietnam", 14))
        self.txtbox_location.setStyleSheet(sty_txtbox)
        self.txtbox_location.setAlignment(Qt.AlignmentFlag.AlignRight)

        # this takes the labels for title and version and puts them in a horz. box layout
        layout_title = QHBoxLayout()
        layout_title.addWidget(lbl_title)
        layout_title.addWidget(lbl_version)
        layout_title.setSpacing(0)

        # this takes the horz. box layout and label for "stuff" and puts them in a vert. box layout
        layout_words = QVBoxLayout()
        layout_words.addLayout(layout_title)

        layout_words.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout_location = QHBoxLayout()
        layout_location.addWidget(self.txtbox_location)
        layout_location.addWidget(btn_import)

        layout_center = QGridLayout()
        layout_center.addWidget(lbl_stuff, 0, 0)
        layout_center.addLayout(layout_location, 1, 0)
        layout_center.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignTop)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_words)
        layout_main.addLayout(layout_center)
        layout_main.addWidget(btn_continue)

        widget_bkg = QWidget()
        widget_bkg.setStyleSheet(sty_background)

        widget_bkg.setLayout(layout_main)
        layout_fin = QStackedLayout()
        layout_fin.addWidget(widget_bkg)

        self.setLayout(layout_fin)
        self.setMinimumSize(QSize(400, 250))

    def import_location(self):
        home_dir = str(Path.home())
        f_name = QFileDialog.getOpenFileName(self, 'Open File:', home_dir, "HTML files (*.html)")

        if f_name[0]:
            self.txtbox_location.setText(f_name[0])

    def switch_widget(self):

        obj.inp_name = (str(self.txtbox_location.text()))

        # this needs to be screen 3

        stacked_widget.setCurrentIndex(2)
        stacked_widget.setWindowTitle("RosterScraper: " + arr_titles[2])


class exp_tofolder_Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        btn_continue = QPushButton("continue ->")
        btn_continue.clicked.connect(self.switch_widget)
        btn_continue.setFont(QFont("Be Vietnam", 14))
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_import = QPushButton("")
        btn_import.setIcon(QIcon(sty_ico_import))
        btn_import.setIconSize(QSize(30, 30))
        btn_import.released.connect(self.export_location)
        btn_import.setStyleSheet(sty_btn_import)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        lbl_title.setFont(QFont("Be Vietnam [ExtraBold]", 20, 800))
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        lbl_version.setFont(QFont("Be Vietnam", 20))
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel("export folder (CSV):", self)
        lbl_stuff.setFont(QFont("Be Vietnam", 20))
        lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QLineEdit("text goes here.")
        self.txtbox_location.setFont(QFont("Be Vietnam", 14))
        self.txtbox_location.setStyleSheet(sty_txtbox)
        self.txtbox_location.setAlignment(Qt.AlignmentFlag.AlignRight)

        # this takes the labels for title and version and puts them in a horz. box layout
        layout_title = QHBoxLayout()
        layout_title.addWidget(lbl_title)
        layout_title.addWidget(lbl_version)
        layout_title.setSpacing(0)

        # this takes the horz. box layout and label for "stuff" and puts them in a vert. box layout
        layout_words = QVBoxLayout()
        layout_words.addLayout(layout_title)

        layout_words.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout_location = QHBoxLayout()
        layout_location.addWidget(self.txtbox_location)
        layout_location.addWidget(btn_import)

        layout_center = QGridLayout()
        layout_center.addWidget(lbl_stuff, 0, 0)
        layout_center.addLayout(layout_location, 1, 0)
        layout_center.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignTop)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_words)
        layout_main.addLayout(layout_center)
        layout_main.addLayout(layout_location)
        layout_main.addWidget(btn_continue)

        widget_bkg = QWidget()
        widget_bkg.setStyleSheet(sty_background)

        widget_bkg.setLayout(layout_main)
        layout_fin = QStackedLayout()
        layout_fin.addWidget(widget_bkg)

        self.setLayout(layout_fin)
        self.setMinimumSize(QSize(400, 250))

    def export_location(self):
        home_dir = str(Path.home())
        f_name = QFileDialog.getExistingDirectory(self, 'Export to folder:', home_dir)

        if f_name:
            self.txtbox_location.setText(f_name)

    def switch_widget(self):

        obj.exp_folder = (str(self.txtbox_location.text()))

        # this needs to be screen four
        stacked_widget.setCurrentIndex(1)
        stacked_widget.setWindowTitle("RosterScraper: " + arr_titles[3])


class exp_name_Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        btn_continue = QPushButton("continue ->")
        btn_continue.clicked.connect(self.switch_widget)
        btn_continue.setFont(QFont("Be Vietnam", 14))
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        lbl_title.setFont(QFont("Be Vietnam [ExtraBold]", 20, 800))
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        lbl_version.setFont(QFont("Be Vietnam", 20))
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel("name your roster datasets (CSV):", self)
        lbl_stuff.setFont(QFont("Be Vietnam", 20))
        lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QLineEdit("text goes here.")
        self.txtbox_location.setFont(QFont("Be Vietnam", 14))
        self.txtbox_location.setStyleSheet(sty_txtbox)
        self.txtbox_location.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # this takes the labels for title and version and puts them in a horz. box layout
        layout_title = QHBoxLayout()
        layout_title.addWidget(lbl_title)
        layout_title.addWidget(lbl_version)
        layout_title.setSpacing(0)

        # this takes the horz. box layout and label for "stuff" and puts them in a vert. box layout
        layout_words = QVBoxLayout()
        layout_words.addLayout(layout_title)

        layout_words.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout_location = QHBoxLayout()
        layout_location.addWidget(self.txtbox_location)

        layout_center = QGridLayout()
        layout_center.addWidget(lbl_stuff, 0, 0)
        layout_center.addLayout(layout_location, 1, 0)
        layout_center.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignTop)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_words)
        layout_main.addLayout(layout_center)
        layout_main.addLayout(layout_location)
        layout_main.addWidget(btn_continue)

        widget_bkg = QWidget()
        widget_bkg.setStyleSheet(sty_background)

        widget_bkg.setLayout(layout_main)
        layout_fin = QStackedLayout()
        layout_fin.addWidget(widget_bkg)

        self.setLayout(layout_fin)
        self.setMinimumSize(QSize(400, 250))

    def export_location(self):
        home_dir = str(Path.home())
        f_name = QFileDialog.getExistingDirectory(self, 'Export to folder:', home_dir)

        if f_name:
            self.txtbox_location.setText(f_name)

    def switch_widget(self):

        obj.exp_name = (str(self.txtbox_location.text()))
        # this needs to be screen five
        print(obj.inp_name)

        obj.run()

        stacked_widget.setCurrentIndex(0)
        stacked_widget.setWindowTitle("RosterScraper: " + arr_titles[4])


# noinspection SpellCheckingInspection
class preview_results_Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        btn_continue = QPushButton("redo program ⟳")
        btn_continue.clicked.connect(self.switch_widget)
        btn_continue.setFont(QFont("Be Vietnam", 14))
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_exit = QPushButton("exit program")
        btn_exit.released.connect(self.end_game)
        btn_exit.setFont(QFont("Be Vietnam", 14))
        btn_exit.setStyleSheet(sty_btn_exit)
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        lbl_title.setFont(QFont("Be Vietnam [ExtraBold]", 20, 800))
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        lbl_version.setFont(QFont("Be Vietnam", 20))
        lbl_version.setStyleSheet("color: #AAA;")

        self.lbl_stuff = QLabel("X students loaded:", self)
        self.lbl_stuff.setFont(QFont("Be Vietnam", 20))
        self.lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QTextEdit("Entry #X")
        self.txtbox_location.setFont(QFont("Be Vietnam", 14))
        self.txtbox_location.setStyleSheet(sty_txtbox2)

        # this takes the labels for title and version and puts them in a horz. box layout
        layout_title = QHBoxLayout()
        layout_title.addWidget(lbl_title)
        layout_title.addWidget(lbl_version)
        layout_title.setSpacing(0)

        # this takes the horz. box layout and label for "stuff" and puts them in a vert. box layout
        layout_words = QVBoxLayout()
        layout_words.addLayout(layout_title)

        layout_words.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout_location = QHBoxLayout()
        layout_location.addWidget(self.txtbox_location)

        layout_center = QGridLayout()
        layout_center.addWidget(self.lbl_stuff, 0, 0)
        layout_center.addLayout(layout_location, 1, 0)
        layout_center.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignTop)

        layout_btns = QHBoxLayout()
        layout_btns.addWidget(btn_continue)
        layout_btns.addWidget(btn_exit)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_words)
        layout_main.addLayout(layout_center)
        layout_main.addLayout(layout_location)
        layout_main.addLayout(layout_btns)

        widget_bkg = QWidget()
        widget_bkg.setStyleSheet(sty_background)

        widget_bkg.setLayout(layout_main)
        layout_fin = QStackedLayout()
        layout_fin.addWidget(widget_bkg)

        self.setLayout(layout_fin)
        self.setMinimumSize(QSize(400, 250))

    def showEvent(self, a0: QShowEvent) -> None:
        self.txtbox_location.setText(obj.all_stu)
        self.lbl_stuff.setText("{} students loaded:".format(obj.num_stu))

    def export_location(self):
        home_dir = str(Path.home())
        f_name = QFileDialog.getExistingDirectory(self, 'Export to folder:', home_dir)

        if f_name:
            self.txtbox_location.setText(f_name)

    def switch_widget(self):

        # this needs to be screen 2
        stacked_widget.setCurrentIndex(3)
        stacked_widget.setWindowTitle("RosterScraper: " + arr_titles[1])

    def end_game(self):
        sys.exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    fonts_name = [QFontDatabase.addApplicationFont(os.path.join(basedir, "fonts", "BeVietnam-ExtraBold.ttf")),
                  QFontDatabase.addApplicationFont(os.path.join(basedir, "fonts", "BeVietnam-Regular.ttf"))]
    for x in fonts_name:
        if x < 0:
            print("Error")

    # families = QFontDatabase.applicationFontFamilies(fonts_name[2])
    # print(families[0])

    # Create the QStackedWidget and add the two widgets to it
    stacked_widget = QStackedWidget()

    widget0 = preview_results_Widget()
    widget1 = exp_name_Widget()
    widget2 = exp_tofolder_Widget()
    widget3 = import_loc_Widget()
    widget4 = startscreen_Widget()

    stacked_widget.addWidget(widget0)
    stacked_widget.addWidget(widget1)
    stacked_widget.addWidget(widget2)
    stacked_widget.addWidget(widget3)
    stacked_widget.addWidget(widget4)

    # Show the first widget (setCurrentIndex = MAX amt. of widgets, last widget is 0)
    stacked_widget.setCurrentIndex(4)
    stacked_widget.setWindowTitle("RosterScraper: " + arr_titles[0])
    stacked_widget.show()

    # if stacked_widget.currentWidget() == 0:
    #     stacked_widget.setWindowTitle("RosterScraper Start Screen")

    # setCentralWidget(stacked_widget)

    sys.exit(app.exec())
