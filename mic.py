import os
import google.generativeai as genai
import sys
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import tempfile
import speech_recognition as sr

api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=api_key)

# Load data from a file
def load_data(dataset_name="Amod/mental_health_counseling_conversations"):
    dataset = load_dataset(dataset_name)
    documents = [f"User: {item['Context']}\nPsychologist: {item['Response']}" for item in dataset['train']]
    return documents

# This function simulates the conversational retrieval process
def conversational_retrieval(query, chat_history):
    documents = load_data()[:5]
    combined_documents = "\n".join(documents)
    conversation_context = "\n".join([f"User: {q}\nAI: {a}" for q, a in chat_history])
    full_context = f"{conversation_context}\nDocuments: {combined_documents[:12000]}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    response = model.generate_content(full_context)
    return response.text

# Function to convert text to speech
def text_to_speech(text):
    tts = gTTS(text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        tts.save(tmp_file.name)
        return tmp_file.name

# Function to recognize speech from audio
def speech_to_text(audio_bytes):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_bytes) as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)

# Streamlit app
st.title("AI Virtual Therapist")
st.write("Talk to your AI virtual therapist!")

# Record audio input
audio_bytes = audio_recorder()
if audio_bytes:
    with tempfile.NamedTemporaryFile(delete=True) as audio_file:
        audio_file.write(audio_bytes)
        audio_file.flush()
        try:
            user_query = speech_to_text(audio_file.name)
            st.write(f"User: {user_query}")
            if user_query.lower() in ['quit', 'q', 'exit']:
                st.write("Exiting...")
                st.stop()

            # Get the AI's response
            result = conversational_retrieval(user_query, chat_history)
            st.write(f"AI: {result}")

            # Add to chat history
            chat_history.append((user_query, result))

            # Convert response to speech
            audio_response = text_to_speech(result)
            st.audio(audio_response, format="audio/wav")

        except sr.UnknownValueError:
            st.write("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.write("Sorry, there was a problem with the speech recognition service.")
