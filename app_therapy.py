import os
import google.generativeai as genai
import sys
from datasets import load_dataset
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from deep_translator import GoogleTranslator
import speech_recognition as sr
from gtts import gTTS
import pyttsx3
import tempfile

# Configure the Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=api_key)

translator = GoogleTranslator(source='en', target='ur')

def load_data(dataset_name="Amod/mental_health_counseling_conversations"):
    dataset = load_dataset(dataset_name)
    # Extracting context and response from the dataset
    documents = []
    for item in dataset['train']:
        context = item['Context']  # User's question
        response = item['Response']  # Psychologist's answer
        documents.append(f"User: {context}\nPsychologist: {response}")
    return documents

# Define conversational retrieval function
def conversational_retrieval(query, chat_history):
    documents = load_data()[:5]  # Load a small subset of the dataset
    combined_documents = "\n".join(documents)
    conversation_context = "\n".join([f"User: {q}\nAI: {a}" for q, a in chat_history])
    full_context = f"{conversation_context}\nDocuments: {combined_documents[:12000]}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(full_context)
    return response.text

def translate_text(text, src_lang='en', dest_lang='ur'):
    return translator.translate(text)

# Function to convert text to speech using pyttsx3
def text_to_speech(text, lang='ur'):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_output:
            tts.save(temp_audio_output.name)
            return temp_audio_output.name
    except Exception as e:
        st.error(f"Error generating speech: {e}")
        return None

    

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Streamlit app interface
st.title("AI Virtual Psychiatrist")
st.write("Speak into the microphone and get responses from the AI Psychiatrist.")

# Audio recording section
st.write("Record your query:")
audio_bytes = audio_recorder()

# Display chat history
if st.session_state.chat_history:
    st.subheader("Chat History")
    for i, (query, response) in enumerate(st.session_state.chat_history):
        st.write(f"Q{i+1}: {query}")
        st.write(f"A{i+1}: {response}")

if audio_bytes:
    # Save the audio bytes to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_file.write(audio_bytes)
        audio_file_path = temp_audio_file.name
    
    # Convert audio to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
        try:
            query = recognizer.recognize_google(audio, language='ur')
            # st.write(f"Your query: {query}")
            st.write(f"آپ نے کہا: {query}")
            
            # Get the AI's response based on the query and the conversation history
            result = conversational_retrieval(query, st.session_state.chat_history)
            # result_en = conversational_retrieval(query, st.session_state.chat_history)
            result_ur = translate_text(result)
            st.write("Dr. jennifer:", result_ur)

            # Add the current query and AI's response to the session history
            st.session_state.chat_history.append((query, result_ur))
            
            # Convert AI's response to speech using pyttsx3
            audio_file_path = text_to_speech(result_ur)
            
            # Play the generated audio
            st.audio(audio_file_path, format='audio/mp3')
        
        # except sr.UnknownValueError:
        #     st.write("Sorry, I could not understand the audio.")
        # except sr.RequestError as e:
        #     st.write(f"Could not request results from Google Speech Recognition service; {e}")
        except sr.UnknownValueError:
            st.write("معذرت، میں آڈیو کو سمجھ نہیں سکا۔")
        except sr.RequestError:
            st.write("معذرت، میں سروس سے نتائج کی درخواست نہیں کر سکا۔")
        except Exception as e:
            st.write(f"ایک خطا واقع ہوئی: {str(e)}")
