import os
import json
import nltk
import speech_recognition as sr
import firebase_admin
from firebase_admin import credentials, storage
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from google.cloud import storage as gcs_storage
from dotenv import load_dotenv
from pydub import AudioSegment  # Import pydub for audio conversion

# Ensure the VADER lexicon is downloaded
nltk.download('vader_lexicon')

# Load environment variables
load_dotenv()
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))  # Debug line

# Set the FFmpeg path for pydub
AudioSegment.converter = os.getenv('FFMPEG_PATH')  # Use env variable for FFmpeg path

# Initialize the Sentiment Intensity Analyzer
sia = SentimentIntensityAnalyzer()

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))  # Use env variable for the path
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')  # Use env variable for the bucket name
})

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text using VADER and returns the sentiment category.
    """
    if not text.strip():  # Handle empty or whitespace text
        return "No Content"

    # Perform sentiment analysis using VADER
    sentiment_score = sia.polarity_scores(text)
    compound_score = sentiment_score['compound']

    # Categorize based on the compound score
    if compound_score >= 0.05:
        sentiment = "Positive"
    elif compound_score <= -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return sentiment

def convert_audio_format(input_path, output_format='wav'):
    """
    Converts audio file to the specified format using pydub.
    """
    audio = AudioSegment.from_file(input_path)  # Automatically detects the file format
    output_path = os.path.splitext(input_path)[0] + f'.{output_format}'
    audio.export(output_path, format=output_format)
    print(f'Converted {input_path} to {output_path}.')
    return output_path

def transcribe_audio(file_path):
    """
    Transcribes audio to text using Google Web Speech API.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Audio could not be understood."
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"

def download_audio_from_firebase(audio_blob_name):
    # Ensure the downloads directory exists
    os.makedirs('./downloads', exist_ok=True)

    # Initialize a Cloud Storage client
    client = gcs_storage.Client()
    bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')  # Use env variable for the bucket name
    bucket = client.bucket(bucket_name)
    
    # Specify the full path to the audio file in Firebase Storage
    blob = bucket.blob(audio_blob_name)  # Blob name as passed in the function
    local_path = f'./downloads/{os.path.basename(audio_blob_name)}'  # Local path for the downloaded file

    # Check if the blob exists
    if not blob.exists():
        print(f'Error: {audio_blob_name} does not exist in Firebase Storage.')
        return None

    # Download the audio file
    try:
        blob.download_to_filename(local_path)
        print(f'Downloaded {audio_blob_name} to {local_path}.')
        return local_path
    except Exception as e:
        print(f'Error downloading {audio_blob_name}: {e}')
        return None

def upload_audio_metadata(audio_blob_name, sentiment):
    """
    Uploads the sentiment as metadata for the audio file in Firebase, 
    only if the existing metadata is an empty string.
    """
    bucket = storage.bucket()
    blob = bucket.blob(audio_blob_name)  # Ensure correct path is used

    # Fetch existing metadata
    metadata = blob.metadata or {}
    existing_sentiment = metadata.get('sentiment', '')  # Get existing sentiment or default to empty string

    # Check if existing sentiment is an empty string
    if existing_sentiment == "":
        # Update metadata with new sentiment
        metadata['sentiment'] = sentiment
        blob.metadata = metadata
        blob.patch()  # This will update the metadata on Firebase
        print(f'Updated sentiment metadata for {audio_blob_name} to: {sentiment}')
    else:
        print(f'Skipped updating sentiment for {audio_blob_name} because existing metadata is not empty.')

def process_audio_files_in_folders():
    """
    Process all audio files in the recordings folders in Firebase Storage.
    """
    client = gcs_storage.Client()
    bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')  # Use env variable for the bucket name
    bucket = client.bucket(bucket_name)

    # List all blobs in the specified folder (assuming the structure is `recordings/{folder_name}/audio_file.m4a`)
    blobs = bucket.list_blobs(prefix='recordings/')  # Adjust prefix based on your folder structure

    # Process each blob
    for blob in blobs:
        if blob.name.endswith('.m4a'):
            audio_blob_name = blob.name
            print(f'Processing {audio_blob_name}...')

            # Check existing metadata before downloading and processing
            metadata = blob.metadata or {}
            existing_sentiment = metadata.get('sentiment', '')  # Get existing sentiment or default to empty string

            if existing_sentiment != "":
                print(f'Skipped processing for {audio_blob_name} because sentiment metadata already exists: {existing_sentiment}')
                continue  # Skip to the next audio file

            # Download the audio from Firebase Storage
            audio_path = download_audio_from_firebase(audio_blob_name)

            # Proceed only if the audio path is valid
            if audio_path:
                # Convert audio file to WAV format
                converted_audio_path = convert_audio_format(audio_path)

                # Transcribe audio to text
                text = transcribe_audio(converted_audio_path)
                print(f"Transcribed Text from audio:\n{text}\n")

                # Perform sentiment analysis
                sentiment_result = analyze_sentiment(text)

                # Print the result
                print(f"The sentiment of the text is: {sentiment_result}")

                # Update the audio metadata in Firebase
                upload_audio_metadata(audio_blob_name, sentiment_result)

                # Clean up downloaded and converted audio files
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                if os.path.exists(converted_audio_path):
                    os.remove(converted_audio_path)

def main():
    process_audio_files_in_folders()

if __name__ == "__main__":
    main()
