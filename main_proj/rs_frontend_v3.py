#!/usr/bin/env python3
import time

# Jefferson A. Cherrington - last update: 09-10-25
# Examsoft Offline Roster Scraper v3.0, originally built for Joliet Junior College's Dept of Nursing
# Desc: converts already downloaded HTML file into CSV file,
# \\    because Examsoft does not currently have a simple export to CSV button.

# future updates: a remembrance of where the program last saved and what its name was last (check for overwriting)

# Only needed for access to command line arguments
import os
import sys
from pathlib import Path
import datetime

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QShowEvent
from PyQt6.QtWidgets import QApplication, QPushButton, QFileDialog, QLabel, QVBoxLayout, \
    QProgressBar, QCheckBox, \
    QHBoxLayout, QGridLayout, QWidget, QStackedWidget, QStackedLayout, QLineEdit, QTextEdit

from main_proj.backend.rs_orchestrator import OfflineRS


def load_app_font_quiet(path: str) -> str | None:
    try:
        if not path or not os.path.exists(path):
            return None
        fid = QFontDatabase.addApplicationFont(path)
        if fid == -1:
            return None
        fams = QFontDatabase.applicationFontFamilies(fid)
        return fams[0] if fams else None
    except Exception:
        return None

def safe_set_font(widget, family: str | None, size: int, weight: int = -1, bold: bool = False):
    if not family:
        return
    f = QFont(family, pointSize=size)
    if weight != -1:
        f.setWeight(weight)
    if bold:
        f.setBold(True)
    widget.setFont(f)
# ------------------------------------

# ---------- Busy overlay shown during startup ----------
class BusyOverlay(QWidget):
    def __init__(self, parent=None, text="Loading…"):
        super().__init__(parent)

        # Semi-transparent backdrop
        self.setStyleSheet("background-color: rgba(0,0,0,120);")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)  # blocks clicks

        # Centered content
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = QWidget(self)
        v = QVBoxLayout(box)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(text, box)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: white; font-size: 18px;")

        self._bar = QProgressBar(box)
        self._bar.setRange(0, 0)  # indeterminate
        self._bar.setTextVisible(False)
        self._bar.setFixedWidth(260)

        v.addWidget(self._label)
        v.addWidget(self._bar)
        root.addWidget(box, 0, Qt.AlignmentFlag.AlignCenter)

        # Track parent geometry changes
        if parent:
            parent.installEventFilter(self)
            # Make sure we start at the correct size immediately
            self._resize_to_parent()

        self.hide()

    def set_text(self, text: str):
        self._label.setText(text)

    def _resize_to_parent(self):
        p = self.parent()
        if p is not None:
            # Cover the entire parent and stay on top
            self.setGeometry(p.rect())
            self.raise_()

    def show(self):
        # Ensure geometry is correct at the time of showing
        self._resize_to_parent()
        super().show()

    def eventFilter(self, watched, event):
        # Whenever the parent resizes/moves/shows, stretch overlay again
        if watched is self.parent():
            t = event.type()
            if t in (event.Type.Resize, event.Type.Move, event.Type.Show, event.Type.ZOrderChange):
                self._resize_to_parent()
        return super().eventFilter(watched, event)



# ---------------------------------------------------------------------


basedir = os.path.dirname(__file__)

obj = OfflineRS()

txt_version = "v3.0.01"

txt_updatedate = "09.10.2025"

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
        safe_set_font(btn_continue, FONT_BE_REG, 14)

        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        safe_set_font(lbl_title, FONT_BE_EXTRA, 40, weight=800)
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        safe_set_font(lbl_version, FONT_BE_REG, 40)
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel(txt_stuff, self)
        safe_set_font(lbl_stuff, FONT_BE_REG, 12)
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
        safe_set_font(btn_continue, FONT_BE_REG, 14)
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_import = QPushButton("")
        btn_import.setIcon(QIcon(sty_ico_import))
        btn_import.setIconSize(QSize(30, 30))
        btn_import.released.connect(self.import_location)
        btn_import.setStyleSheet(sty_btn_import)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        safe_set_font(lbl_title, FONT_BE_EXTRA, 20, weight=800)
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        safe_set_font(lbl_version, FONT_BE_REG, 20)
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel("import location (HTML):", self)
        safe_set_font(lbl_stuff, FONT_BE_REG, 20)
        lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QLineEdit("text goes here.")
        safe_set_font(self.txtbox_location, FONT_BE_REG, 14)
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
        safe_set_font(btn_continue, FONT_BE_REG, 14)
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_import = QPushButton("")
        btn_import.setIcon(QIcon(sty_ico_import))
        btn_import.setIconSize(QSize(30, 30))
        btn_import.released.connect(self.export_location)
        btn_import.setStyleSheet(sty_btn_import)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        safe_set_font(lbl_title, FONT_BE_EXTRA, 20, weight=800)
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        safe_set_font(lbl_version, FONT_BE_REG, 20)
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel("export folder (CSV):", self)
        safe_set_font(lbl_stuff, FONT_BE_REG, 20)
        lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QLineEdit("text goes here.")
        safe_set_font(self.txtbox_location, FONT_BE_REG, 14)
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
        safe_set_font(btn_continue, FONT_BE_REG, 14)
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        self.checkbox = QCheckBox("Append date + time to filename.", self)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        safe_set_font(self.checkbox, FONT_BE_REG, 14)
        # self.checkbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        safe_set_font(lbl_title, FONT_BE_EXTRA, 20, weight=800)
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        safe_set_font(lbl_version, FONT_BE_REG, 20)
        lbl_version.setStyleSheet("color: #AAA;")

        lbl_stuff = QLabel("name your roster datasets (CSV):", self)
        safe_set_font(lbl_stuff, FONT_BE_REG, 20)
        lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QLineEdit("text goes here.")
        self.txtbox_location.mousePressEvent = self.clear_on_click
        safe_set_font(self.txtbox_location, FONT_BE_REG, 14)
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
        layout_center.addWidget(self.checkbox, 2, 0)
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

    def on_checkbox_changed(self, value):
        state = Qt.CheckState(value)
        current_text = self.txtbox_location.text()
        current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        if state == Qt.CheckState.Checked:
            self.txtbox_location.setText(current_text + "---" + current_time)
        elif state == Qt.CheckState.Unchecked:
            past_text = self.txtbox_location.text().rsplit("---")
            self.txtbox_location.setText(past_text[0])

    def clear_on_click(self, event):
        self.txtbox_location.clear()
        self.checkbox.setCheckState(Qt.CheckState.Unchecked)
        # Call the default mousePressEvent to ensure normal behavior
        super(QLineEdit, self.txtbox_location).mousePressEvent(event)

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
        safe_set_font(btn_continue, FONT_BE_REG, 14)
        btn_continue.setStyleSheet(sty_btn_continue)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_exit = QPushButton("exit program")
        btn_exit.released.connect(self.end_game)
        safe_set_font(btn_exit, FONT_BE_REG, 14)
        btn_exit.setStyleSheet(sty_btn_exit)
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_title = QLabel("Examsoft RosterScraper", self)
        safe_set_font(lbl_title, FONT_BE_EXTRA, 20, weight=800)
        lbl_title.setStyleSheet("padding-left: 1px; padding-right: 0px;")

        lbl_version = QLabel(txt_version, self)
        safe_set_font(lbl_version, FONT_BE_REG, 20)
        lbl_version.setStyleSheet("color: #AAA;")

        self.lbl_stuff = QLabel("X students loaded:", self)
        safe_set_font(self.lbl_stuff, FONT_BE_REG, 20)
        self.lbl_stuff.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.txtbox_location = QTextEdit(obj.all_stu)
        safe_set_font(self.txtbox_location, FONT_BE_REG, 14)
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



    
# ---------- Staged startup (show window fast, build pages after) ----------
if __name__ == "__main__":
    import sys, os
    from PyQt6.QtWidgets import QMessageBox

    app = QApplication.instance() or QApplication(sys.argv)

    # Fast show a shell window
    stacked_widget = QStackedWidget()
    stacked_widget._pages = ()
    stacked_widget.resize(800, 520)
    stacked_widget.setWindowTitle("RosterScraper")
    stacked_widget.show()

    # Busy overlay
    startup_busy = BusyOverlay(parent=stacked_widget, text="Loading…")
    startup_busy.show()
    startup_busy.raise_()
    QApplication.processEvents()

    # Globals for font families
    FONT_BE_REG = None
    FONT_BE_EXTRA = None
    FONT_BE_SEMI = None

    def _stage_1():
        startup_busy.set_text("Loading fonts…")
        base_dir = os.path.dirname(__file__)
        global FONT_BE_REG, FONT_BE_EXTRA, FONT_BE_SEMI

        FONT_BE_REG   = load_app_font_quiet(os.path.join(base_dir, "fonts", "BeVietnam-Regular.ttf"))

        FONT_BE_EXTRA = load_app_font_quiet(os.path.join(base_dir, "fonts", "BeVietnam-ExtraBold.ttf"))

        FONT_BE_SEMI  = load_app_font_quiet(os.path.join(base_dir, "fonts", "BeVietnam-SemiBold.ttf"))

        QTimer.singleShot(50, _stage_2)

    def _stage_2():
        startup_busy.set_text("Preparing screens…")

        try:
            w0 = preview_results_Widget()
            w1 = exp_name_Widget()
            w2 = exp_tofolder_Widget()
            w3 = import_loc_Widget()
            w4 = startscreen_Widget()
        except Exception as e:
            startup_busy.hide()
            QMessageBox.critical(stacked_widget, "Startup Error", str(e))
            sys.exit(1)
        stacked_widget._pages = (w0, w1, w2, w3, w4)
        QTimer.singleShot(50, _stage_3)

    def _stage_3():
        startup_busy.set_text("Finalizing UI…")
        try:
            for w in stacked_widget._pages:
                time.sleep(.5)
                stacked_widget.addWidget(w)
            stacked_widget.setCurrentIndex(4)
            stacked_widget.setWindowTitle("RosterScraper: Start")
        except Exception as e:
            startup_busy.hide()
            QMessageBox.critical(stacked_widget, "Startup Error", str(e))
            sys.exit(1)
        QTimer.singleShot(50, _stage_4)

    def _stage_4():
        startup_busy.hide()

    QTimer.singleShot(0, _stage_1)

    sys.exit(app.exec())
# -------------------------------------------------------------------------

