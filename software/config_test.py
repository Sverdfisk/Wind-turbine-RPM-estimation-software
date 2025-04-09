import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QFrame,
    QButtonGroup,
    QFileDialog,
    QGridLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt


class ConfigGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Config Generator")
        self.resize(800, 650)

        # Apply global stylesheet
        self.apply_global_styles()

        # Main widget and layout
        main_widget = QWidget()
        main_widget.setObjectName("main_container")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setCentralWidget(main_widget)

        # Feed path section
        feed_path_layout = QHBoxLayout()
        feed_path_label = QLabel("Feed path")
        feed_path_label.setObjectName("field_label")
        self.feed_path_input = QLineEdit()
        self.feed_path_input.setPlaceholderText("path...")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setObjectName("browse_button")
        self.browse_button.clicked.connect(self.browse_feed_path)

        feed_path_layout.addWidget(feed_path_label)
        feed_path_layout.addWidget(self.feed_path_input)
        feed_path_layout.addWidget(self.browse_button)
        main_layout.addLayout(feed_path_layout)

        # Coordinate range group
        coord_group = QGroupBox("Coordinate Range")
        coord_layout = QGridLayout(coord_group)

        # From X
        from_x_label = QLabel("From X")
        from_x_label.setObjectName("field_label")
        self.from_x_input = QLineEdit("0")
        coord_layout.addWidget(from_x_label, 0, 0)
        coord_layout.addWidget(self.from_x_input, 0, 1)

        # To X
        to_x_label = QLabel("To X")
        to_x_label.setObjectName("field_label")
        self.to_x_input = QLineEdit("1000")
        coord_layout.addWidget(to_x_label, 0, 2)
        coord_layout.addWidget(self.to_x_input, 0, 3)

        # From Y
        from_y_label = QLabel("From Y")
        from_y_label.setObjectName("field_label")
        self.from_y_input = QLineEdit("0")
        coord_layout.addWidget(from_y_label, 1, 0)
        coord_layout.addWidget(self.from_y_input, 1, 1)

        # To Y
        to_y_label = QLabel("To Y")
        to_y_label.setObjectName("field_label")
        self.to_y_input = QLineEdit("1000")
        coord_layout.addWidget(to_y_label, 1, 2)
        coord_layout.addWidget(self.to_y_input, 1, 3)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("refresh_button")
        coord_layout.addWidget(self.refresh_button, 1, 4)

        main_layout.addWidget(coord_group)

        # Basic parameters group
        basic_params_group = QGroupBox("Basic Parameters")
        basic_params_layout = QFormLayout(basic_params_group)

        self.run_id_input = QLineEdit("1")
        self.feed_fps_input = QLineEdit("0")
        self.real_rpm_input = QLineEdit("0")

        basic_params_layout.addRow(QLabel("Run ID"), self.run_id_input)
        basic_params_layout.addRow(QLabel("Feed FPS"), self.feed_fps_input)
        basic_params_layout.addRow(QLabel("Real RPM"), self.real_rpm_input)

        main_layout.addWidget(basic_params_group)

        # Processing mode selection
        mode_group = QGroupBox("Processing Mode")
        mode_layout = QHBoxLayout(mode_group)

        # Create a button group for mode selection
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)

        self.bpm_button = QPushButton("BPM")
        self.bpm_button.setObjectName("mode_button")
        self.bpm_button.setCheckable(True)
        self.bpm_button.setChecked(True)

        self.optical_flow_button = QPushButton("Optical Flow")
        self.optical_flow_button.setObjectName("mode_button")
        self.optical_flow_button.setCheckable(True)

        self.mode_btn_group.addButton(self.bpm_button)
        self.mode_btn_group.addButton(self.optical_flow_button)

        mode_layout.addWidget(self.bpm_button)
        mode_layout.addWidget(self.optical_flow_button)

        main_layout.addWidget(mode_group)

        # Detection Zone Configuration
        detection_group = QGroupBox("Detection Zone Configuration")
        detection_layout = QGridLayout(detection_group)

        # Row 1
        detection_layout.addWidget(QLabel("Quadrant"), 0, 0)
        self.quadrant_input = QLineEdit("1")
        detection_layout.addWidget(self.quadrant_input, 0, 1)

        detection_layout.addWidget(QLabel("Number of boxes"), 0, 2)
        self.num_boxes_input = QLineEdit("10")
        detection_layout.addWidget(self.num_boxes_input, 0, 3)

        detection_layout.addWidget(QLabel("Box size"), 0, 4)
        self.box_size_input = QLineEdit("10")
        detection_layout.addWidget(self.box_size_input, 0, 5)

        # Row 2
        detection_layout.addWidget(QLabel("Start from box"), 1, 0)
        self.start_box_input = QLineEdit("0")
        detection_layout.addWidget(self.start_box_input, 1, 1)

        detection_layout.addWidget(QLabel("Trim last N boxes"), 1, 2)
        self.trim_boxes_input = QLineEdit("0")
        detection_layout.addWidget(self.trim_boxes_input, 1, 3)

        # Stack boxes orientation
        stack_box_group = QGroupBox("Stack Boxes Orientation")
        stack_box_layout = QHBoxLayout(stack_box_group)

        self.stack_orientation_group = QButtonGroup(self)
        self.stack_orientation_group.setExclusive(True)

        self.horizontal_btn = QPushButton("Horizontal")
        self.horizontal_btn.setObjectName("orientation_button")
        self.horizontal_btn.setCheckable(True)
        self.horizontal_btn.setChecked(True)

        self.vertical_btn = QPushButton("Vertical")
        self.vertical_btn.setObjectName("orientation_button")
        self.vertical_btn.setCheckable(True)

        self.diagonal_btn = QPushButton("Diagonal")
        self.diagonal_btn.setObjectName("orientation_button")
        self.diagonal_btn.setCheckable(True)

        self.stack_orientation_group.addButton(self.horizontal_btn)
        self.stack_orientation_group.addButton(self.vertical_btn)
        self.stack_orientation_group.addButton(self.diagonal_btn)

        stack_box_layout.addWidget(self.horizontal_btn)
        stack_box_layout.addWidget(self.vertical_btn)
        stack_box_layout.addWidget(self.diagonal_btn)

        detection_layout.addWidget(stack_box_group, 2, 0, 1, 6)

        main_layout.addWidget(detection_group)

        # Processing parameters
        processing_group = QGroupBox("Processing Parameters")
        processing_layout = QGridLayout(processing_group)

        # Row 1
        processing_layout.addWidget(QLabel("Frame buffer size"), 0, 0)
        self.frame_buffer_input = QLineEdit("5")
        processing_layout.addWidget(self.frame_buffer_input, 0, 1)

        processing_layout.addWidget(QLabel("Update frequency"), 0, 2)
        self.update_freq_input = QLineEdit("2")
        processing_layout.addWidget(self.update_freq_input, 0, 3)

        # Row 2
        processing_layout.addWidget(QLabel("Contrast multiplier"), 1, 0)
        self.contrast_input = QLineEdit("1")
        processing_layout.addWidget(self.contrast_input, 1, 1)

        processing_layout.addWidget(QLabel("Detection threshold"), 1, 2)
        self.detection_input = QLineEdit("1")
        processing_layout.addWidget(self.detection_input, 1, 3)

        main_layout.addWidget(processing_group)

        # Advanced parameters
        advanced_group = QGroupBox("Advanced Parameters")
        advanced_layout = QGridLayout(advanced_group)

        advanced_layout.addWidget(QLabel("Kernel size"), 0, 0)
        self.kernel_input = QLineEdit("10")
        advanced_layout.addWidget(self.kernel_input, 0, 1)

        advanced_layout.addWidget(QLabel("Dilation iterations"), 0, 2)
        self.dilation_input = QLineEdit("2")
        advanced_layout.addWidget(self.dilation_input, 0, 3)

        advanced_layout.addWidget(QLabel("Erosion iterations"), 1, 0)
        self.erosion_input = QLineEdit("1")
        advanced_layout.addWidget(self.erosion_input, 1, 1)

        main_layout.addWidget(advanced_group)

        # Save configuration
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("Save as"))
        self.save_filename_input = QLineEdit("config.json")
        save_layout.addWidget(self.save_filename_input)

        self.generate_btn = QPushButton("Generate Config")
        self.generate_btn.setObjectName("generate_config")
        save_layout.addWidget(self.generate_btn)

        main_layout.addLayout(save_layout)

        # Add stretch to push everything up
        main_layout.addStretch()

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

        /* Radio buttons styled as toggle buttons */
        QPushButton#orientation_button {
            background-color: #f0f0f0;
            color: #333333;
            border: 1px solid #d0d0d0;
            padding: 6px 12px;
            font-weight: normal;
        }

        QPushButton#orientation_button:hover {
            background-color: #e0e0e0;
        }

        QPushButton#orientation_button:checked {
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
        QLabel.field_label {
            color: #555555;
        }

        /* Tooltips */
        QToolTip {
            background-color: #ffffdd;
            color: #333333;
            border: 1px solid #ddddcc;
            padding: 3px;
        }
        """)

    def browse_feed_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Feed File", "", "All Files (*)"
        )
        if file_path:
            self.feed_path_input.setText(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigGenerator()
    window.show()
    sys.exit(app.exec())
