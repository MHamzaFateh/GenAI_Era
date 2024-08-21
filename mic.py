import os
import google.generativeai as genai
import speech_recognition as sr
from datasets import load_dataset
from deep_translator import GoogleTranslator
from gtts import gTTS
import pygame
import streamlit as st
from pydub import AudioSegment
from pydub.playback import play
from st_audiorec import st_audiorec

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

# Streamlit app interface
st.title("AI Virtual Psychiatrist")
st.write("Speak into the microphone and get responses from the AI.")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Record audio using st_audiorec
st.write("Please record your query:")
wav_audio_data = st_audiorec()

if wav_audio_data is not None:
    # Save the recorded audio to a temporary file
    audio_file = "temp_audio.wav"
    with open(audio_file, "wb") as f:
        f.write(wav_audio_data)

    # Convert the WAV file to an AudioSegment for recognition
    audio_segment = AudioSegment.from_wav(audio_file)

    # Initialize the recognizer and process the audio
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            query = recognizer.recognize_google(audio_data, language='ur')
    except sr.UnknownValueError:
        st.write("Could not understand the audio.")
        query = None
    except sr.RequestError as e:
        st.write(f"Could not request results; {e}")
        query = None

    if query:
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
