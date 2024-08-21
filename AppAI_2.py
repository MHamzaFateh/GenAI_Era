import os
import sys
import google.generativeai as genai
import speech_recognition as sr
from datasets import load_dataset
from deep_translator import GoogleTranslator
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import streamlit as st

# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Translator setup
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
    full_context = f"{conversation_context}\nDocuments: {combined_documents[:9000]}\nUser Query: {query}"
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    response = model.generate_content(full_context)
    return response.text

def translate_text(text, src_lang='en', dest_lang='ur'):
    translation = translator.translate(text)
    return translation

def speak_text(text, lang='ur'):
    tts = gTTS(text=text, lang=lang)
    audio_file = os.path.join(os.getcwd(), "response.mp3")
    tts.save(audio_file)
    # Load and play audio using pydub
    sound = AudioSegment.from_file(audio_file)
    play(sound)
    os.remove(audio_file)

st.title("AI Virtual Psychiatrist")
st.write("Speak into the microphone and get responses from the AI. To end the conversation, say 'Q'.")

chat_history = []

if st.button("Start Listening"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=6)
            query = recognizer.recognize_google(audio, language='ur')
            st.write(f"آپ نے کہا: {query}")

            if query.strip().lower() == 'q':
                st.write("گفتگو ختم کی جا رہی ہے۔")
                sys.exit()

            result_en = conversational_retrieval(query, chat_history)
            result_ur = translate_text(result_en)
            st.write(f"AI: {result_ur}")

            speak_text(result_ur, lang='ur')

            chat_history.append((query, result_ur))

        except sr.UnknownValueError:
            st.write("معذرت، میں آڈیو کو سمجھ نہیں سکا۔")
        except sr.RequestError:
            st.write("معذرت، میں سروس سے نتائج کی درخواست نہیں کر سکا۔")
        except sr.WaitTimeoutError:
            st.write("وقت کے دوران کوئی آواز نہیں سنی گئی۔")

if chat_history:
    st.subheader("Chat History")
    for i, (user_query, ai_response) in enumerate(chat_history):
        st.write(f"Q{i+1}: {user_query}")
        st.write(f"A{i+1}: {ai_response}")
