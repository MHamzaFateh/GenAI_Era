import os
import google.generativeai as genai
import sys
import streamlit as st
from st_audiorec import st_audiorec
import speech_recognition as sr
from gtts import gTTS
import tempfile
import pygame

# Configure the Gemini API key
os.environ["GEMINI_API_KEY"] = "AIzaSyCEFs57Nts11jLv1cIpA4qgHn1ZNJPUX7w"
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Load data from a file
def load_data(filepath="data.txt"):
    documents = []
    if os.path.isfile(filepath):
        with open(filepath, 'r') as file:
            documents.append(file.read())
    else:
        raise FileNotFoundError(f"The file {filepath} does not exist.")
    return documents

# This function simulates the conversational retrieval process
def conversational_retrieval(query, chat_history):
    documents = load_data()
    combined_documents = " ".join(documents)
    conversation_context = "\n".join([f"User: {q}\nAI: {a}" for q, a in chat_history])
    full_context = f"{conversation_context}\nDocuments: {combined_documents}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    response = model.generate_content(full_context)
    return response.text

# Initialize chat history
chat_history = []

# Streamlit app
st.title("AI Virtual Therapist with Voice Interaction")

# Record voice input
st.write("Please speak to the AI:")
wav_audio_data = st_audiorec()

if wav_audio_data is not None:
    # Save the audio data to a temporary file
    with tempfile.NamedTemporaryFile(delete=True) as temp_wav_file:
        temp_wav_file.write(wav_audio_data)
        temp_wav_file.flush()

        # Recognize speech using Google's speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav_file.name) as source:
            audio_data = recognizer.record(source)
            try:
                query = recognizer.recognize_google(audio_data, language="en-US")
                st.write(f"You said: {query}")

                # Get the AI's response
                result = conversational_retrieval(query, chat_history)
                st.write(f"AI: {result}")

                # Text-to-Speech (TTS)
                tts = gTTS(text=result, lang='en')
                with tempfile.NamedTemporaryFile(delete=True) as temp_mp3_file:
                    tts.save(temp_mp3_file.name)
                    pygame.mixer.init()
                    pygame.mixer.music.load(temp_mp3_file.name)
                    pygame.mixer.music.play()

                # Add the conversation to the history
                chat_history.append((query, result))

            except sr.UnknownValueError:
                st.write("Google Speech Recognition could not understand the audio.")
            except sr.RequestError as e:
                st.write(f"Could not request results from Google Speech Recognition service; {e}")

# Prompt for text input as well
text_query = st.text_input("Or type your question here:")

if st.button("Submit Query"):
    result = conversational_retrieval(text_query, chat_history)
    st.write(f"AI: {result}")

    # TTS for text input
    tts = gTTS(text=result, lang='en')
    with tempfile.NamedTemporaryFile(delete=True) as temp_mp3_file:
        tts.save(temp_mp3_file.name)
        pygame.mixer.init()
        pygame.mixer.music.load(temp_mp3_file.name)
        pygame.mixer.music.play()

    chat_history.append((text_query, result))
