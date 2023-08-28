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

@stub.function()
@asgi_app()
@web_app.get("/")
def index():
    return {"message": "Hello World"}

@stub.function()
@asgi_app()
@web_app.post("/tts")
async def post_request(request: Request):
    data = await request.json()
    wav = await TortoiseModal().run_tts.call(data["text"], data["voices"])
    return Response(content=wav.getvalue(), media_type="audio/wav")

@stub.function()
@asgi_app()
def app():
    return web_app


if __name__ == "__main__":
    stub.serve()