"""
Voice Bot Interface
===================
Local voice bot using microphone and speakers.

Flow: Microphone → OpenAI Whisper → Memory Query → ElevenLabs TTS → Speaker
"""

import os
import io
import time
import tempfile
import wave
from typing import Optional, Tuple

import sounddevice as sd
import numpy as np
from openai import OpenAI
from elevenlabs import ElevenLabs
from elevenlabs.play import play

from ..core.graph import MeetingGraph
from ..core.query import QueryEngine
from ..core.embeddings import EmbeddingStore
from ..ingest.loader import MeetingLoader

# Configuration
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5

# Wake words that activate the bot
WAKE_WORDS = ["hey ampm", "ampm,", "ampm ", "hey am pm", "hey a]mpm", "hey amp", "a]mpm"]


class VoiceBot:
    """
    Voice-activated bot for querying meeting memory.

    Say "Hey AMPM" followed by your question.
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the voice bot.

        Args:
            data_path: Optional path to meeting data JSON file.
        """
        self._validate_keys()

        # Initialize API clients
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # ElevenLabs is optional
        self.elevenlabs = None
        if os.getenv("ELEVENLABS_API_KEY"):
            self.elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

        # Initialize memory system
        self.graph = MeetingGraph()
        self.embeddings = EmbeddingStore(use_backboard=True)
        self.loader = MeetingLoader(self.graph, self.embeddings)
        self.query_engine = QueryEngine(self.graph, self.embeddings)

        # Load meeting data
        if data_path:
            self.loader.load_file(data_path)
        else:
            try:
                self.loader.load_sample_data()
            except FileNotFoundError:
                print("Warning: No sample data found")

        # State
        self.is_speaking = False

        # Voice settings
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        stats = self.graph.stats
        print(f"VoiceBot initialized")
        print(f"Loaded: {stats['meetings']} meetings, {stats['decisions']} decisions")

    def _validate_keys(self):
        """Check that all required API keys are present."""
        # OpenAI is required for Whisper STT
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "Missing OPENAI_API_KEY\n"
                "Copy .env.example to .env and add your keys."
            )
        
        # ElevenLabs is required for TTS (optional - will skip TTS if not set)
        if not os.getenv("ELEVENLABS_API_KEY"):
            print("Warning: ELEVENLABS_API_KEY not set - TTS will be disabled")

    def _record_audio(self, duration: float = RECORD_SECONDS) -> np.ndarray:
        """Record audio from microphone."""
        print(f"Recording for {duration}s... (speak now)")
        audio = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16'
        )
        sd.wait()
        print("Recording complete")
        return audio

    def _audio_to_wav_bytes(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio array to WAV bytes."""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        buffer.seek(0)
        return buffer.read()

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio using OpenAI Whisper."""
        print("Transcribing...")

        wav_bytes = self._audio_to_wav_bytes(audio)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_bytes)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as audio_file:
                transcript = self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            return transcript.text
        finally:
            os.unlink(temp_path)

    def _detect_wake_word(self, text: str) -> Tuple[bool, str]:
        """Check if text contains wake word and extract the question."""
        text_lower = text.lower().strip()

        for wake in WAKE_WORDS:
            if wake in text_lower:
                idx = text_lower.find(wake)
                question = text[idx + len(wake):].strip()
                question = question.lstrip(",.:;!? ")
                if question:
                    return True, question
                return True, text

        return False, ""

    def _query(self, question: str) -> str:
        """Query the meeting memory."""
        print("Thinking...", end=" ", flush=True)
        start_time = time.time()

        result = self.query_engine.query(question)

        elapsed = time.time() - start_time
        print(f"({elapsed:.2f}s)")

        return result.answer

    def _speak(self, text: str) -> Optional[bytes]:
        """Convert text to speech and play it. Returns audio bytes if available."""
        print(f"\nAMPM: {text}\n")
        self.is_speaking = True

        try:
            if not self.elevenlabs:
                print("(TTS disabled - no ELEVENLABS_API_KEY)")
                return None
                
            audio = self.elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )
            play(audio)
            return audio
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
        finally:
            self.is_speaking = False
    
    def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech and return audio bytes (no playback)."""
        if not self.elevenlabs:
            return None
            
        try:
            audio_generator = self.elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )
            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            return audio_bytes
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    def ask(self, question: str) -> str:
        """
        Ask a question and get a response (without speech).

        Args:
            question: The question to ask.

        Returns:
            The response text.
        """
        return self._query(question)

    def ask_and_speak(self, question: str) -> str:
        """
        Ask a question, get a response, and speak it.

        Args:
            question: The question to ask.

        Returns:
            The response text.
        """
        response = self._query(question)
        self._speak(response)
        return response

    def run(self):
        """Main run loop - record, transcribe, respond."""
        print("\n" + "=" * 50)
        print("AMPM Voice Bot - Ready!")
        print("=" * 50)
        print("\nSay 'Hey AMPM' followed by your question.")
        print("Examples:")
        print("  - 'Hey AMPM, why did we choose Stripe?'")
        print("  - 'AMPM, what happened with Legal approval?'")
        print("  - 'Hey AMPM, who made the checkout decision?'")
        print("\nPress Ctrl+C to stop.")
        print("Press Enter to start recording...\n")

        try:
            while True:
                input(">>> Press Enter to record your question...")

                audio = self._record_audio()
                transcript = self._transcribe(audio)
                print(f"Heard: \"{transcript}\"")

                if not transcript.strip():
                    print("(No speech detected)\n")
                    continue

                detected, question = self._detect_wake_word(transcript)

                if detected:
                    print(f"Question: \"{question}\"")
                    response = self._query(question)
                    self._speak(response)
                else:
                    print("(No wake word detected. Say 'Hey AMPM' followed by your question)\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
