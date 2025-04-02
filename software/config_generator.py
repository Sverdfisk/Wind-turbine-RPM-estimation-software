import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QFileDialog
from PyQt6.QtGui import QIcon, QFont, QPixmap, QImage
import cv2


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Config Generator")
        self.setGeometry(400, 300, 700, 500)
        self.setWindowIcon(QIcon("../assets/gui_icon.png"))

        image_preview = QLabel(self)
        image_preview.setGeometry(345, 5, 350, 490)

        video = cv2.VideoCapture(
            "../assets/gtav_front_night_57f53_11r5025.mp4")
        _, frame = video.read()
        frame = QPixmap(convert_cvimg_to_qimg(frame))
        image_preview.setPixmap(frame)

        tf_path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select directory",
            directory=".",
            options=QFileDialog.Option.ShowDirsOnly,
        )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def convert_cvimg_to_qimg(cvImg):
    height, width, _ = cvImg.shape
    bytesPerLine = 3 * width
    qImg = QImage(cvImg.data, width, height, bytesPerLine,
                  QImage.Format.Format_RGB888)
    return qImg


if __name__ == "__main__":
    main()
