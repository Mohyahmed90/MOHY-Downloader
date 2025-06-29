# 🌟 MOHY DOWNLOADER 🌟

A simple yet powerful tool to clip and download segments from YouTube videos with high accuracy and multiple language support.

---

<div align="center">

  ![MOHY_DOWNLOADER](https://github.com/user-attachments/assets/ee5bad55-78ad-454d-af0e-59b78743b813)
 

</div>

---

## ✨ Features

- **✅ Interactive Time Selection:** Easily select start/end times with sliders and interactive `+/-` buttons.
- **🌍 Multi-Language Support:** Full UI translation for Arabic, English, German, and Spanish.
- **🎯 High Accuracy Mode:** A special mode to re-encode video for frame-perfect clips, fixing any freezing or black screen issues.
- **🎬 All Qualities Supported:** From 1080p to 360p, including Audio-Only downloads.
- **✍️ Smart Filename:** Automatically suggests the video title as the filename.
- **💾 Saves User Preferences:** Remembers your last used save folder and language.
- **📋 Paste Button:** Instantly paste links from your clipboard.
- **🍪 Cookie Support:** Allows using a `cookies.txt` file for private videos and improved stability.

---

## 🚀 Getting Started

### 1. Download FFmpeg (Required First Step)
This program requires **FFmpeg** to function correctly.
- **Download Link:** Get it from the official site: **[ffmpeg.org](https://ffmpeg.org/download.html)**
- **Installation Tutorial:** This short YouTube video clearly explains how to download and install FFmpeg and add it to the Windows PATH: **(https://www.youtube.com/watch?v=K7znsMo_48I)**
- *You must add FFmpeg to your system's PATH for the program to find and use it.*

---

### 2. Configure Cookies (Essential for Stability)
For the best performance, stability, and to access private or age-restricted content, using a cookies file is **essential**.

**Why is it essential?**
- It ensures the program can access YouTube with a valid, logged-in session, preventing many potential errors.
- **Important:** YouTube cookies expire frequently. You must refresh your cookie file regularly.

#### Recommended Tool: Automated Cookie Exporter
The best way to manage your cookies is with a browser extension that automates the process. I strongly recommend **[youtube-cookies-exporter](https://github.com/reiarseni/youtube-cookies-exporter)** by reiarseni.

**How it works automatically:**
This extension simplifies the process. After the initial setup, you only need to click one button in the extension to automatically update your saved `cookies.txt` file with fresh cookies.

1.  **Install the Extension:**
    *   [**Chrome/Edge/Brave**](https://chrome.google.com/webstore/detail/youtube-cookies-exporter/tccgjnpatnefhdjgcfigpambkmememca)
    *   [**Firefox**](https://addons.mozilla.org/en-US/firefox/addon/youtube-cookies-exporter/)

2.  **One-Time Setup:**
    *   Click the extension's icon in your browser's toolbar and go to its settings.
    *   Set the "Filename" to `cookies.txt`.
    *   Choose the folder where you want to save the file.
    *   Click "Save".

3.  **Using it:**
    *   Whenever you need to refresh your cookies, just go to `youtube.com`, click the extension's icon, and click **"Export Cookies"**. The file will be updated automatically in the location you chose.
    *   In MOHY Downloader, click the "Select Cookie File" button and choose the `cookies.txt` file you saved.

---

### 3. Download and Run MOHY Downloader

- Go to the [**Releases Page**](https://github.com/your-username/your-repo-name/releases).
- Download the `MOHY_Downloader_Setup.exe` file from the latest release.
- Run the installer.

### ⚠️ **Important: Run as Administrator**
To avoid any permission issues, especially when saving files, it is **required** to run the program as an administrator.

- **Right-click** on the MOHY Downloader desktop shortcut.
- Select **"Run as administrator"**.

---

## 👨‍💻 For Developers

If you want to run the project from the source code:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ensure FFmpeg is in your system's PATH.**

4.  **Run the script:**
    ```bash
    python MOHY_Downloader_Final.py
    ```
    
---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/your-username/your-repo-name/blob/main/LICENSE) file for details.
