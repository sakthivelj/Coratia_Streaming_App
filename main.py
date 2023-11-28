import sys
import cv2
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QLineEdit, QHBoxLayout, QFormLayout, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
import time
import os
from PyQt5.QtGui import QIcon
import warnings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Settings')

        self.port_edit = QLineEdit()

        self.save_location_edit = QLineEdit()
        self.save_location_edit.setReadOnly(True) 

        save_location_button = QPushButton('Select Directory', self)
        save_location_button.clicked.connect(self.select_save_directory)

        layout = QFormLayout()
        layout.addRow('Port Number:', self.port_edit)
        layout.addRow('Save Location:', self.save_location_edit)
        layout.addRow('', save_location_button) 

        save_button = QPushButton('Save', self)
        save_button.clicked.connect(self.save_settings)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(save_button)

        self.setLayout(main_layout)

        self.load_settings()
    
    def select_save_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            self.save_location_edit.setText(directory)

    def load_settings(self):
        settings = QSettings()
        self.port_edit.setText(settings.value('port_number', '5600'))
        self.save_location_edit.setText(settings.value('save_location', 'recorded_video.mp4'))

    def save_settings(self):
        settings = QSettings()
        settings.setValue('port_number', self.port_edit.text())
        settings.setValue('save_location', self.save_location_edit.text())
        self.accept()
    

class VideoRecorderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.cap = cv2.VideoCapture()
        if not self.cap.open(f"udp://{self.get_ip_address()}:{self.get_port_number()}"):
            print("Error: Unable to open video stream.")
            return

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  

        self.is_recording = False
        self.video_writer = None

    def initUI(self):
        self.setWindowTitle('Video Recorder App')

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.record_button = QPushButton('Record', self)
        self.record_button.clicked.connect(self.toggle_record)

        self.settings_button = QPushButton('Settings', self)
        self.settings_button.clicked.connect(self.show_settings)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.settings_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def update_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            print("Error: Unable to read frame from the video stream.")
            return

        if ret:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QPixmap.fromImage(QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888))
            self.video_label.setPixmap(q_img)

            if self.is_recording:
                if self.video_writer is None:
                    fps = 30.0 if self.cap.get(cv2.CAP_PROP_FPS) == 30.0 else 24.0
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    save_location = self.get_save_location()
                    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())  
                    filename = f"video_{timestamp}.mp4"
                    save_path = os.path.join(save_location, filename)
                    self.video_writer = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

                self.video_writer.write(frame)

    def toggle_record(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            print("Recording started")
            self.record_button.setText('Stop')
        else:
            print("Recording stopped")
            self.record_button.setText('Record') 

            if self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.cap = cv2.VideoCapture(f"udp://{self.get_ip_address()}:{self.get_port_number()}")

    def get_ip_address(self):
        settings = QSettings()
        return settings.value('ip_address', '192.168.1.4')

    def get_port_number(self):
        settings = QSettings()
        return settings.value('port_number', '5600')

    def get_save_location(self):
        settings = QSettings()
        return settings.value('save_location', 'recorded_video.mp4')

if __name__ == '__main__':

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        app = QApplication(sys.argv)
        icon_path = 'resources/icon.png'
        app.setWindowIcon(QIcon(icon_path))
        window = VideoRecorderApp()
        window.setGeometry(100, 100, 800, 600)
        window.show()
        sys.exit(app.exec_())