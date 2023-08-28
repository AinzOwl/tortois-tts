import os

import fastapi
import fastapi.middleware.cors
from fastapi import Request
from fastapi.responses import Response

from model import TortoiseModal, stub
from modal import wsgi_app

web_app = fastapi.FastAPI()
web_app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@web_app.get("/")
def index():
    return {"message": "Hello World"}

@web_app.get("/tts/{voices}/{text}")
async def get_request(voices: str, text: str):
    wav = await TortoiseModal().run_tts.call(text, voices, None)

    return Response(content=wav.getvalue(), media_type="audio/wav")

@stub.function()
@wsgi_app()
def app():
    return web_app


if __name__ == "__main__":
    stub.serve()