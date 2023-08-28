import os

import fastapi
import fastapi.middleware.cors
from fastapi import Request
from fastapi.responses import Response

from model import TortoiseModal, stub
from modal import web_endpoint



## Setup FastAPI server.
web_app = fastapi.FastAPI()
web_app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.post("/")
def post_request(req: Request):
    """
    POST endpoint for running Tortoise. Checks whether the user exists,
    and adds usage time to the user's account.
    """
    import asyncio
    import time

    body = asyncio.run(req.json())
    text = body["text"]
    voices = body["voices"]
    api_key = body["api_key"]
    target_file_web_paths = body.get("target_file", None)

    start = time.time()
    wav = TortoiseModal().run_tts.call(text, voices, target_file_web_paths)
    end = time.time()

    return Response(content=wav.getvalue(), media_type="audio/wav")


@stub.function()
@web_endpoint()
def app():
    return web_app


if __name__ == "__main__":
    stub.serve()
