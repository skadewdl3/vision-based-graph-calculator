# Add these imports at the top of the file
from ..model.load import load_model
from ..utils import BUILD_DIR, SCREENSHOT
import os
from torchvision import transforms
from PIL import Image
import pyautogui
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QPoint, QRect
import torch
from ..dataset import IM2LatexDataset

class SnippingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet('background-color: rgba(0, 0, 0, 100);')
        self.setGeometry(QApplication.desktop().geometry())

        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.dataset = IM2LatexDataset(split='train')

    def paintEvent(self, event):
        if self.is_snipping:
            brush_color = QColor(0, 0, 0, 0)
            lw = 3
            opacity = 0.3
        else:
            brush_color = QColor(100, 100, 100, 100)
            lw = 0
            opacity = 0.3

        self.setWindowOpacity(opacity)
        qp = QPainter(self)
        qp.setPen(QPen(Qt.red, lw, Qt.SolidLine))
        qp.setBrush(brush_color)
        qp.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_snipping = False
        self.capture_screen()
        self.close()

    def capture_screen(self):
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        img = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        img.save(os.path.join(BUILD_DIR, SCREENSHOT))
        print("Screenshot saved as 'screenshot.png'")

        # Perform OCR on the captured image
        model, tokenizer = load_model()
        model.eval()

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
        ])

        image = Image.open(os.path.join(BUILD_DIR, SCREENSHOT)).convert('L')
        image = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(image)

        #Added following lines
        predicted_indices = torch.argmax(output, dim=-1)
        result = tokenizer.decode(predicted_indices.squeeze().tolist(), skip_special_tokens=True)
        print("Recognized formula:", result)
