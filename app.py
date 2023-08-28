import os

import fastapi
import fastapi.middleware.cors
from fastapi import Request
from fastapi.responses import Response

from model import TortoiseModal, stub
from modal import asgi_app

web_app = fastapi.FastAPI()
web_app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.post("/")
async def post_request(req: Request):
    body = await req.json()
    text = body["text"]
    voices = body["voices"]
    target_file_web_paths = body.get("target_file", None)

    wav = await TortoiseModal().run_tts.call(text, voices, target_file_web_paths)

    return Response(content=wav.getvalue(), media_type="audio/wav")


@stub.function()
@asgi_app()
def app():
    return web_app


if __name__ == "__main__":
    stub.serve()