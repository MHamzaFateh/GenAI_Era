import os
import google.generativeai as genai
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import tempfile
import speech_recognition as sr
from datasets import load_dataset
from deep_translator import GoogleTranslator
import pygame


# Retrieve API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=api_key)

# Initialize translator
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
    full_context = f"{conversation_context}\nDocuments: {combined_documents[:9000]}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    response = model.generate_content(full_context)
    return response.text

# Function to translate text
def translate_text(text, src_lang='en', dest_lang='ur'):
    return translator.translate(text)

Function to speak text
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


# Function to recognize speech from audio
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language='en')  # You can change language code if needed
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError:
            return "Sorry, there was a problem with the speech recognition service."

# Initialize Streamlit app
st.title("AI Virtual Psychiatrist")
st.write("Speak into the microphone and get responses from the AI. To end the conversation, say 'Q'.")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Record audio input
audio_bytes = audio_recorder()
if audio_bytes:
    with tempfile.NamedTemporaryFile(delete=True) as audio_file:
        audio_file.write(audio_bytes)
        audio_file.flush()
        try:
            user_query = speech_to_text(audio_file.name)
            st.write(f"User: {user_query}")
            if user_query.strip().lower() == 'q':
                st.write("Exiting...")
                st.stop()

            # Get AI response
            result_en = conversational_retrieval(user_query, st.session_state.chat_history)
            result_ur = translate_text(result_en)
            st.write(f"AI: {result_ur}")

            # Speak AI response
            speak_text(result_ur, lang='ur')

            # Update chat history
            st.session_state.chat_history.append((user_query, result_ur))

        except Exception as e:
            st.write(f"An error occurred: {str(e)}")

# Display chat history
if st.session_state.chat_history:
    st.subheader("Chat History")
    for i, (user_query, ai_response) in enumerate(st.session_state.chat_history):
        st.write(f"Q{i+1}: {user_query}")
        st.write(f"A{i+1}: {ai_response}")
