# app/main.py
from bson import ObjectId
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response
from openai import OpenAI
from pathlib import Path
from enum import Enum
from .database import mongodb
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from .auth import get_api_key
from .config import OPENAI_API_KEY

app = FastAPI()
router = APIRouter(prefix="/v1")

client = OpenAI(
    # This is the default and can be omitted
    api_key=OPENAI_API_KEY,
)

class Language(str, Enum):
    english = "English"
    chinese = "Chinese"
    turkish = "Turkish"

class AudioLanguage(str, Enum):
    source = "source"
    target = "target"

class Voice(str, Enum):
    alloy = "alloy"
    echo = "echo"
    fable = "fable"
    onyx = "onyx"
    nova = "nova"
    shimmer = "shimmer"

@router.post("/translate",dependencies=[Depends(get_api_key)])
async def translate(
    text: str,
    source_language: Language = Language.chinese,
    target_language: Language = Language.english,
    audio_language: AudioLanguage = AudioLanguage.target,
    voice: Voice = Voice.alloy,
    speed_factor: float = 0.75
):
    try:
        completion = client.chat.completions.create(
            messages=[
                    {"role": "system", "content": "You are a helpful assistant that translates text."},
                    {"role": "user", "content": f"Translate the following text from {source_language} to {target_language}: {text}. \nnotice : just return in {target_language}, and using casual language , spoken language and Correct grammatical statement as much as possible"}
            ],
            model="gpt-3.5-turbo",
        )

        print(f"{completion.choices[0].message.content}")

        if audio_language == "target":
            speech_input = completion.choices[0].message.content
        else:
            speech_input = text

        speech_file_path = Path(__file__).parent / "speech.mp3"
        response_tts = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=speech_input,
            speed=speed_factor
        )
        
        response_tts.stream_to_file(speech_file_path)

        # Save the audio file to MongoDB using AsyncIOMotorGridFSBucket
        bucket = AsyncIOMotorGridFSBucket(mongodb.db)
        with open(speech_file_path, "rb") as f:
            file_id = await bucket.upload_from_stream(f"{speech_input}.mp3", f)

        return {"message": "Translation and audio file saved successfully", "translated_text":completion.choices[0].message.content,"file_id": str(file_id)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/download/{file_id}", dependencies=[Depends(get_api_key)])
async def download_file(file_id: str):
    try:
        bucket = AsyncIOMotorGridFSBucket(mongodb.db)
        file_id = ObjectId(file_id)
        grid_out = await bucket.open_download_stream(file_id)

        # Read the file content
        file_data = await grid_out.read()

        return Response(content=file_data, media_type="audio/mpeg", headers={
            "Content-Disposition": f"attachment; filename={grid_out.filename}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)
