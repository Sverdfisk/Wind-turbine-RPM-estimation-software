import sys
import json
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
    QSpacerItem,
    QFrame,
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
        self.apply_global_styles()

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
        self.initln_path_select()
        self.initln_crop_points()
        self.initln_feed_details()

        self.add_spacer_horizontal_line(thickness=1)

        #  Mode select
        self.initln_mode_select()
        self.add_spacer_horizontal_line()

        #  Detection params
        self.initln_box_section_header()
        self.initln_box_params()
        self.initln_detection_params()

        self.add_spacer_horizontal_line(thickness=1)

        #  Processing params
        self.initln_kernel_params()

        #  Generate config button
        self.initln_generate_config()

        # Composition
        self.main_layout.addWidget(self.control_panel, stretch=1)
        self.preview.show()
        # self.main_layout.addWidget(self.preview, stretch=1)
        self.main_widget.setLayout(self.main_layout)

    def initln_path_select(self):
        self.path_select = QWidget()
        self.path_select.setLayout(QHBoxLayout())
        path_select_input, self.fld_path_select = self.create_labeled_field(
            "Feed path", "path..."
        )
        self.btn_path_select = QPushButton(parent=self, text="Browse..")
        self.btn_path_select.clicked.connect(self.dialog_path_select)
        self.btn_path_select.clicked.connect(self.preview.update_image_preview)
        self.path_select.layout().addWidget(path_select_input)
        self.path_select.layout().addWidget(self.btn_path_select)
        self.control_panel.layout().addWidget(self.path_select)

    def add_spacer_horizontal_line(self, thickness=1):
        spacer_container = QWidget()
        spacer_container.setLayout(QHBoxLayout())

        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.HLine)
        spacer.setFrameShadow(QFrame.Shadow.Sunken)
        spacer.setLineWidth(thickness)

        spacer_container.layout().addWidget(spacer)
        self.control_panel.layout().addWidget(spacer_container)

    def add_empty_space(self, height=10):
        spacer = QSpacerItem(
            20, height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self.control_panel.layout().addSpacerItem(spacer)

    def initln_kernel_params(self):
        self.kernel_params = QWidget()
        self.kernel_params.setLayout(QHBoxLayout())
        self.kernel_size, _ = self.create_labeled_field(
            "Kernel size", placeholder_text="10"
        )
        self.dilation_iterations, _ = self.create_labeled_field(
            "Dilation iterations", placeholder_text="2"
        )
        self.erosion_iterations, _ = self.create_labeled_field(
            "Erosion iterations", placeholder_text="1"
        )
        self.kernel_params.layout().addWidget(self.kernel_size)
        self.kernel_params.layout().addWidget(self.dilation_iterations)
        self.kernel_params.layout().addWidget(self.erosion_iterations)
        self.control_panel.layout().addWidget(self.kernel_params)

    def initln_box_section_header(self):
        self.box_section_header = QWidget()
        self.box_section_header.setLayout(QHBoxLayout())
        lbl_header = QLabel(parent=self, text="Detection zone configuration:")
        self.box_section_header.layout().addWidget(lbl_header)
        self.control_panel.layout().addWidget(self.box_section_header)

    def initln_box_params(self):
        self.box_params = QWidget()
        self.box_params.setLayout(QHBoxLayout())

        quadrant, _ = self.create_labeled_field("Quadrant", placeholder_text="1")
        num_boxes, _ = self.create_labeled_field(
            "Number of boxes", placeholder_text="10"
        )
        box_size, _ = self.create_labeled_field("Box size", placeholder_text="10")
        start_from_box, _ = self.create_labeled_field(
            "Start from box", placeholder_text="0"
        )
        trim_last_n, _ = self.create_labeled_field(
            "Trim last N boxes", placeholder_text="0"
        )

        self.box_params.layout().addWidget(quadrant)
        self.box_params.layout().addWidget(num_boxes)
        self.box_params.layout().addWidget(box_size)
        self.box_params.layout().addWidget(start_from_box)
        self.box_params.layout().addWidget(trim_last_n)
        self.control_panel.layout().addWidget(self.box_params)

    def initln_detection_params(self):
        self.detection_params = QWidget()
        self.detection_params.setLayout(QHBoxLayout())

        fb_size_container, self.fb_size = self.create_labeled_field(
            "Frame buffer size", "5"
        )

        update_frequency_container, self.update_freq = self.create_labeled_field(
            "Update frequency", "2"
        )

        contrast_multiplier_container, self.contrast_multiplier = (
            self.create_labeled_field("Contrast multiplier", "1")
        )

        threshold_multiplier_container, self.threshold_multiplier = (
            self.create_labeled_field("Detection threshold multiplier", "1")
        )

        self.detection_params.layout().addWidget(fb_size_container)
        self.detection_params.layout().addWidget(update_frequency_container)
        self.detection_params.layout().addWidget(contrast_multiplier_container)
        self.detection_params.layout().addWidget(threshold_multiplier_container)
        self.control_panel.layout().addWidget(self.detection_params)

    def initln_feed_details(self):
        feed_details = QWidget()
        feed_details.setLayout(QHBoxLayout())
        self.id, _ = self.create_labeled_field("Run ID", placeholder_text="1")
        self.fps, _ = self.create_labeled_field("Feed FPS", placeholder_text="0")
        self.real_rpm, _ = self.create_labeled_field("Real RPM", placeholder_text="0")
        feed_details.layout().addWidget(self.id)
        feed_details.layout().addWidget(self.fps)
        feed_details.layout().addWidget(self.real_rpm)
        self.control_panel.layout().addWidget(feed_details)

    def initln_generate_config(self):
        config_button = QWidget()
        config_button.setLayout(QHBoxLayout())
        btn = QPushButton(text="Generate config")
        btn.setObjectName("generate_config")
        btn.pressed.connect(self.generate_config)
        config_button.layout().addWidget(btn)
        self.control_panel.layout().addWidget(config_button)

    def generate_config(self):
        json_params = self.extract_params()
        with open("args.json", "w", encoding="utf-8") as f:
            json.dump(json_params, f, ensure_ascii=False, indent=4)

    def extract_params(self):
        items = self.findChildren(QLineEdit)
        items_dict = dict()
        for item in items:
            items_dict[item.property("label")] = item.text()
        return items_dict

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
        field.setProperty("label", label_text)

        container.layout().addWidget(label)
        container.layout().addWidget(field)

        return container, field

    def update_crop_points(self):
        try:
            from_x_text = self.fld_from_x.text()
            to_x_text = self.fld_to_x.text()
            from_y_text = self.fld_from_y.text()
            to_y_text = self.fld_to_y.text()

            from_x = int(from_x_text) if from_x_text.strip() else 0
            to_x = int(to_x_text) if to_x_text.strip() else 100
            from_y = int(from_y_text) if from_y_text.strip() else 0
            to_y = int(to_y_text) if to_y_text.strip() else 100

            self.xrange = slice(from_x, to_x)
            self.yrange = slice(from_y, to_y)
            self.preview.update_image_preview(xrange=self.xrange, yrange=self.yrange)

        except ValueError:
            print("Please enter valid integer values for all crop coordinates")

    def closeEvent(self, event):
        # This ensures the child window (preview) closes when parent is closed
        if self.preview:
            self.preview.close()
        event.accept()

    def initln_crop_points(self):
        self.crop_point_select = QWidget()
        self.crop_point_select.setLayout(QHBoxLayout())

        from_x, self.fld_from_x = self.create_labeled_field(
            "from x", placeholder_text="0"
        )
        to_x, self.fld_to_x = self.create_labeled_field("to x", placeholder_text="1000")
        from_y, self.fld_from_y = self.create_labeled_field(
            "from y", placeholder_text="0"
        )
        to_y, self.fld_to_y = self.create_labeled_field("to y", placeholder_text="1000")

        self.refresh_crop = QPushButton(parent=self, text="Refresh")
        self.refresh_crop.clicked.connect(self.update_crop_points)
        self.crop_point_select.layout().addWidget(from_x)
        self.crop_point_select.layout().addWidget(to_x)
        self.crop_point_select.layout().addWidget(from_y)
        self.crop_point_select.layout().addWidget(to_y)
        self.crop_point_select.layout().addWidget(self.refresh_crop)
        self.control_panel.layout().addWidget(self.crop_point_select)

    def apply_global_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QFrame.panel {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }

            QPushButton {
                background-color: #0078d7;
                color: white;
                border: 2px solid transparent;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #005a9e;
            }

            QPushButton:pressed {
                background-color: #004275;
            }

            /* Fix for the focus indicator */
            QPushButton:focus {
                outline: none;
                border: none;
            }

            /* Style for selected buttons */
            QPushButton:checked {
                background-color: #004275;
                border: 2px solid #0078d7;
            }

            /* Additional focus override for checked buttons */
            QPushButton:checked:focus {
                outline: none;
                border: 2px solid #0078d7;
            }

            QPushButton#generate_config {
                background-color: #379937
            }

            QPushButton#generate_config:hover {
                background-color: #187718;
            }

            QPushButton#generate_config:pressed {
                background-color: #225522
            }

            QLineEdit {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 4px;
            }

            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def convert_cvimg_to_qimg(cvImg):
    height, width, _ = cvImg.shape
    bytesPerLine = 3 * width
    data = cvImg.tobytes()
    qImg = QImage(data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
    return qImg


if __name__ == "__main__":
    main()
