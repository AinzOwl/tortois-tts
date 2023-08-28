import io
import os
import subprocess
import tempfile
import requests

import modal 
from modal import method

stub = modal.Stub("tts")


def download_models():
    from tortoise.api import MODELS_DIR, TextToSpeech

    tts = TextToSpeech(models_dir=MODELS_DIR)
    tts.get_random_conditioning_latents()


tortoise_image = (
    modal.Image.debian_slim()
    .apt_install("git", "libsndfile-dev", "ffmpeg", "curl")
    .pip_install(
        "torch",
        "torchvision",
        "torchaudio",
        "pydub",
        extra_index_url="https://download.pytorch.org/whl/cu116",
    )
    .pip_install("git+https://github.com/neonbjb/tortoise-tts")
    .run_function(download_models)
)

@stub.cls(
    image=tortoise_image,
    gpu="A10G",
)

class TortoiseModal:
    def __enter__(self):
        """
        Load the model weights into GPU memory when the container starts.
        """
        from tortoise.api import MODELS_DIR, TextToSpeech
        from tortoise.utils.audio import load_audio, load_voices

        self.load_voices = load_voices
        self.load_audio = load_audio
        self.tts = TextToSpeech(models_dir=MODELS_DIR)
        self.tts.get_random_conditioning_latents()

    def process_synthesis_result(self, result):
        """
        Converts an audio torch tensor to a binary blob.
        """
        import pydub
        import torchaudio

        with tempfile.NamedTemporaryFile() as converted_wav_tmp:
            torchaudio.save(
                converted_wav_tmp.name + ".wav",
                result,
                24000,
            )
            wav = io.BytesIO()
            _ = pydub.AudioSegment.from_file(
                converted_wav_tmp.name + ".wav", format="wav"
            ).export(wav, format="wav")

        return wav

    def download_voice_file(self, voice_url):
        """
        Downloads the voice file from the provided URL and returns the path to the downloaded file.
        """
        response = requests.get(voice_url)
        if response.status_code != 200:
            raise ValueError(f"Failed to download voice file from {voice_url}.")
        
        with tempfile.NamedTemporaryFile(delete=False) as voice_file:
            voice_file.write(response.content)
            voice_file_path = voice_file.name

        return voice_file_path

    @method()
    def run_tts(self, text, voice_url):
        """
        Runs Tortoise TTS on the given text and voice URL.
        """
        CANDIDATES = 1  # NOTE: this code only works for one candidate.
        CVVP_AMOUNT = 0.0
        SEED = None
        PRESET = "fast"

        if voice_url and voice_url.strip():
            voice_file_path = self.download_voice_file(voice_url)
            voice_samples, conditioning_latents = self.load_audio([voice_file_path])
            os.remove(voice_file_path)
        else:
            voice_samples, conditioning_latents = self.load_voices(["target"])

        gen, _ = self.tts.tts_with_preset(
            text,
            k=CANDIDATES,
            voice_samples=voice_samples,
            conditioning_latents=conditioning_latents,
            preset=PRESET,
            use_deterministic_seed=SEED,
            return_deterministic_state=True,
            cvvp_amount=CVVP_AMOUNT,
        )

        wav = self.process_synthesis_result(gen.squeeze(0).cpu())

        return wav