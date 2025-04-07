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
    QButtonGroup,
)
from PyQt6.QtGui import QIcon, QPixmap, QImage
import cv2


class PreviewWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setLayout(QVBoxLayout())
        self.xrange = None
        self.yrange = None
        self.init_image_preview()

    def init_image_preview(self):
        self.image_preview = QLabel()
        self.image_preview.setScaledContents(True)
        self.image_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.update_image_preview(None, None)

        # Add label to your panel’s layout
        self.layout().addWidget(self.image_preview, stretch=1)

    def update_image_preview(self, xrange=None, yrange=None):
        self.xrange = xrange
        self.yrange = yrange
        self.video = cv2.VideoCapture(self.parent.video_path)
        ret, frame = self.video.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.xrange is not None and self.yrange is not None:
                frame = frame[self.yrange, self.xrange]
            frame_qimage = convert_cvimg_to_qimg(frame)
            frame_pixmap = QPixmap(frame_qimage)
            self.image_preview.setPixmap(frame_pixmap)
            self.adjustSize()
        else:
            self.image_preview.setText("No video selected")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Window setup
        self.setWindowTitle("Config Generator")
        self.setGeometry(400, 300, 700, 500)
        self.setWindowIcon(QIcon("assets/gui_icon.png"))
        self.video_path = None

        # Top level layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Feed preview
        self.preview = PreviewWindow(self)

        # Config generator panel
        self.control_panel = QWidget()
        self.control_panel.setLayout(QVBoxLayout())

        # Main params
        self.initln_mode_select()
        self.initln_path_select()
        self.initln_feed_details()
        self.initln_box_section_header()
        self.initln_box_params()

        # Detail params
        self.initln_crop_points()

        # Composition
        self.main_layout.addWidget(self.control_panel, stretch=1)
        self.preview.show()
        # self.main_layout.addWidget(self.preview, stretch=1)
        self.main_widget.setLayout(self.main_layout)

    def initln_path_select(self):
        self.path_select = QWidget()
        self.path_select.setLayout(QHBoxLayout())
        self.lbl_path_select = QLabel(parent=self, text="Feed path")
        self.fld_path_select = QLineEdit(placeholderText="path...")
        self.btn_path_select = QPushButton(parent=self, text="Browse..")
        self.btn_path_select.clicked.connect(self.dialog_path_select)
        self.btn_path_select.clicked.connect(self.preview.update_image_preview)
        self.path_select.layout().addWidget(self.lbl_path_select)
        self.path_select.layout().addWidget(self.fld_path_select)
        self.path_select.layout().addWidget(self.btn_path_select)
        self.control_panel.layout().addWidget(self.path_select)

    def initln_box_section_header(self):
        self.box_section_header = QWidget()
        self.box_section_header.setLayout(QHBoxLayout())
        lbl_header = QLabel(parent=self, text="Detection zone configuration:")
        self.box_section_header.layout().addWidget(lbl_header)
        self.control_panel.layout().addWidget(self.box_section_header)

    def initln_box_params(self):
        self.box_params = QWidget()
        self.box_params.setLayout(QHBoxLayout())
        self.lbl_num_boxes = QLabel(parent=self, text="Number of boxes")
        self.fld_num_boxes = QLineEdit(placeholderText="10")
        self.lbl_box_size = QLabel(parent=self, text="Box size")
        self.fld_box_size = QLineEdit(placeholderText="10")
        self.lbl_start_from_box = QLabel(parent=self, text="Start from box")
        self.fld_start_from_box = QLineEdit(placeholderText="0")
        self.lbl_trim_last_n = QLabel(parent=self, text="Trim last N boxes")
        self.fld_trim_last_n = QLineEdit(placeholderText="0")
        self.box_params.layout().addWidget(self.lbl_num_boxes)
        self.box_params.layout().addWidget(self.fld_num_boxes)
        self.box_params.layout().addWidget(self.lbl_box_size)
        self.box_params.layout().addWidget(self.fld_box_size)
        self.box_params.layout().addWidget(self.lbl_start_from_box)
        self.box_params.layout().addWidget(self.fld_start_from_box)
        self.box_params.layout().addWidget(self.lbl_trim_last_n)
        self.box_params.layout().addWidget(self.fld_trim_last_n)
        self.control_panel.layout().addWidget(self.box_params)

    def initln_feed_details(self):
        feed_details = QWidget()
        feed_details.setLayout(QHBoxLayout())
        self.id = self.create_labeled_field("Run ID:", placeholder_text="1")
        self.fps = self.create_labeled_field("Feed FPS:", placeholder_text="0")
        self.real_rpm = self.create_labeled_field(
            "Real RPM:", placeholder_text="0")
        feed_details.layout().addWidget(self.id)
        feed_details.layout().addWidget(self.fps)
        feed_details.layout().addWidget(self.real_rpm)
        self.control_panel.layout().addWidget(feed_details)

    def initln_mode_select(self):
        bar = QWidget()
        bar.setLayout(QHBoxLayout())

        bpm_mode = QPushButton(parent=self, text="BPM")
        bpm_mode.setCheckable(True)
        bpm_mode.setAutoExclusive(True)
        bpm_mode.setChecked(True)

        opticalflow_mode = QPushButton(parent=self, text="Optical flow")
        opticalflow_mode.setCheckable(True)
        opticalflow_mode.setAutoExclusive(True)

        group = QButtonGroup()
        group.addButton(bpm_mode)
        group.addButton(opticalflow_mode)

        bar.layout().addWidget(bpm_mode)
        bar.layout().addWidget(opticalflow_mode)
        self.control_panel.layout().addWidget(bar)

    def dialog_path_select(self) -> QFileDialog:
        file_path = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select directory",
            directory=".",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        self.fld_path_select.setText(file_path[0])
        self.video_path = file_path[0]

    def create_labeled_field(self, label_text, placeholder_text=""):
        container = QWidget()
        container.setLayout(QHBoxLayout())

        label = QLabel(parent=self, text=label_text)
        field = QLineEdit(placeholderText=placeholder_text)

        container.layout().addWidget(label)
        container.layout().addWidget(field)

        return container

    def update_crop_points(self):
        # from y and to y are flipped on purpose. This is because we follow
        # real-life y axis and not the pythonic code one (which is flipped)
        self.xrange = slice(int(self.from_x.text()), int(self.to_x.text()))
        self.yrange = slice(int(self.from_y.text()), int(self.to_y.text()))
        self.preview.update_image_preview(
            xrange=self.xrange, yrange=self.yrange)

    def closeEvent(self, event):
        # This ensures the child window (preview) closes when parent is closed
        if self.preview:
            self.preview.close()
        event.accept()

    def initln_crop_points(self):
        self.crop_point_select = QWidget()
        self.crop_point_select.setLayout(QHBoxLayout())
        self.from_x_label = QLabel(parent=self, text="from x")
        self.from_x = QLineEdit(placeholderText="0")
        self.to_x_label = QLabel(parent=self, text="to x")
        self.to_x = QLineEdit(placeholderText="1000")
        self.from_y_label = QLabel(parent=self, text="from y")
        self.from_y = QLineEdit(placeholderText="0")
        self.to_y_label = QLabel(parent=self, text="to y")
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
        self.crop_point_select.layout().addWidget(self.refresh_crop)
        self.control_panel.layout().addWidget(self.crop_point_select)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def convert_cvimg_to_qimg(cvImg):
    height, width, _ = cvImg.shape
    bytesPerLine = 3 * width
    data = cvImg.tobytes()
    qImg = QImage(data, width, height, bytesPerLine,
                  QImage.Format.Format_RGB888)
    return qImg


if __name__ == "__main__":
    main()
