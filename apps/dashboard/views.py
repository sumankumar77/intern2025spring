from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import pandas as pd
import docx
import os
import wave
import tempfile
import subprocess
import requests
from pydub import AudioSegment


@login_required
def home(request):
    return render(request, 'dashboard/home.html', {'user': request.user})

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/wav2vec2-large-960h"
HUGGINGFACE_API_KEY = "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"  # Replace with your API key


@csrf_exempt  # Disable CSRF protection for testing; use proper authentication in production
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            # Dummy bot response
            bot_response = f"I received and will get back to you soon!"

            return JsonResponse({"response": bot_response})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt  # Disable CSRF for testing
def transcribe_audio(request):
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]

        try:
            # Convert the received audio file to the correct format
            converted_audio_path = convert_audio(audio_file)

            # Debug: Print audio file properties
            with wave.open(converted_audio_path, "rb") as wf:
                print(f"Converted File: {converted_audio_path}")
                print(f"Channels: {wf.getnchannels()}, Sample Rate: {wf.getframerate()}, Format: {wf.getsampwidth()} bytes")

            # **Send the file as binary to Hugging Face API**
            with open(converted_audio_path, "rb") as f:
                headers = {
                    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                    "Content-Type": "audio/wav"  # Ensure correct MIME type
                }
                audio_data = f.read()
                response = requests.post(HUGGINGFACE_API_URL, headers=headers, data=audio_data)

            # Clean up temp files
            os.remove(converted_audio_path)

            # Return transcription response
            if response.status_code == 200:
                return JsonResponse(response.json())  # Send back the transcription
            else:
                return JsonResponse({"error": "Transcription failed", "details": response.text}, status=500)

        except Exception as e:
            return JsonResponse({"error": "Audio conversion failed", "details": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

def convert_audio(audio_file):
    """ Convert uploaded audio file to 16kHz mono WAV format using pydub """
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_input.write(audio_file.read())
    temp_input.close()

    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_output.close()

    audio = AudioSegment.from_file(temp_input.name)
    audio = audio.set_channels(1).set_frame_rate(16000)  # Convert to mono & 16kHz

    audio.export(temp_output.name, format="wav")

    os.remove(temp_input.name)  # Clean up temp input file
    return temp_output.name  # Return path of converted file

import traceback  #  For better error debugging

@csrf_exempt  # Disable CSRF only for testing (Use authentication in production)
def upload_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        try:
            file = request.FILES["file"]
            file_name = file.name.lower()
            print(f"Received file: {file_name}")  #  Debugging

            # Allowed file types
            allowed_extensions = (".xlsx", ".xls", ".docx")
            if not file_name.endswith(allowed_extensions):
                print("Invalid file type detected!")  #  Debugging
                return JsonResponse({"error": "Invalid file type. Only .xlsx, .xls, and .docx files are allowed."}, status=400)

            # **Process Excel files**
            if file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
                file_content = df.to_dict(orient="records")  # Convert Excel to JSON
                print("Excel file processed successfully!")  #  Debugging

            # **Process Word files**
            elif file_name.endswith(".docx"):
                doc = docx.Document(file)
                file_content = "\n".join([para.text for para in doc.paragraphs])  # Extract text
                print("Word file processed successfully!")  #  Debugging

            return JsonResponse({
                "message": f"File '{file.name}' uploaded successfully!",
                "file_content": file_content
            })

        except Exception as e:
            print(f"Error processing file: {str(e)}")  #  Debugging
            traceback.print_exc()  #  Print full error stack trace
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    return JsonResponse({"error": "No file uploaded"}, status=400)