import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QLabel,
    QFileDialog,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QWidget,
    QSizePolicy,
)
from PyQt6.QtGui import QIcon, QPixmap, QImage
import cv2


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Window setup
        self.setWindowTitle("Config Generator")
        self.setGeometry(400, 300, 700, 500)
        self.setWindowIcon(QIcon("assets/gui_icon.png"))

        # Top level layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Feed preview
        self.xrange = None
        self.yrange = None
        self.preview_panel = QWidget()
        self.preview_panel.setLayout(QVBoxLayout())
        self.init_image_preview()

        # Config generator panel
        self.control_panel = QWidget()
        self.control_panel.setLayout(QVBoxLayout())
        self.initln_path_select()
        self.initln_crop_points()

        # Composition
        self.main_layout.addWidget(self.control_panel, stretch=1)
        self.main_layout.addWidget(self.preview_panel, stretch=1)
        self.main_widget.setLayout(self.main_layout)

    def init_image_preview(self):
        self.image_preview = QLabel()
        self.image_preview.setScaledContents(True)
        self.image_preview.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.update_image_preview()

        # Add label to your panel’s layout
        self.preview_panel.layout().addWidget(self.image_preview, stretch=1)

    def update_image_preview(self):
        self.video = cv2.VideoCapture("assets/gtav_front_night_57f53_11r5025.mp4")
        ret, frame = self.video.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.xrange is not None and self.yrange is not None:
                frame = frame[self.yrange, self.xrange]
            frame_qimage = convert_cvimg_to_qimg(frame)
            frame_pixmap = QPixmap(frame_qimage)
            self.image_preview.setPixmap(frame_pixmap)
        else:
            self.image_preview.setText("Failed to read video.")

    def initln_path_select(self):
        self.path_select = QWidget()
        self.path_select.setLayout(QHBoxLayout())
        self.lbl_path_select = QLabel(parent=self, text="Path:")
        self.fld_path_select = QLineEdit(placeholderText="path...")
        self.btn_path_select = QPushButton(parent=self, text="Browse..")
        self.btn_path_select.clicked.connect(self.dialog_path_select)
        self.path_select.layout().addWidget(self.lbl_path_select)
        self.path_select.layout().addWidget(self.fld_path_select)
        self.path_select.layout().addWidget(self.btn_path_select)
        self.control_panel.layout().addWidget(self.path_select)

    def dialog_path_select(self) -> QFileDialog:
        file_path = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select directory",
            directory=".",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        self.fld_path_select.setText(file_path[0])

    def update_crop_points(self):
        self.xrange = slice(self.from_x.text, self.to_x.text)
        self.range = slice(self.from_y.text, self.to_y.text)
        self.update_image_preview()

    def initln_crop_points(self):
        self.crop_point_select = QWidget()
        self.crop_point_select.setLayout(QHBoxLayout())
        self.from_x_label = QLabel(parent=self, text="from x:")
        self.from_x = QLineEdit(placeholderText="0")
        self.to_x_label = QLabel(parent=self, text="from x:")
        self.to_x = QLineEdit(placeholderText="1000")
        self.from_y_label = QLabel(parent=self, text="from x:")
        self.from_y = QLineEdit(placeholderText="0")
        self.to_y_label = QLabel(parent=self, text="from x:")
        self.to_y = QLineEdit(placeholderText="1000")
        self.refresh_crop = QPushButton(parent=self, text="Refresh")
        self.refresh_crop.clicked.connect(self.update_crop_points)
        self.crop_point_select.layout().addWidget(self.from_x_label)
        self.crop_point_select.layout().addWidget(self.from_x)
        self.crop_point_select.layout().addWidget(self.to_x_label)
        self.crop_point_select.layout().addWidget(self.to_x)
        self.crop_point_select.layout().addWidget(self.from_y_label)
        self.crop_point_select.layout().addWidget(self.from_y)
        self.crop_point_select.layout().addWidget(self.to_y_label)
        self.crop_point_select.layout().addWidget(self.to_y)
        self.control_panel.layout().addWidget(self.crop_point_select)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def convert_cvimg_to_qimg(cvImg):
    height, width, _ = cvImg.shape
    bytesPerLine = 3 * width
    qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
    return qImg


if __name__ == "__main__":
    main()
