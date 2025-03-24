import requests

API_URL = "https://api-inference.huggingface.co/models/facebook/wav2vec2-large-960h"
HEADERS = {"Authorization": "Bearer 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"}  # Replace with your Hugging Face API Key


def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        audio_data = f.read()

    response = requests.post(API_URL, headers=HEADERS, data=audio_data)

    if response.status_code == 200:
        print("Transcription:", response.json())
    else:
        print("Error:", response.status_code, response.text)


# Run test with sample audio
transcribe_audio("sample_audio.wav")
