import sys
import os
import time
import urllib2
import requests
import datetime
import functools
from PyQt4 import QtGui, QtCore, Qt

import configuration

sys.path.append("J:/Scripting/scoper/WebScraper")

import scraper


def time_it(func):
    def wrapped(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time() - start_time
        print "*" * 50
        print func.__name__, "took", end_time, "time"
        print "*" * 50
        return result
    return wrapped


class Interface(QtGui.QWidget):
    def __init__(self, url_dictionary):
        QtGui.QWidget.__init__(self)

        self.url_dictionary = url_dictionary
        self.resize(400, 700)

        self.setWindowTitle("Scoper (Interactive)")

        self.layout = QtGui.QVBoxLayout()
        self.lineEdit_layout = QtGui.QHBoxLayout()

        self.refresh_timer = QtGui.QSpinBox()
        self.images_widget = QtGui.QTreeWidget()
        self.url_bar = QtGui.QLineEdit()
        self.download_bar = QtGui.QLineEdit()

        _widget_headers = ("user name", "broadcast status", "a/t", "l/v", "t/v", "download", "preview")
        
        self.images_widget.setHeaderLabels(_widget_headers)
        self.images_widget.setIconSize(QtCore.QSize(128,128))

        self.lineEdit_layout.addWidget(self.url_bar)
        self.lineEdit_layout.addWidget(self.download_bar)

        self.layout.addWidget(self.refresh_timer)
        self.layout.addWidget(self.images_widget)
        self.layout.addLayout(self.lineEdit_layout)

        self.setLayout(self.layout)

        self.show()
        self.update_widget()


    def handler(self):
        '''
        main function
        '''
        pass

    @time_it
    def update_widget(self):
        for user in self.url_dictionary:
            #__import__("pprint").pprint(user)
            image_url = user.get("image_url_small", user.get("image_url", user.get("profile_image_url")))
            downloaded = self.download_thumbs(image_url, os.path.join(os.path.expanduser("~"), os.getenv('username'), "scoper_downloads"))
            if downloaded is None:
                continue
            item = UserWidget(user, downloaded, self.images_widget)
            QtGui.QApplication.processEvents()
            self.images_widget.addTopLevelItem(item)
            QtGui.QApplication.processEvents()
            self.update()
            QtGui.QApplication.processEvents()
            

    @time_it
    def download_thumbs(self, url, download_path=None):

        # try:
        #     with open (download_path, 'wb') as writer:
        #         writer.write(urllib2.urlopen(url).read())
        # except:
        #     return None
        try:
            link = scraper.URL(url)
        except:
            return None

        if download_path is None:
            downloaded = link.download() 
        else:   
            downloaded = link.download(download_path=download_path, overwrite=True)
        return downloaded

class UserWidget(QtGui.QTreeWidgetItem):
    def __init__(self, user_dictionary, image_path, QWidgetparent=None):

        QtGui.QTreeWidgetItem.__init__(self, QWidgetparent)

        self.user_name = user_dictionary.get('user_display_name')
        self.setText(0, self.user_name)
        self.user_image =  QtGui.QIcon(image_path)
        self.setIcon(0, self.user_image)

        date = datetime.datetime.strptime(user_dictionary.get("start").split("T")[0], "%Y-%m-%d").date()
        time = datetime.datetime.strptime(user_dictionary.get("start").split("T")[-1].split(".")[0], "%H:%M:%S").time()
        total_time = datetime.datetime.now() - datetime.datetime.combine(date, time)
        passed_time = datetime.timedelta(seconds=total_time.total_seconds())

        self.broadcast_id = user_dictionary.get('user_id')
        self.broadcast_status = user_dictionary.get('status')

        self.broadcast_status_label = QtGui.QLabel(self.broadcast_status)
        self.user_name_label = QtGui.QLabel(self.user_name)
        self.active_time_label = QtGui.QLabel(str(passed_time))
        self.live_views_label = QtGui.QLabel(str(user_dictionary.get('n_watching')))
        self.total_views_label = QtGui.QLabel(str(user_dictionary.get('n_total_watching')))

        self.download_button = QtGui.QPushButton('Download')
        self.preview_button = QtGui.QPushButton('Preview')

        self.broadcast_status_label.setWordWrap(True)

        QWidgetparent.setItemWidget(self, 1, self.broadcast_status_label)
        QWidgetparent.setItemWidget(self, 2, self.active_time_label)
        QWidgetparent.setItemWidget(self, 3, self.live_views_label)
        QWidgetparent.setItemWidget(self, 4, self.total_views_label)
        QWidgetparent.setItemWidget(self, 5, self.download_button)
        QWidgetparent.setItemWidget(self, 6, self.preview_button)

        self.download_button.clicked.connect(self.download_scope)
        self.download_button.clicked.connect(functools.partial(self.download_scope))

    def download_scope(self, *args):
        print args




login = configuration.Login()
data = configuration.Config()
cookie = data.get('cookie')
session = requests.Session()
data = session.post("https://api.periscope.tv/api/v2/rankedBroadcastFeed", json=data)
sorted_data = sorted(data.json(), reverse=True, key=lambda x: x.get('n_watching'))

app = QtGui.QApplication(sys.argv)
ui = Interface(sorted_data)
# ui.show()
app.exec_()
