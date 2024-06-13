import sys
import os
from exif import Image
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
    QGraphicsPixmapItem, QFileDialog, QVBoxLayout, QWidget, 
    QPushButton, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox,
    QLabel, QShortcut, QDialog, QScrollArea, QDialogButtonBox, QCheckBox, QGridLayout, QListView, QProgressBar
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from fractions import Fraction
import warnings
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_photos_auth import get_credentials
from concurrent.futures import ThreadPoolExecutor

class ImageLoader(QThread):
    image_loaded = pyqtSignal(str, QPixmap)
    progress_update = pyqtSignal(int)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        images = [os.path.join(self.directory, f) for f in os.listdir(self.directory) if f.lower().endswith('.jpg')]
        total_images = len(images)
        with ThreadPoolExecutor(max_workers=8) as executor:
            for idx, result in enumerate(executor.map(self.load_image, images)):
                image_path, thumbnail = result
                self.image_loaded.emit(image_path, thumbnail)
                progress = int((idx + 1) / total_images * 100)
                self.progress_update.emit(progress)

    def load_image(self, image_path):
        thumbnail = QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return image_path, thumbnail

class ExifDialog(QDialog):
    def __init__(self, exif_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Full EXIF Info")
        self.setGeometry(200, 200, 400, 600)
        layout = QVBoxLayout(self)

        scroll_area = QScrollArea(self)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for tag, value in exif_data.items():
            scroll_layout.addWidget(QLabel(f"{tag}: {value}"))

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

class ImageCuller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shutter Sweep")
        self.setGeometry(100, 100, 1000, 700)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setAlignment(Qt.AlignCenter)

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        layout = QVBoxLayout()
        layout.addWidget(self.view)

        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("<< Prev")
        self.prev_button.clicked.connect(self.prev_image)
        controls_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next >>")
        self.next_button.clicked.connect(self.next_image)
        controls_layout.addWidget(self.next_button)

        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(lambda: self.view.scale(1.25, 1.25))
        controls_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(lambda: self.view.scale(0.8, 0.8))
        controls_layout.addWidget(self.zoom_out_button)

        self.rotate_left_button = QPushButton("Rotate Left")
        self.rotate_left_button.clicked.connect(lambda: self.rotate_image(-90))
        controls_layout.addWidget(self.rotate_left_button)

        self.rotate_right_button = QPushButton("Rotate Right")
        self.rotate_right_button.clicked.connect(lambda: self.rotate_image(90))
        controls_layout.addWidget(self.rotate_right_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_image)
        controls_layout.addWidget(self.delete_button)

        self.delete_selected_button = QPushButton("Delete Selected")
        self.delete_selected_button.clicked.connect(self.delete_selected_images)
        controls_layout.addWidget(self.delete_selected_button)

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_images)
        controls_layout.addWidget(self.select_all_button)

        layout.addLayout(controls_layout)

        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListWidget.IconMode)
        self.thumbnail_list.setIconSize(QSize(100, 100))
        self.thumbnail_list.setSpacing(10)
        self.thumbnail_list.setMovement(QListWidget.Static)
        self.thumbnail_list.setResizeMode(QListWidget.Adjust)
        self.thumbnail_list.setFlow(QListView.LeftToRight)
        self.thumbnail_list.setWrapping(False)
        self.thumbnail_list.setSelectionMode(QListWidget.NoSelection)
        self.thumbnail_list.setMaximumHeight(120)  # Adjust the height of the thumbnail list
        self.thumbnail_list.itemClicked.connect(lambda item: self.on_thumbnail_click(item))

        thumbnail_container = QHBoxLayout()
        thumbnail_container.addWidget(self.thumbnail_list)

        layout.addLayout(thumbnail_container)

        self.loading_label = QLabel("Please wait while images are loaded...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        right_layout = QVBoxLayout()
        exif_layout = QVBoxLayout()
        self.exif_label = QLabel()
        self.exif_label.setWordWrap(True)
        exif_layout.addWidget(self.exif_label)

        self.exif_link = QLabel('<a href="#">Full EXIF Info</a>')
        self.exif_link.setOpenExternalLinks(False)
        self.exif_link.linkActivated.connect(self.show_full_exif)
        self.exif_link.setVisible(False)
        exif_layout.addWidget(self.exif_link)

        right_layout.addLayout(exif_layout)

        button_layout = QVBoxLayout()
        self.open_button = QPushButton("Open Directory")
        self.open_button.clicked.connect(self.open_directory)
        button_layout.addWidget(self.open_button)

        self.upload_button = QPushButton("Upload Selected to Google Photos")
        self.upload_button.clicked.connect(self.upload_selected_images)
        button_layout.addWidget(self.upload_button)

        right_layout.addLayout(button_layout)
        right_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(right_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.images = []
        self.current_image_index = -1
        self.current_image_exif = {}

        self.set_shortcuts()

    def set_shortcuts(self):
        self.shortcut_next = QShortcut(Qt.Key_Right, self)
        self.shortcut_next.activated.connect(self.next_image)

        self.shortcut_prev = QShortcut(Qt.Key_Left, self)
        self.shortcut_prev.activated.connect(self.prev_image)

        self.shortcut_zoom_in = QShortcut(Qt.Key_Plus, self)
        self.shortcut_zoom_in.activated.connect(lambda: self.view.scale(1.25, 1.25))

        self.shortcut_zoom_out = QShortcut(Qt.Key_Minus, self)
        self.shortcut_zoom_out.activated.connect(lambda: self.view.scale(0.8, 0.8))

        self.shortcut_select = QShortcut(Qt.Key_Space, self)
        self.shortcut_select.activated.connect(self.toggle_select_current_image)

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            # Clear previous images and reset
            self.images.clear()
            self.current_image_index = -1
            self.thumbnail_list.clear()
            self.pixmap_item.setPixmap(QPixmap())
            self.loading_label.setVisible(True)
            self.progress_bar.setVisible(True)
            
            self.loader_thread = ImageLoader(directory)
            self.loader_thread.image_loaded.connect(self.add_thumbnail)
            self.loader_thread.progress_update.connect(self.update_progress)
            self.loader_thread.finished.connect(self.loading_finished)
            self.loader_thread.start()

    def add_thumbnail(self, image_path, thumbnail):
        item_widget = QWidget()
        item_layout = QGridLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(0)

        icon_label = QLabel()
        icon_label.setPixmap(thumbnail)
        icon_label.mousePressEvent = lambda event, img_path=image_path: self.on_thumbnail_click_path(img_path)
        item_layout.addWidget(icon_label, 0, 0)

        checkbox = QCheckBox()
        checkbox.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
        item_layout.addWidget(checkbox, 0, 1, Qt.AlignTop | Qt.AlignRight)

        item_widget.setLayout(item_layout)

        item = QListWidgetItem(self.thumbnail_list)
        item.setSizeHint(item_widget.sizeHint())
        self.thumbnail_list.setItemWidget(item, item_widget)
        item.setData(Qt.UserRole, image_path)

        self.images.append(image_path)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def loading_finished(self):
        self.loading_label.setVisible(False)
        self.progress_bar.setVisible(False)
        if self.images:
            self.current_image_index = 0
            self.display_current_image()
        else:
            self.pixmap_item.setPixmap(QPixmap())

    def display_current_image(self):
        if 0 <= self.current_image_index < len(self.images):
            self.display_image(self.images[self.current_image_index])
        else:
            self.pixmap_item.setPixmap(QPixmap())

    def display_image(self, image_path):
        image = QImage(image_path)
        pixmap = QPixmap.fromImage(image)
        self.pixmap_item.setPixmap(pixmap)
        self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        self.load_exif_data(image_path)
        self.exif_link.setVisible(True)

    def load_exif_data(self, image_path):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with open(image_path, 'rb') as img_file:
                    img = Image(img_file)

            exif_data = {
                "Camera": img.get("model", "Unknown"),
                "Lens": f"{img.get('lens_model', 'Unknown')} {img.get('lens_make', '')}".strip(),
                "Aperture": f"f/{img.get('f_number', 'Unknown')}",
                "ISO": img.get("photographic_sensitivity", "Unknown"),
                "Shutter Speed": self.format_shutter_speed(img.get('exposure_time', 'Unknown')),
                "Date": self.format_datetime(img.get("datetime_original", "Unknown"))
            }

            self.current_image_exif = exif_data
            self.update_exif_label()
        except Exception as e:
            print(f"Error reading EXIF data: {e}")

    def format_shutter_speed(self, shutter_speed):
        try:
            return f"1/{int(1 / float(shutter_speed))}"
        except Exception:
            return shutter_speed

    def format_datetime(self, datetime_str):
        try:
            dt = datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %I:%M:%S %p")
        except ValueError:
            return datetime_str

    def update_exif_label(self):
        exif_text = "\n".join([f"{key}: {value}" for key, value in self.current_image_exif.items()])
        self.exif_label.setText(exif_text)

    def show_full_exif(self):
        if self.current_image_exif:
            try:
                with open(self.images[self.current_image_index], 'rb') as img_file:
                    img = Image(img_file)
                exif_data = {tag: img.get(tag) for tag in img.list_all() if img.get(tag) is not None}
                exif_dialog = ExifDialog(exif_data, self)
                exif_dialog.exec_()
            except Exception as e:
                print(f"Error showing full EXIF data: {e}")

    def on_thumbnail_click_path(self, image_path):
        self.current_image_index = self.images.index(image_path)
        self.display_current_image()

    def toggle_select_current_image(self):
        if 0 <= self.current_image_index < len(self.images):
            current_item = self.thumbnail_list.item(self.current_image_index)
            checkbox = self.thumbnail_list.itemWidget(current_item).findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())

    def next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.display_current_image()

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_current_image()

    def rotate_image(self, angle):
        self.pixmap_item.setRotation(self.pixmap_item.rotation() + angle)
        self.view.resetTransform()
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def delete_image(self):
        if 0 <= self.current_image_index < len(self.images):
            jpg_path = self.images[self.current_image_index]
            reply = QMessageBox.question(self, 'Delete Image', f"Are you sure you want to delete {os.path.basename(jpg_path)}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.images.pop(self.current_image_index)
                self.delete_raw_pairs(jpg_path)
                try:
                    os.remove(jpg_path)
                    self.display_current_image()
                except FileNotFoundError:
                    print(f"File not found: {jpg_path}")
                    self.display_current_image()
            self.load_images(os.path.dirname(jpg_path))

    def delete_raw_pairs(self, image_path):
        raw_extensions = ['.RAF', '.NEF', '.CR2', '.ARW', '.ORF', '.RW2', '.PEF']
        base_name = os.path.splitext(image_path)[0]
        for ext in raw_extensions:
            raw_path = base_name + ext
            if os.path.exists(raw_path):
                os.remove(raw_path)

    def delete_selected_images(self):
        selected_items = [self.thumbnail_list.item(i) for i in range(self.thumbnail_list.count())]
        items_to_delete = [item for item in selected_items if self.thumbnail_list.itemWidget(item).findChild(QCheckBox).isChecked()]

        if not items_to_delete:
            return

        reply = QMessageBox.question(self, 'Delete Selected Images', "Are you sure you want to delete the selected images?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for item in items_to_delete:
                image_path = item.data(Qt.UserRole)
                self.images.remove(image_path)
                self.delete_raw_pairs(image_path)
                try:
                    os.remove(image_path)
                except FileNotFoundError:
                    print(f"File not found: {image_path}")
            self.load_images(os.path.dirname(image_path))

    def select_all_images(self):
        for i in range(self.thumbnail_list.count()):
            item = self.thumbnail_list.item(i)
            checkbox = self.thumbnail_list.itemWidget(item).findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(True)

    def upload_selected_images(self):
        selected_items = [self.thumbnail_list.item(i) for i in range(self.thumbnail_list.count())]
        items_to_upload = [item for item in selected_items if self.thumbnail_list.itemWidget(item).findChild(QCheckBox).isChecked()]

        if not items_to_upload:
            QMessageBox.information(self, 'Upload Images', "No images selected for upload.")
            return

        creds = get_credentials()
        try:
            service = build('photoslibrary', 'v1', credentials=creds, discoveryServiceUrl='https://photoslibrary.googleapis.com/$discovery/rest?version=v1')
        except Exception as e:
            QMessageBox.critical(self, 'Google Photos API Error', f"Failed to build service: {e}")
            return

        for item in items_to_upload:
            image_path = item.data(Qt.UserRole)
            upload_token = self.upload_image_bytes(service, image_path)
            if upload_token:
                self.create_media_item(service, upload_token, os.path.basename(image_path))

                # Upload associated RAW pairs
                raw_extensions = ['.RAF', '.NEF', '.CR2', '.ARW', '.ORF', '.RW2', '.PEF']
                base_name = os.path.splitext(image_path)[0]
                for ext in raw_extensions:
                    raw_path = base_name + ext
                    if os.path.exists(raw_path):
                        raw_upload_token = self.upload_image_bytes(service, raw_path)
                        if raw_upload_token:
                            self.create_media_item(service, raw_upload_token, os.path.basename(raw_path))

        QMessageBox.information(self, 'Upload Images', "Selected images and their RAW pairs have been uploaded to Google Photos.")

    def upload_image_bytes(self, service, image_path):
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            headers = {
                'Content-type': 'application/octet-stream',
                'X-Goog-Upload-Content-Type': 'image/jpeg' if image_path.lower().endswith('.jpg') else 'image/raw',
                'X-Goog-Upload-Protocol': 'raw',
            }

            upload_response = service._http.request(
                uri='https://photoslibrary.googleapis.com/v1/uploads',
                method='POST',
                body=image_data,
                headers=headers
            )

            upload_token = upload_response[1].decode('utf-8')
            return upload_token

        except Exception as e:
            print(f"Error uploading image {image_path}: {e}")
            return None

    def create_media_item(self, service, upload_token, file_name):
        try:
            new_item = {
                'newMediaItems': [
                    {
                        'description': file_name,
                        'simpleMediaItem': {
                            'uploadToken': upload_token
                        }
                    }
                ]
            }
            service.mediaItems().batchCreate(body=new_item).execute()
        except Exception as e:
            print(f"Error creating media item for {file_name}: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageCuller()
    window.show()
    sys.exit(app.exec_())
