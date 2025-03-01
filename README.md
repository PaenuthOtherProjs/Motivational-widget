# Motivational Widget

A lightweight, customizable desktop widget that displays a slideshow of images from a folder of your choice. Perfect for motivational quotes, inspirational images, or personal photos that keep you focused throughout your day.

## ✨ Features

- **Image Slideshow**: Display images from any folder with customizable timing
- **Sleek Interface Options**:
  - Borderless mode with custom title bar
  - Dark/light theme options 
  - Always-on-top capability
- **User-friendly Controls**:
  - Position lock to prevent accidental movement
  - Minimize to taskbar
  - Right-click menu for all settings
- **Windows Integration**:
  - Add to startup for automatic launch at Windows login
  - Save position and settings between sessions

## 🚀 Installation

### Download Executable (Recommended)
1. Download the latest release from the [Releases](https://github.com/PaenuthOtherProjs/Motivational-widget/releases) section
2. Scroll down to "Assets" and click the "MotivationWidget.exe" to download.
3. Run the executable file - no installation needed!
4. Note: This program is safe and secure. You may scan it with your preferred anti-virus software to check.

### Run from Source
1. Clone this repository
   ```bash
   git clone https://github.com/PaenuthOtherProjs/Motivational-widget.git
   cd Motivational-widget
   ```

2. Install required packages
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application
   ```bash
   python motivation_widget.py
   ```

## 📖 Usage

1. **First Launch**: On first launch, you'll have to right click inside the widget and select a folder containing images
2. **Image Selection**: Choose any folder with JPG, PNG, GIF, or BMP images
3. **Settings**:
   - Right-click on the widget to access all settings
   - Left-click and drag the title bar to move the widget (when position is unlocked)

### Menu Options

| Option | Description |
|--------|-------------|
| Select Folder | Choose a folder containing your images |
| Set Duration | Change how long each image is displayed (seconds) |
| Always on Top | Keep the widget visible above other windows |
| Lock Position | Prevent accidental movement |
| Dark Mode | Toggle between light and dark themes |
| Borderless Mode | Toggle window borders |
| Run at Startup | Set to run automatically when you log in |

## ⚙️ Configuration

Settings are automatically saved to `%USERPROFILE%\motivation_widget_config.json` and loaded on startup.

## 🖥️ System Requirements

- Windows 7 or higher
- Python 3.7+ (if running from source)
- Not tested on other OS

## 🤝 Contributing

Contributions are welcome! Please check the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Python](https://www.python.org/) and [Tkinter](https://docs.python.org/3/library/tkinter.html)
