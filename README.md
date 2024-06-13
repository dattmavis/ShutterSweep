
# Shutter Sweep

Shutter Sweep is a lightweight photo culling application designed to help photographers quickly review and manage their photos. Unlike heavy-handed tools like Lightroom, Shutter Sweep offers a simple and intuitive interface, allowing users to easily select, delete, and even upload their photos to Google Photos. This tool is particularly useful for photographers who shoot in RAW + JPEG mode and need a streamlined process to manage both file types simultaneously - especially in regards to culling. Once a JPEG is deleted, it's corresponding RAW file pair is deleted automatically. 

## Features

- **Photo Review and Management**: View and manage your photos with a simple and intuitive interface.
- **Thumbnail Carousel**: Browse through a carousel of photo thumbnails for quick selection.
- **EXIF Data Display**: View detailed EXIF data for each photo. Quick at a glance info, with more details a click away.
- **Image Manipulation**: Rotate, zoom in, and zoom out of photos. Check focus in certain spots to find keepers.
- **Batch Operations**: Multi-Select, Select All, Delete Selected, and Upload Selected Photos.
- **RAW + JPEG Handling**: Automatically manage RAW + JPEG pairs.
- **Google Photos Integration**: Upload selected photos directly to Google Photos using OAuth 2.0 authentication.


## Screenshots



## Technologies Used

### Python

The core logic of Shutter Sweep is implemented in Python, leveraging its rich ecosystem of libraries and frameworks.

### PyQt5

PyQt5 is used to create the graphical user interface (GUI). It provides a wide range of tools to build a user-friendly and responsive application.

- **QMainWindow**: The main window of the application.
- **QGraphicsScene and QGraphicsView**: To display and manipulate images.
- **QListWidget**: To display a carousel of photo thumbnails.
- **QVBoxLayout, QHBoxLayout, QGridLayout**: To arrange widgets within the application.

### exif Library

The `exif` library is used to extract EXIF metadata from images, providing valuable information such as camera model, lens information, aperture, ISO, shutter speed, and date.

### Google Photos API

The Google Photos API allows the application to upload selected photos to Google Photos. This integration is handled through the following:

- **google-auth and google-auth-oauthlib**: For OAuth 2.0 authentication.
- **google-api-python-client**: To interact with the Google Photos API.

### Multithreading

The application uses multithreading to handle image loading in the background, ensuring a smooth and responsive user experience.

## Installation

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/yourusername/shutter-sweep.git
   cd shutter-sweep`` 

2.  **Install Dependencies**:
    
    sh
    
    Copy code
    
    `pip install -r requirements.txt` 
    
3.  **Set Up Google Cloud Project**:
    
    -   Create a project in the Google Cloud Console.
    -   Enable the Google Photos Library API.
    -   Create OAuth 2.0 credentials and download the client secret JSON file.
    -   Save the credentials file as `oauth.json` in the project directory.
4.  **Run the Application**:
    
    sh
    
    Copy code
    
    `python ShutterSweep.py` 
    

## Usage

1.  **Open Directory**: Click the "Open Directory" button to select a folder containing your photos.
2.  **Thumbnail Carousel**: Browse through the thumbnails to view and select photos.
3.  **Image Manipulation**: Use the provided buttons to rotate, zoom in, and zoom out of the selected image.
4.  **Select All**: Click the "Select All" button to select all photos in the carousel.
5.  **Delete Selected**: Select the photos you want to delete and click the "Delete Selected" button.
6.  **Upload to Google Photos**: Select the photos you want to upload and click the "Upload Selected to Google Photos" button. Authenticate with your Google account to complete the upload.

## Concepts Demonstrated

### Python Programming

-   Developed a fully functional desktop application using Python.
-   Utilized object-oriented programming principles for better code organization and maintainability.

### PyQt5 for GUI Development

-   Created a responsive and user-friendly interface with PyQt5.
-   Managed layout and widgets for a seamless user experience.

### EXIF Data Extraction

-   Extracted and displayed EXIF metadata from images using the `exif` library.

### Google Photos API Integration

-   Implemented OAuth 2.0 authentication to securely access Google Photos.
-   Utilized Google Photos API to upload images directly from the application.

### Multithreading

-   Used multithreading to load images in the background, ensuring the main application remains responsive.

### File Management

-   Handled the management of RAW + JPEG pairs, ensuring both files are managed together to prevent inconsistencies.

## License

This project is licensed under the MIT License. 

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your suggestions and improvements.

## Acknowledgements

-   Thanks to the maintainers of the `exif`, `PyQt5`, and `google-api-python-client` libraries for their excellent work.

----------

Feel free to explore the code, suggest improvements, or use Shutter Sweep to simplify your photo culling process. This project showcases a blend of GUI development, API integration, and effective file management, all aimed at creating a practical tool for photographers.
