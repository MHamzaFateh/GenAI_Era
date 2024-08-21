import os
import io
import wave
import numpy as np
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment
from speech_recognition import Recognizer, AudioFile
import google.generativeai as genai
from deep_translator import GoogleTranslator
from gtts import gTTS
import pygame

# Set up Google Gemini API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=api_key)

# Initialize the translator
translator = GoogleTranslator(source='en', target='ur')

# Function to convert WEBM audio bytes to WAV format
def audio_bytes_to_wav(audio_bytes, sample_rate):
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)
    return wav_io

# Function to perform speech recognition on WAV audio
def audio_bytes_to_text(audio_bytes, sample_rate):
    wav_io = audio_bytes_to_wav(audio_bytes, sample_rate)
    recognizer = Recognizer()
    with AudioFile(wav_io) as source:
        audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language='ur')  # Adjust language code if needed

# Function to load dataset
def load_data(dataset_name="Amod/mental_health_counseling_conversations"):
    dataset = load_dataset(dataset_name)
    documents = [f"User: {item['Context']}\nPsychologist: {item['Response']}" for item in dataset['train']]
    return documents

# Function for conversational retrieval
def conversational_retrieval(query, chat_history):
    documents = load_data()[:5]
    combined_documents = "\n".join(documents)
    conversation_context = "\n".join([f"User: {q}\nAI: {a}" for q, a in chat_history])
    full_context = f"{conversation_context}\nDocuments: {combined_documents[:12000]}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    response = model.generate_content(full_context)
    return response.text

# Function to translate text
def translate_text(text, src_lang='en', dest_lang='ur'):
    return translator.translate(text)

# Function to speak text
def speak_text(text, lang='ur'):
    tts = gTTS(text=text, lang=lang)
    audio_file = "response.mp3"
    tts.save(audio_file)

    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.quit()

# Streamlit app interface
st.title("AI Virtual Psychiatrist")

# Record audio using Streamlit Mic Recorder
audio = mic_recorder(
    start_prompt="Start recording",
    stop_prompt="Stop recording",
    just_once=True,
    format="webm"
)

# Process the recorded audio
if audio:
    audio_bytes = audio['bytes']
    sample_rate = audio['sample_rate']
    try:
        query = audio_bytes_to_text(audio_bytes, sample_rate)
        st.write(f"You said: {query}")

        # Perform conversational retrieval
        result_en = conversational_retrieval(query, st.session_state.get('chat_history', []))
        result_ur = translate_text(result_en)
        st.write(f"AI: {result_ur}")

        # Speak the response
        speak_text(result_ur, lang='ur')

        # Update chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append((query, result_ur))
        
    except Exception as e:
        st.write(f"Error: {e}")

if st.session_state.get('chat_history'):
    st.subheader("Chat History")
    for i, (user_query, ai_response) in enumerate(st.session_state.chat_history):
        st.write(f"Q{i+1}: {user_query}")
        st.write(f"A{i+1}: {ai_response}")
