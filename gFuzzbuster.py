#!/usr/bin/env python3.11
import concurrent.futures
import sys
import logging
from datetime import datetime as dt
import threading
import Core.network
import Core.process
import Core.reports
import Core.settings
from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QListWidget, QMenu, QMenuBar, QPushButton, QWidget)

logging.basicConfig(filename="log.txt", encoding='utf-8', level=logging.INFO, format='')


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(615, 400)
        # MainWindow.setTabShape(QTabWidget.Rounded)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.btn_wordlist = QPushButton(self.centralwidget)
        self.btn_wordlist.setObjectName(u"btn_wordlist")
        self.btn_wordlist.setGeometry(QRect(10, 310, 151, 26))
        self.line_wordlist = QLineEdit(self.centralwidget)
        self.line_wordlist.setObjectName(u"line_wordlist")
        self.line_wordlist.setGeometry(QRect(170, 310, 431, 26))
        self.line_url = QLineEdit(self.centralwidget)
        self.line_url.setObjectName(u"line_url")
        self.line_url.setGeometry(QRect(50, 280, 551, 26))
        self.label_url = QLabel(self.centralwidget)
        self.label_url.setObjectName(u"label_url")
        self.label_url.setGeometry(QRect(10, 280, 41, 20))
        self.btn_start = QPushButton(self.centralwidget)
        self.btn_start.setObjectName(u"btn_start")
        self.btn_start.setGeometry(QRect(480, 340, 121, 26))
        self.listWidget_results = QListWidget(self.centralwidget)
        self.listWidget_results.setObjectName(u"listWidget_results")
        self.listWidget_results.setGeometry(QRect(5, 11, 601, 251))
        # MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 615, 23))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        # MainWindow.setMenuBar(self.menubar)
        QWidget.setTabOrder(self.line_url, self.btn_wordlist)
        QWidget.setTabOrder(self.btn_wordlist, self.line_wordlist)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

        self.actionExit.triggered.connect(self.exit_app)
        self.btn_start.clicked.connect(self.start_fuzz)
        self.btn_wordlist.clicked.connect(self.add_url_result)

    # setupUi

    def exit_app(self):
        sys.exit()

    def start_fuzz(self):
        url = self.line_url.text()
        wordlist = self.line_wordlist.text()

        thread = threading.Thread(target=self.fuzz, args=(url, wordlist))
        thread.start()

    def add_url_result(self, response):
        response = "test"
        self.listWidget_results.addItem(response)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"gFuzzbuster", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.btn_wordlist.setText(QCoreApplication.translate("MainWindow", u"Select Wordlist", None))
        self.line_wordlist.setText(QCoreApplication.translate("MainWindow", u"/usr/share/wordlists/", None))
        # if QT_CONFIG(tooltip)
        self.line_url.setToolTip(
            QCoreApplication.translate("MainWindow", u"https://www.google.com/search?q=FUZZ", None))
        # endif // QT_CONFIG(tooltip)
        self.label_url.setText(QCoreApplication.translate("MainWindow", u"URL:", None))
        self.btn_start.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))

    # retranslateUi

    def fuzz(self, url: str, wordlist: str) -> list:
        original_fuzzer_url = url
        networking = Core.network.Network()
        processing = Core.process.Process(wordlist)
        formatted_url_list = processing.format_wordlist(url)

        # print(id(formatted_url_list))
        total_urls = 0
        i = 0
        valid_response_list = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=Core.settings.Settings.max_workers) as executor:
            futures = []

            for url in formatted_url_list:
                futures.append(executor.submit(networking.perform_request, url))
                total_urls += 1
                print(f"Total URLs: {total_urls}...", end="\r")

            try:
                for future in concurrent.futures.as_completed(futures):
                    response = future.result()
                    if response is not None:
                        valid_response_list.append(response)
                        self.listWidget_results.addItem(response)

                    i += 1
                    print(end='\x1b[2K')
                    print(f"{i} of {total_urls}", end="\r")  # to end of line

            except KeyboardInterrupt:
                print("\n[!] Keyboard Interrupt Detected\n[!] Gracefully closing after threads finish... "
                      "(or press ctrl-c again)")
                exit(0)

            except Exception as e:
                print("[!] Is the web server running?")
                print(f"[!] {e}")
                i += 1
                pass

            print(end='\x1b[2K')
            print(f"{i} of {total_urls}")

            assert type(valid_response_list) == list
            logging.info(
                f"{dt.now()} ({original_fuzzer_url}) {len(valid_response_list)} resolved URLs returned from {total_urls}"
                f" total URL entries.")
            for url in valid_response_list:
                logging.info(f" -  {url}")

            return valid_response_list


def main():
    app = QApplication(sys.argv)
    MainWindow = QWidget()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
