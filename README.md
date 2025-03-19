# 🎵 Audio Processing & Sentiment Analysis

## 📌 Overview
This project processes audio files by uploading them to a MySQL database, converting them into different formats, and analyzing sentiment using **NLTK**. It also supports basic CRUD operations for audio storage and retrieval.

## ⚙️ Features
- Upload audio files to a **MySQL database**.
- Convert audio formats using **Pydub**.
- Perform **sentiment analysis** using **VADER**.
- Fetch and process audio stored in the database.
- Supports **MP3, WAV, OGG**, and other formats.

## 📂 Project Structure
```
├── downloaded_audio/       # Directory for downloaded audio files
├── main.py                 # Entry point of the application
├── app.py                  # Handles audio processing
├── database.py             # Manages MySQL database operations
├── requirements.txt        # Dependencies
├── README.md               # Project Documentation
```

## 🛠 Installation & Setup
### 1️⃣ **Clone the Repository**
```sh
git clone https://github.com/yourusername/audio-processing.git
cd audio-processing
```

### 2️⃣ **Create & Activate Virtual Environment** (Optional but Recommended)
```sh
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows
```

### 3️⃣ **Install Dependencies**
```sh
pip install -r requirements.txt
```

### 4️⃣ **Setup MySQL Database**
1. **Start MySQL Server**
2. **Create Database & Table**
```sql
CREATE DATABASE audio_db;
USE audio_db;

CREATE TABLE audio_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_data LONGBLOB NOT NULL
);
```
3. **Update `database.py` with your MySQL credentials.**

### 5️⃣ **Ensure `ffmpeg` is Installed** (Required for Audio Processing)
```sh
ffmpeg -version
```
- If not installed:
  - **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to PATH.
  - **Mac/Linux**: Install via Homebrew or APT:
    ```sh
    brew install ffmpeg  # Mac
    sudo apt install ffmpeg  # Ubuntu/Debian
    ```

## 🚀 Usage
### **Upload an Audio File to MySQL**
Run the following command to upload `11.wav` to the database:
```python
from database import upload_audio
upload_audio("11.wav")
```

### **Fetch and Process Audio from Database**
```python
from app import process_audio_from_db
process_audio_from_db(1)  # Process audio with ID=1
```

### **Convert Audio Format**
```python
from app import convert_audio_format
convert_audio_format("downloaded_audio/11.mp3")
```

### **Perform Sentiment Analysis on Transcribed Audio**
```python
from app import analyze_sentiment
text = "The audio file contains positive words."
sentiment = analyze_sentiment(text)
print(sentiment)
```

## ❓ Troubleshooting
### **1️⃣ File Not Found Error**
- Ensure the file exists in the expected location.
- Try using an **absolute path** instead of a relative one.
- Run `ls downloaded_audio/` (Mac/Linux) or `dir downloaded_audio\` (Windows) to verify.

### **2️⃣ ffmpeg Not Found**
- Ensure `ffmpeg` is installed and accessible in the system PATH.
- Test by running `ffmpeg -version`.

### **3️⃣ MySQL Connection Issues**
- Verify MySQL is running (`mysql -u root -p`).
- Check credentials in `database.py`.
- Ensure the database and table exist.

## 🏗️ Future Improvements
- ✅ Implement **Speech-to-Text Conversion**.
- ✅ Add **Web Interface** for user uploads.
- ✅ Optimize **Audio Processing Speed**.

## ✨ Credits
Developed by **Vishwajeet** 🚀

## 📜 License
This project is licensed under the **MIT License**.

