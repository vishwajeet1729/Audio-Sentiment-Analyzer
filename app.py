import os
import nltk
import pymysql
import speech_recognition as sr
from dotenv import load_dotenv
from pydub import AudioSegment
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure the VADER lexicon is downloaded
nltk.download('vader_lexicon')

# Load environment variables
load_dotenv()

# Set FFmpeg path for pydub
AudioSegment.converter = os.getenv('FFMPEG_PATH')

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

# Connect to MySQL
def connect_db():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.MySQLError as e:
        print("Error connecting to MySQL:", e)
        return None

# Setup the database (Ensure required tables exist)
def setup_database():
    connection = connect_db()
    if not connection:
        return

    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_name VARCHAR(255) UNIQUE NOT NULL,
                audio_data LONGBLOB NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_metadata (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_name VARCHAR(255) UNIQUE NOT NULL,
                sentiment VARCHAR(20) NOT NULL
            )
        """)
        connection.commit()
    connection.close()

# Fetch audio from MySQL
def fetch_audio_from_db(file_id, output_folder="./downloaded_audio"):
    connection = connect_db()
    if not connection:
        return None

    os.makedirs(output_folder, exist_ok=True)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT file_name, audio_data FROM audio_files WHERE id = %s", (file_id,))
        result = cursor.fetchone()
        
        if not result:
            print("Error: No audio file found with ID", file_id)
            return None

        file_name, audio_data = result["file_name"], result["audio_data"]
        file_path = os.path.join(output_folder, file_name)

        # Save audio file
        with open(file_path, "wb") as file:
            file.write(audio_data)

        print(f"Audio file saved at: {file_path}")
        return file_path

    except pymysql.MySQLError as e:
        print("Error fetching audio:", e)
        return None
    finally:
        connection.close()

# Transcribe audio
def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Audio could not be understood."
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"

# Analyze sentiment
def analyze_sentiment(text):
    if not text.strip():
        return "No Content"

    sentiment_score = sia.polarity_scores(text)
    compound_score = sentiment_score['compound']

    if compound_score >= 0.05:
        return "Positive"
    elif compound_score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# Save sentiment to MySQL
def save_audio_metadata(file_name, sentiment):
    connection = connect_db()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM audio_metadata WHERE file_name = %s", (file_name,))
            existing_entry = cursor.fetchone()

            if existing_entry is None:
                cursor.execute("INSERT INTO audio_metadata (file_name, sentiment) VALUES (%s, %s)", (file_name, sentiment))
                connection.commit()
                print(f'Saved sentiment for {file_name}: {sentiment}')
            else:
                print(f'Skipped {file_name}, already processed.')
    except pymysql.MySQLError as e:
        print("Error saving sentiment:", e)
    finally:
        connection.close()

# Process an audio file from MySQL
def process_audio_from_db(file_id):
    print("Processing the audio")
    audio_file_path = fetch_audio_from_db(file_id)
    if not audio_file_path:
        return

    print(f'Processing {audio_file_path}...')

    # Transcribe audio
    text = transcribe_audio(audio_file_path)
    print(f"Transcribed Text: {text}")

    # Analyze sentiment
    sentiment_result = analyze_sentiment(text)
    print(f"Sentiment: {sentiment_result}")

    # Save metadata to MySQL
    save_audio_metadata(os.path.basename(audio_file_path), sentiment_result)

# Main function
def main():
    setup_database()

    # Replace with actual file ID from MySQL
    file_id = 1
    process_audio_from_db(file_id)

if __name__ == "__main__":
    main()
