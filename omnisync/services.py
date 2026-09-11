import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def parse_retail_input_with_gemini(raw_input_text: str = None, image_bytes: bytes = None):
    """
    Parses unstructured voice/text/image data into structured JSON 
    using Google's Gemini API with active flash model fallbacks.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    models_to_try = ['gemini-3.6-flash']
    
    prompt = """
    Extract product inventory details from the provided input. 
    Return a valid JSON array of objects with these exact keys: 
    name, category, cost_price, selling_price, quantity.
    Ensure the output is strictly valid JSON without markdown wrapping.
    """
    
    contents = [prompt]
    
    if raw_input_text:
        contents.append(raw_input_text)
        
    if image_bytes:
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg',
            )
        )

    last_exception = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            last_exception = e
            continue
            
    raise RuntimeError(f"Gemini text parsing failed across all fallback models: {str(last_exception)}")


def transcribe_audio_with_gemini(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """
    Transcribes raw audio bytes into editable text using Gemini with model fallback 
    and container type normalization.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    models_to_try = ['gemini-3.6-flash']
    
    if "webm" in mime_type.lower():
        normalized_mime = "audio/webm"
    elif "ogg" in mime_type.lower():
        normalized_mime = "audio/ogg"
    else:
        normalized_mime = "audio/wav"

    last_exception = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    "Transcribe the following audio recording accurately into plain text. Return only the transcribed sentence or words without any introductory or conversational filler.",
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=normalized_mime,
                    )
                ],
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            last_exception = e
            continue
            
    raise RuntimeError(f"Audio transcription service is temporarily unavailable. ({str(last_exception)})")