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
    QDialog,
    QGroupBox,
    QFormLayout,
    QGridLayout,
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
        self.image_preview.setObjectName("image_preview")
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
        self.setGeometry(400, 000, 700, 500)
        self.setWindowIcon(QIcon("assets/gui_icon.png"))
        self.video_path = None
        self.apply_global_styles()

        # Top level layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        # Feed preview
        self.preview = PreviewWindow(self)

        # Config generator panel
        self.control_panel = QWidget()
        self.control_panel.setLayout(QVBoxLayout())

        # Main params
        self.initln_path_select()
        self.initln_crop_points()
        self.initln_feed_details()

        #  Mode select
        self.initln_mode_select()

        #  Detection params
        self.initln_box_params()
        self.initln_box_stacking()
        self.initln_detection_params()

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
        self.path_select = QGroupBox("Path selection")
        self.path_select_layout = QFormLayout(self.path_select)

        path_select_input, self.fld_path_select, _ = self.create_labeled_field(
            "Feed path", objname="input_field"
        )

        self.btn_path_select = QPushButton(parent=self, text="Browse..")
        self.btn_path_select.setObjectName("browse_button")
        self.btn_path_select.clicked.connect(self.dialog_path_select)
        self.btn_path_select.clicked.connect(self.preview.update_image_preview)

        path_select_input.layout().addWidget(self.btn_path_select)
        self.path_select_layout.addRow(path_select_input)
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
        self.kernel_params = QGroupBox("Image region processing parameters")
        self.kernel_params_layout = QGridLayout(self.kernel_params)

        kernel_size, kernel_size_fld, kernel_size_lbl = self.create_labeled_field(
            "Kernel size", placeholder_text="10", objname="input_field"
        )
        dilation_iterations, dilation_iterations_fld, dilation_iterations_lbl = (
            self.create_labeled_field(
                "Dilation iterations", placeholder_text="2", objname="input_field"
            )
        )
        erosion_iterations, erosion_iterations_fld, erosion_iterations_lbl = (
            self.create_labeled_field(
                "Erosion iterations", placeholder_text="1", objname="input_field"
            )
        )

        self.kernel_params_layout.addWidget(kernel_size_lbl, 0, 0)
        self.kernel_params_layout.addWidget(kernel_size_fld, 0, 1)
        self.kernel_params_layout.addWidget(dilation_iterations_lbl, 0, 2)
        self.kernel_params_layout.addWidget(dilation_iterations_fld, 0, 3)
        self.kernel_params_layout.addWidget(erosion_iterations_lbl, 0, 4)
        self.kernel_params_layout.addWidget(erosion_iterations_fld, 0, 5)

        self.control_panel.layout().addWidget(self.kernel_params)

    def initln_box_stacking(self):
        self.box_stack_container = QGroupBox("Box stacking orientation")
        self.box_stack_container_layout = QHBoxLayout(self.box_stack_container)
        self.stack_group = QButtonGroup(self)
        self.stack_group.setExclusive(True)

        stack_mode_hor = QPushButton(parent=self, text="Horizontal")
        stack_mode_hor.setObjectName("orientation_button")
        stack_mode_hor.setCheckable(True)
        stack_mode_hor.setChecked(True)

        stack_mode_vert = QPushButton(parent=self, text="Vertical")
        stack_mode_hor.setObjectName("orientation_button")
        stack_mode_vert.setCheckable(True)

        stack_mode_diag = QPushButton(parent=self, text="Diagonal")
        stack_mode_hor.setObjectName("orientation_button")
        stack_mode_diag.setCheckable(True)

        self.stack_group.addButton(stack_mode_hor)
        self.stack_group.addButton(stack_mode_vert)
        self.stack_group.addButton(stack_mode_diag)

        self.box_stack_container_layout.addWidget(stack_mode_hor)
        self.box_stack_container_layout.addWidget(stack_mode_vert)
        self.box_stack_container_layout.addWidget(stack_mode_diag)

        self.control_panel.layout().addWidget(self.box_stack_container)

    def initln_box_params(self):
        self.box_params = QGroupBox("Detection zone configuration")
        box_params_layout = QGridLayout(self.box_params)

        quadrant_container, quadrant_fld, quadrant_label = self.create_labeled_field(
            "Quadrant", placeholder_text="1", objname="input_field"
        )
        num_boxes, num_boxes_fld, num_boxes_label = self.create_labeled_field(
            "Number of boxes", placeholder_text="10", objname="input_field"
        )
        box_size, box_size_fld, box_size_label = self.create_labeled_field(
            "Box size", placeholder_text="10"
        )
        start_from_box, start_from_box_fld, start_from_box_label = (
            self.create_labeled_field(
                "Start from box", placeholder_text="0", objname="input_field"
            )
        )
        trim_last_n, trim_last_n_fld, trim_last_n_label = self.create_labeled_field(
            "Trim last N boxes", placeholder_text="0", objname="input_field"
        )

        box_params_layout.addWidget(quadrant_label, 0, 0)
        box_params_layout.addWidget(quadrant_fld, 0, 1)
        box_params_layout.addWidget(num_boxes_label, 0, 2)
        box_params_layout.addWidget(num_boxes_fld, 0, 3)
        box_params_layout.addWidget(box_size_label, 0, 4)
        box_params_layout.addWidget(box_size_fld, 0, 5)
        box_params_layout.addWidget(start_from_box_label, 1, 0)
        box_params_layout.addWidget(start_from_box_fld, 1, 1)
        box_params_layout.addWidget(trim_last_n_label, 1, 2)
        box_params_layout.addWidget(trim_last_n_fld, 1, 3)

        self.control_panel.layout().addWidget(self.box_params)

    def initln_detection_params(self):
        self.detection_params = QGroupBox("Detection parameters")
        self.detection_params_layout = QGridLayout(self.detection_params)

        fb_size_container, fb_fld, fb_lbl = self.create_labeled_field(
            "Frame buffer size", "5", objname="input_field"
        )

        update_frequency_container, update_freq_fld, update_freq_lbl = (
            self.create_labeled_field("Update frequency", "2", objname="input_field")
        )

        (
            contrast_multiplier_container,
            contrast_multiplier_fld,
            contrast_multiplier_label,
        ) = self.create_labeled_field("Contrast multiplier", "1", objname="input_field")

        (
            threshold_multiplier_container,
            threshold_multiplier_fld,
            threshold_multiplier_label,
        ) = self.create_labeled_field(
            "Detection threshold multiplier", "1", objname="input_field"
        )

        self.detection_params_layout.addWidget(fb_lbl, 0, 0)
        self.detection_params_layout.addWidget(fb_fld, 0, 1)
        self.detection_params_layout.addWidget(update_freq_lbl, 0, 2)
        self.detection_params_layout.addWidget(update_freq_fld, 0, 3)
        self.detection_params_layout.addWidget(contrast_multiplier_label, 1, 0)
        self.detection_params_layout.addWidget(contrast_multiplier_fld, 1, 1)
        self.detection_params_layout.addWidget(threshold_multiplier_label, 1, 2)
        self.detection_params_layout.addWidget(threshold_multiplier_fld, 1, 3)

        self.control_panel.layout().addWidget(self.detection_params)

    def initln_feed_details(self):
        feed_details = QGroupBox("Basic feed parameters")
        feed_details_layout = QFormLayout(feed_details)

        id_container, id_field, id_label = self.create_labeled_field(
            "Run ID", placeholder_text="1", objname="input_field"
        )
        fps_container, fps_field, fps_label = self.create_labeled_field(
            "Feed FPS", placeholder_text="0", objname="input_field"
        )
        rpm_container, rpm_field, rpm_label = self.create_labeled_field(
            "Real RPM", placeholder_text="0", objname="input_field"
        )

        feed_details_layout.addRow(id_label, id_field)
        feed_details_layout.addRow(fps_label, fps_field)
        feed_details_layout.addRow(rpm_label, rpm_field)
        self.control_panel.layout().addWidget(feed_details)

    def initln_generate_config(self):
        config_button = QWidget()
        config_button_layout = QHBoxLayout(config_button)
        save_path_container, self.save_path_field, save_path_label = (
            self.create_labeled_field("Save as", placeholder_text="config.json")
        )

        btn = QPushButton(text="Generate config")
        btn.setObjectName("generate_config")
        btn.pressed.connect(self.generate_config)
        config_button_layout.addWidget(save_path_label)
        config_button_layout.addWidget(self.save_path_field)
        config_button_layout.addWidget(btn)
        self.control_panel.layout().addWidget(config_button)

    def generate_config(self):
        json_params = self.extract_params()
        json_params_sanitized = self.json_sanitize(json_params)

        file_loc = (
            self.save_path_field.text()
            if self.save_path_field.text() != ""
            else self.save_path_field.placeholderText()
        )

        with open(f"config/{file_loc}", "w", encoding="utf-8") as f:
            json.dump(json_params_sanitized, f, ensure_ascii=False, indent=4)

    def extract_params(self):
        items = self.findChildren(QLineEdit)
        items_dict = dict()
        for item in items:
            if item.text() != "":
                items_dict[item.property("label")] = item.text()
            else:
                items_dict[item.property("label")] = item.placeholderText()

        stack_method = self.stack_group.checkedButton().text()
        if stack_method == "Horizontal":
            items_dict["stack_boxes_vertically"] = False
            items_dict["stack_boxes_horizontally"] = True
        elif stack_method == "Vertical":
            items_dict["stack_boxes_vertically"] = True
            items_dict["stack_boxes_horizontally"] = False
        elif stack_method == "Diagonal":
            items_dict["stack_boxes_vertically"] = False
            items_dict["stack_boxes_horizontally"] = False

        mode = self.mode_group.checkedButton().text()
        if mode == "BPM":
            items_dict["mode"] = "bpm"
        else:
            items_dict["mode"] = "opticalflow"

        return items_dict

    def json_sanitize(self, args: dict) -> dict:
        args["crop_points"] = [
            [args["from y"], args["to y"]],
            [args["from x"], args["to x"]],
        ]
        del args["from y"]
        del args["to y"]
        del args["from x"]
        del args["to x"]
        remapped_args = {key_map.get(k, k): v for k, v in args.items()}
        remapped_args["resize_boxes"] = False
        remapped_args["adjust_num_boxes"] = False
        for item in remapped_args:
            if item == "target":
                remapped_args[item] = str(remapped_args[item])
                continue
            if (
                item == "contrast_multiplier"
                or item == "threshold_multiplier"
                or item == "fps"
                or item == "real_rpm"
            ):
                remapped_args[item] = float(remapped_args[item])
                continue
            if item == "crop_points":
                for pair in remapped_args[item]:
                    pair[0] = int(pair[0])
                    pair[1] = int(pair[1])
                continue
            if item == "stack_boxes_horizontally" or item == "stack_boxes_vertically":
                continue
            if item == "Save as":
                continue
            if item == "mode":
                continue
            if item == "erosion_dilation_kernel_size":
                remapped_args["erosion_dilation_kernel_size"] = [
                    int(float(remapped_args["erosion_dilation_kernel_size"])),
                    int(float(remapped_args["erosion_dilation_kernel_size"])),
                ]
                continue

            # We should have escaped all the baddies by now, so this is practically an else clause
            remapped_args[item] = int(float(remapped_args[item]))

        return remapped_args

    def initln_mode_select(self):
        bar = QGroupBox("RPM calculation mode")
        bar_layout = QHBoxLayout(bar)

        self.mode_group = QButtonGroup()

        bpm_mode = QPushButton(parent=self, text="BPM")
        bpm_mode.setCheckable(True)
        bpm_mode.setAutoExclusive(True)
        bpm_mode.setChecked(True)
        bpm_mode.setObjectName("mode_button")

        opticalflow_mode = QPushButton(parent=self, text="Optical flow")
        opticalflow_mode.setCheckable(True)
        opticalflow_mode.setAutoExclusive(True)
        opticalflow_mode.setObjectName("mode_button")

        self.mode_group.addButton(bpm_mode)
        self.mode_group.addButton(opticalflow_mode)

        bar_layout.addWidget(bpm_mode)
        bar_layout.addWidget(opticalflow_mode)

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

    def create_labeled_field(self, label_text, placeholder_text="", objname=None):
        container = QWidget()
        container.setLayout(QHBoxLayout())

        label = QLabel(parent=self, text=label_text)
        field = QLineEdit(placeholderText=placeholder_text)
        field.setProperty("label", label_text)

        container.layout().addWidget(label)
        container.layout().addWidget(field)

        if objname is not None:
            field.setObjectName(objname)

        return container, field, label

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
        self.coord_group = QGroupBox("Crop point selection")
        self.coord_layout = QGridLayout(self.coord_group)

        from_x, self.fld_from_x, _ = self.create_labeled_field(
            "from x", placeholder_text="0", objname="input_field"
        )
        to_x, self.fld_to_x, _ = self.create_labeled_field(
            "to x", placeholder_text="1000", objname="input_field"
        )
        from_y, self.fld_from_y, _ = self.create_labeled_field(
            "from y", placeholder_text="0", objname="input_field"
        )
        to_y, self.fld_to_y, _ = self.create_labeled_field(
            "to y", placeholder_text="1000", objname="input_field"
        )

        self.refresh_crop = QPushButton(parent=self, text="Refresh")
        self.refresh_crop.setObjectName("refresh_button")
        self.refresh_crop.clicked.connect(self.update_crop_points)

        self.coord_layout.addWidget(from_x, 0, 0)
        self.coord_layout.addWidget(self.fld_from_x, 0, 1)
        self.coord_layout.addWidget(to_x, 0, 2)
        self.coord_layout.addWidget(self.fld_to_x, 0, 3)
        self.coord_layout.addWidget(from_y, 1, 0)
        self.coord_layout.addWidget(self.fld_from_y, 1, 1)
        self.coord_layout.addWidget(to_y, 1, 2)
        self.coord_layout.addWidget(self.fld_to_y, 1, 3)

        self.coord_layout.addWidget(self.refresh_crop, 1, 4)
        self.control_panel.layout().addWidget(self.coord_group)

    def apply_global_styles(self):
        # Apply the stylesheet here
        self.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f9f9f9;
            font-size: 10pt;
        }

        /* Window title bar styling */
        QMainWindow::title {
            background-color: #333333;
            color: white;
        }

        /* Main container */
        QWidget#main_container {
            background-color: #f9f9f9;
            padding: 15px;
        }

        /* Section headings */
        QLabel.section_heading {
            font-weight: bold;
            color: #333333;
            font-size: 11pt;
            padding-top: 10px;
        }

        /* Group box styling */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            background-color: white;
            margin-top: 15px;
            padding-top: 15px;
            padding-bottom: 8px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #0078d7;
        }

        /* Input field styling */
        QLineEdit {
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            selection-background-color: #0078d7;
            min-height: 16px;
        }

        QLineEdit:focus {
            border: 1px solid #0078d7;
            background-color: #f0f7ff;
        }

        QLineEdit:disabled {
            background-color: #f0f0f0;
            color: #888888;
        }

        QLineEdit::placeholder {
            color: #aaaaaa;
        }

        /* Standard buttons */
        QPushButton {
            background-color: #0078d7;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-height: 16px;
        }

        QPushButton:hover {
            background-color: #106ebe;
        }

        QPushButton:pressed {
            background-color: #005a9e;
        }

        QPushButton:focus {
            outline: none;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #888888;
        }

        QPushButton:checked {
            background-color: #005a9e;
            border: 1px solid #0078d7;
        }

        /* Browse button */
        QPushButton#browse_button {
            background-color: #f0f0f0;
            color: #333333;
            border: 1px solid #d0d0d0;
            font-weight: normal;
        }

        QPushButton#browse_button:hover {
            background-color: #e0e0e0;
        }

        QPushButton#browse_button:pressed {
            background-color: #d0d0d0;
        }

        /* Generate config button */
        QPushButton#generate_config {
            background-color: #107c10;
            font-weight: bold;
            padding: 10px 20px;
        }

        QPushButton#generate_config:hover {
            background-color: #0b6a0b;
        }

        QPushButton#generate_config:pressed {
            background-color: #004b00;
        }

        /* Refresh button */
        QPushButton#refresh_button {
            background-color: #0078d7;
            padding: 8px 16px;
        }

        /* Toggle buttons / orientation buttons */
        QPushButton#orientation_button, 
        QPushButton[checkable="true"] {
            background-color: #f0f0f0;
            color: #333333;
            border: 1px solid #d0d0d0;
            padding: 6px 12px;
            font-weight: normal;
        }

        QPushButton#orientation_button:hover, 
        QPushButton[checkable="true"]:hover {
            background-color: #e0e0e0;
        }

        QPushButton#orientation_button:checked,
        QPushButton[checkable="true"]:checked {
            background-color: #0078d7;
            color: white;
            border: 1px solid #005a9e;
        }

        /* BPM/Optical flow toggle buttons */
        QPushButton#mode_button {
            padding: 10px 20px;
            font-size: 11pt;
        }

        QPushButton#mode_button:checked {
            background-color: #005a9e;
            border-bottom: 3px solid white;
        }

        /* Separator line */
        QFrame[frameShape="4"], 
        QFrame[frameShape="5"], 
        QFrame.separator_line {
            background-color: #e0e0e0;
            max-height: 1px;
            min-height: 1px;
            border: none;
        }

        /* Form layout spacing */
        QFormLayout {
            spacing: 12px;
        }

        /* Form field labels */
        QLabel.field_label, 
        QLabel {
            color: #333333;
            font-weight: 500;
        }

        /* Preview panel styling */
        QLabel#image_preview {
            background-color: white;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }

        /* Tooltips */
        QToolTip {
            background-color: #ffffdd;
            color: #333333;
            border: 1px solid #ddddcc;
            padding: 3px;
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
    key_map = {
        "Feed path": "target",
        "Feed FPS": "fps",
        "Real RPM": "real_rpm",
        "Quadrant": "quadrant",
        "Number of boxes": "target_num_boxes",
        "Box size": "target_box_size",
        "Start from box": "start_from_box",
        "Trim last N boxes": "trim_last_n_boxes",
        "Frame buffer size": "frame_buffer_size",
        "Update frequency": "color_delta_update_frequency",
        "Contrast multiplier": "contrast_multiplier",
        "Detection threshold multiplier": "threshold_multiplier",
        "Kernel size": "erosion_dilation_kernel_size",
        "Dilation iterations": "dilation_iterations",
        "Erosion iterations": "erosion_iterations",
        "Run ID": "id",
    }
    main()
