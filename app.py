from flask import Flask, render_template, request, send_file
from PIL import Image
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from googletrans import Translator
from gtts import gTTS
import pyttsx3
import requests
import os
import nltk

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
def extract_text_from_image(image_path):
    try:
        api_key = "K89919669988957"
        with open(image_path, 'rb') as f:
            response = requests.post(
                "https://api.ocr.space/parse/image",
                files={image_path: f},
                data={
                    'apikey': api_key,
                    'language': 'eng'
                }
            )
        result = response.json()
        if result.get("IsErroredOnProcessing"):
            return f"⚠️ OCR Error: {result.get('ErrorMessage', ['Unknown error'])[0]}"
        parsed_results = result.get("ParsedResults")
        if parsed_results:
            return parsed_results[0].get("ParsedText", "").strip()
        else:
            return "⚠️ No text detected."
    except Exception as e:
        return f"⚠️ Error extracting text: {e}"
def summarize_text(text, sentence_count=None):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()

        if not sentence_count:
            words = len(text.split())
            if words < 80:
                sentence_count = 2
            elif words < 200:
                sentence_count = 3
            else:
                sentence_count = 5

        summary = summarizer(parser.document, sentence_count)
        summarized_text = " ".join(str(sentence) for sentence in summary)
        return summarized_text.strip()
    except Exception as e:
        return f"⚠️ Error summarizing text: {e}"
def translate_to_tamil(text):
    try:
        translator = Translator()
        translated = translator.translate(text, dest='ta')
        return translated.text
    except Exception as e:
        return f"⚠️ Error translating to Tamil: {e}"
def text_to_audio_english(text, filename):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 1.0)
        audio_path = os.path.join(OUTPUT_FOLDER, filename)
        engine.save_to_file(text, audio_path)
        engine.runAndWait()
        return audio_path
    except Exception as e:
        print("English audio error:", e)
        return None
def text_to_audio_tamil(text, filename):
    try:
        audio_path = os.path.join(OUTPUT_FOLDER, filename)
        tts = gTTS(text=text, lang='ta')
        tts.save(audio_path)
        return audio_path
    except Exception as e:
        print("Tamil audio error:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'image' not in request.files:
        return "⚠️ No file uploaded."

    file = request.files['image']
    if file.filename == '':
        return "⚠️ No image selected."

    image_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(image_path)
    extracted_text = extract_text_from_image(image_path)
    summarized_text = summarize_text(extracted_text)
    tamil_text = translate_to_tamil(summarized_text)
    english_audio_file = "summary_english.mp3"
    tamil_audio_file = "summary_tamil.mp3"
    text_to_audio_english(summarized_text, english_audio_file)
    text_to_audio_tamil(tamil_text, tamil_audio_file)

    return render_template(
        'result.html',
        extracted_text=extracted_text,
        summarized_text=summarized_text,
        tamil_text=tamil_text,
        english_audio_file=english_audio_file,
        tamil_audio_file=tamil_audio_file
    )

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

