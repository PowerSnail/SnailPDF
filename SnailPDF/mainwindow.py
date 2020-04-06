from typing import List, Dict, Optional, Any
import pathlib
import contextlib
import enum

import fitz
from PIL import Image, ImageQt

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from PySide2.QtCore import Qt

from SnailPDF import pdfview

EMPTY_DOC = fitz.Document()


def set_horizontal_strech(widget: QtWidgets.QWidget, value: int):
    policy = widget.sizePolicy()
    policy.setHorizontalStretch(value)
    widget.setSizePolicy(policy)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Actions
        self.action_open = QtWidgets.QAction(QtGui.QIcon.fromTheme("Open"), "Open")
        self.action_save = QtWidgets.QAction(QtGui.QIcon.fromTheme("Save"), "Save")
        self.action_toggle_sidebar = QtWidgets.QAction("Toggle Sidebar")
        self.action_debug = QtWidgets.QAction("Debug")
        self.action_about = QtWidgets.QAction("About")
        self.action_aboutqt = QtWidgets.QAction("About Qt")
        self.action_next_page = QtWidgets.QAction("Next")
        self.action_prev_page = QtWidgets.QAction("Previous")
        self.action_fit_page = QtWidgets.QAction("Fit Page")
        self.action_next_page_prev = QtWidgets.QAction("Next with Preview")

        # Widgets
        self.pdf_view = pdfview.PDFPageView()
        self.toc_view = QtWidgets.QTreeWidget()
        self.sidebar = QtWidgets.QWidget()

        self.auto_page_turn = False

        self.setup_ui()
        self.pdf_doc: fitz.Document = EMPTY_DOC
        self.current_page = 0

    def setup_ui(self):
        self.setup_menu()
        self.setup_layouts()
        self.setup_events()
        self.setup_toolbar()

    def setup_menu(self):
        menu_file = QtWidgets.QMenu("File")
        menu_file.addAction(self.action_open)
        menu_file.addAction(self.action_save)

        menu_edit = QtWidgets.QMenu("Edit")
        menu_edit.addAction(self.action_debug)

        menu_view = QtWidgets.QMenu("View")
        menu_view.addAction(self.action_toggle_sidebar)

        menu_about = QtWidgets.QMenu("About")
        menu_about.addAction(self.action_about)
        menu_about.addAction(self.action_aboutqt)

        self.menuBar().addMenu(menu_file)
        self.menuBar().addMenu(menu_edit)
        self.menuBar().addMenu(menu_view)
        self.menuBar().addMenu(menu_about)

    def setup_toolbar(self):
        toolbar = QtWidgets.QToolBar()
        toolbar.setFloatable(False)
        toolbar.addAction(self.action_prev_page)
        toolbar.addAction(self.action_next_page)
        toolbar.addAction(self.action_next_page_prev)
        toolbar.addSeparator()
        toolbar.addAction(self.action_fit_page)
        self.addToolBar(toolbar)

    def setup_layouts(self):
        self.toc_view.setHeaderLabels(["Title", "Page"])
        self.toc_view.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.toc_view.header().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents
        )

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.toc_view)
        self.sidebar.setLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        set_horizontal_strech(self.sidebar, 0)
        set_horizontal_strech(self.pdf_view, 1)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.pdf_view)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def setup_events(self):
        self.action_aboutqt.triggered.connect(QtWidgets.QApplication.aboutQt)
        self.action_open.triggered.connect(self.load_file)
        self.action_toggle_sidebar.triggered.connect(self.toggle_sidebar)
        self.action_debug.triggered.connect(self.debug)
        self.action_next_page.triggered.connect(
            lambda: self.goto_page(self.current_page + 1)
        )
        self.action_prev_page.triggered.connect(
            lambda: self.goto_page(self.current_page - 1)
        )
        self.action_next_page_prev.triggered.connect(self.next_page_with_preview)
        self.toc_view.itemClicked.connect(
            lambda item, _: self.goto_page(int(item.text(1)) - 1)
        )

    def load_file(self):
        filename = pathlib.Path(QtWidgets.QFileDialog.getOpenFileName(self)[0])
        if not filename.exists():
            return
        try:
            new_doc = fitz.Document(filename)
        except RuntimeError as err:
            print(f"Failed to open document [fitz] : {filename}")
            return

        if new_doc is None:
            return

        if self.pdf_doc is not None:
            self.pdf_doc.close()
        self.pdf_doc = new_doc
        self.pdf_view.set_page(self.pdf_doc.loadPage(0))
        self.pdf_view.update()

        self.load_toc()

    def load_toc(self):
        if self.pdf_doc == EMPTY_DOC:
            return
        toc = self.pdf_doc.getToC(simple=True)
        self.toc_view.clear()
        parents = [self.toc_view.invisibleRootItem()]
        for lvl, title, page in toc:
            new_item = QtWidgets.QTreeWidgetItem(parents[lvl - 1])
            new_item.setText(0, title)
            new_item.setText(1, str(page))
            if lvl == len(parents):
                parents.append(new_item)
            else:
                parents[lvl] = new_item

    def debug(self):
        self.pdf_view.set_page(self.pdf_doc.loadPage(0))
        self.pdf_view.update()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def next_page_with_preview(self):
        if self.current_page >= self.pdf_doc.pageCount - 1:
            return

        self.pdf_view.set_preview_page(self.pdf_doc.loadPage(self.current_page + 1))
        self.auto_page_turn = True
        self.pdf_view.update()
        QtCore.QTimer.singleShot(5000, lambda: self.goto_page(self.current_page + 1))

    def goto_page(self, page: int):
        if self.pdf_doc == EMPTY_DOC or page < 0 or page >= self.pdf_doc.pageCount:
            return

        self.current_page = page
        self.pdf_view.set_page(self.pdf_doc.loadPage(page))
        self.auto_page_turn = False
        self.pdf_view.update()

