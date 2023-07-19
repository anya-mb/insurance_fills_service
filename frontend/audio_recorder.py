import os
import openai
import streamlit as st
from audiorecorder import audiorecorder
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

st.title("Audio Recorder")
audio = audiorecorder("Click to record", "Recording...")

if len(audio) > 0:
    # To play audio in frontend:
    st.audio(audio.tobytes())

    # To save audio to a file:
    wav_file = open("audio.mp3", "wb")
    wav_file.write(audio.tobytes())

if st.button("Transcribe"):
    audio_file = open("audio.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    st.write(transcript)
