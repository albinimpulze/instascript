import moviepy.editor as mp
import speech_recognition as sr
import os
import streamlit as st
import tempfile
import instaloader
import requests
from urllib.parse import urlparse
import time

def download_instagram_video(url):
    path = urlparse(url).path
    shortcode = path.split('/')[-2]
    L = instaloader.Instaloader()

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_file_name = temp_file.name
        temp_file.close()

        if post.is_video:
            response = requests.get(post.video_url)
            with open(temp_file_name, 'wb') as file:
                file.write(response.content)
            return temp_file_name
        else:
            raise ValueError("The Instagram post does not contain a video.")
    except Exception as e:
        raise ValueError(f"Error downloading Instagram video: {str(e)}")

def video_to_text(video_path):
    video = mp.VideoFileClip(video_path)
    audio = video.audio
    
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_audio_path = temp_audio_file.name
    temp_audio_file.close()

    audio.write_audiofile(temp_audio_path, verbose=False, logger=None)

    r = sr.Recognizer()

    with sr.AudioFile(temp_audio_path) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)

    video.close()
    audio.close()

    return text, temp_audio_path

def safe_delete(file_path, max_attempts=5, delay=1):
    for attempt in range(max_attempts):
        try:
            os.unlink(file_path)
            return True
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                return False

# Streamlit interface
st.title("Instagram Video to Text Converter")

instagram_url = st.text_input("Enter Instagram video URL")

if instagram_url:
    if st.button("Transcribe Video"):
        with st.spinner("Downloading and transcribing..."):
            try:
                # Download the Instagram video
                video_path = download_instagram_video(instagram_url)
                
                # Transcribe the video
                transcription, temp_audio_path = video_to_text(video_path)
                
                st.success("Transcription complete!")
                st.text_area("Transcription", transcription, height=300)

                # Clean up the temporary files after everything else is done
                files_to_delete = [video_path, temp_audio_path]
                for file_path in files_to_delete:
                    if not safe_delete(file_path):
                        st.warning(f"Unable to delete temporary file: {file_path}")
                    else:
                        st.info(f"Successfully deleted temporary file: {file_path}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

st.markdown("Note: This app uses Google's Speech Recognition API and requires an internet connection. It also requires access to Instagram, which may be restricted in some regions or networks.")