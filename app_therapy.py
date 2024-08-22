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

api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=api_key)

translator = GoogleTranslator(source='en', target='ur')

def load_data(dataset_name="Amod/mental_health_counseling_conversations"):
    dataset = load_dataset(dataset_name)
    documents = []
    for item in dataset['train']:
        context = item['Context']  
        response = item['Response']  
        documents.append(f"User: {context}\nPsychologist: {response}")
    return documents

def conversational_retrieval(query, chat_history):
    documents = load_data()[:5]  
    combined_documents = "\n".join(documents)
    conversation_context = "\n".join([f"User: {q}\nAI: {a}" for q, a in chat_history])
    full_context = f"{conversation_context}\nDocuments: {combined_documents[:15000]}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(full_context)
    return response.text

def translate_text(text, src_lang='en', dest_lang='ur'):
    return translator.translate(text)

def text_to_speech(text, lang='ur'):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_output:
            tts.save(temp_audio_output.name)
            return temp_audio_output.name
    except Exception as e:
        st.error(f"Error generating speech: {e}")
        return None

    
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("AI Virtual Psychiatrist")
st.write("Speak into the microphone and get responses from the AI Psychiatrist.")

st.write("Record your query:")
audio_bytes = audio_recorder()

if st.session_state.chat_history:
    st.subheader("Chat History")
    for i, (query, response) in enumerate(st.session_state.chat_history):
        st.write(f"Q{i+1}: {query}")
        st.write(f"A{i+1}: {response}")

if audio_bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_file.write(audio_bytes)
        audio_file_path = temp_audio_file.name
    
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
        try:
            query = recognizer.recognize_google(audio, language='ur')
            # st.write(f"Your query: {query}")
            st.write(f"آپ نے کہا: {query}")
            
            result = conversational_retrieval(query, st.session_state.chat_history)
            # result_en = conversational_retrieval(query, st.session_state.chat_history)
            result_ur = translate_text(result)
            st.write("Dr. jennifer:", result_ur)

            st.session_state.chat_history.append((query, result_ur))
            
            audio_file_path = text_to_speech(result_ur)
            
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
