import os
import google.generativeai as genai
import speech_recognition as sr
from datasets import load_dataset
from deep_translator import GoogleTranslator
from gtts import gTTS
import pygame
import streamlit as st
import numpy as np
import sounddevice as sd

# Set up Google Gemini API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=api_key)

# Initialize the translator
translator = GoogleTranslator(source='en', target='ur')

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

# Function to record audio using sounddevice as fallback
def record_audio():
    st.write("Recording...")
    duration = 5  # seconds
    fs = 44100  # sample rate
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    audio_data = np.squeeze(audio_data)
    return sr.AudioData(audio_data.tobytes(), fs, 2)

# Streamlit app interface
st.title("AI Virtual Psychiatrist")
st.write("Speak into the microphone and get responses from the AI.")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if st.button("Start Listening"):
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.write("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=6)
            query = recognizer.recognize_google(audio, language='ur')
    except AttributeError:
        # If PyAudio is not available, use sounddevice
        audio = record_audio()
        query = recognizer.recognize_google(audio, language='ur')

    st.write(f"آپ نے کہا: {query}")

    result_en = conversational_retrieval(query, st.session_state.chat_history)
    result_ur = translate_text(result_en)
    st.write(f"AI: {result_ur}")

    speak_text(result_ur, lang='ur')

    st.session_state.chat_history.append((query, result_ur))

if st.session_state.chat_history:
    st.subheader("Chat History")
    for i, (user_query, ai_response) in enumerate(st.session_state.chat_history):
        st.write(f"Q{i+1}: {user_query}")
        st.write(f"A{i+1}: {ai_response}")
