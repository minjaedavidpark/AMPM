"""
AMPM Bot - Local Audio Version
==============================
Voice-activated AI assistant using microphone and speakers.

Flow: Microphone -> OpenAI Whisper -> Cerebras LLM -> ElevenLabs TTS -> Speaker
"""

import os
import io
import time
import tempfile
import wave
from typing import Tuple, Optional

import sounddevice as sd
import numpy as np
from openai import OpenAI
from cerebras.cloud.sdk import Cerebras
from elevenlabs import ElevenLabs
from elevenlabs.play import play

from .knowledge import MeetingKnowledge

# Configuration
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5

# Wake words that activate the bot
WAKE_WORDS = ["hey ampm", "ampm,", "ampm ", "hey am pm", "hey a]mpm", "hey amp", "a]mpm"]


class AMPMBot:
    """Main bot class that orchestrates STT, LLM, and TTS."""

    def __init__(self, knowledge_path: Optional[str] = None):
        """
        Initialize the AMPM bot.

        Args:
            knowledge_path: Optional path to meeting data JSON file.
        """
        self._validate_keys()

        # Initialize API clients
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.cerebras = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
        self.elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

        # Load knowledge base
        self.knowledge = MeetingKnowledge(knowledge_path)

        # State
        self.is_speaking = False

        # Voice settings
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        print(f"AMPM Bot initialized with Cerebras (fast inference)")
        print(f"Loaded {self.knowledge.meeting_count} meetings from {self.knowledge.project_name}")

    def _validate_keys(self):
        """Check that all required API keys are present."""
        required = ["OPENAI_API_KEY", "CEREBRAS_API_KEY", "ELEVENLABS_API_KEY"]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(
                f"Missing API keys: {', '.join(missing)}\n"
                "Copy .env.example to .env and add your keys."
            )

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

    def _generate_response(self, question: str) -> str:
        """Use Cerebras for fast response generation."""
        print("Thinking (Cerebras)...", end=" ", flush=True)
        start_time = time.time()

        context = self.knowledge.get_context()

        system_prompt = """You are AMPM, an AI meeting assistant that helps teams remember decisions and track action items.

Your role:
- Answer questions about past meetings, decisions, and action items
- Be concise and direct (2-3 sentences max for spoken responses)
- Always cite the specific meeting date and who made the decision
- If you don't know, say so clearly

Important: Your response will be spoken aloud, so keep it conversational and brief."""

        user_prompt = f"""Based on the following meeting history, answer this question:

Question: {question}

Meeting History:
{context}

Remember: Keep your answer brief (2-3 sentences) as it will be spoken aloud."""

        response = self.cerebras.chat.completions.create(
            model="llama-3.3-70b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )

        elapsed = time.time() - start_time
        print(f"({elapsed:.2f}s)")

        return response.choices[0].message.content

    def _speak(self, text: str):
        """Convert text to speech and play it."""
        print(f"\nAMPM: {text}\n")
        self.is_speaking = True

        try:
            audio = self.elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )
            play(audio)
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            self.is_speaking = False

    def ask(self, question: str) -> str:
        """
        Ask a question and get a response (without speech).

        Args:
            question: The question to ask.

        Returns:
            The response text.
        """
        return self._generate_response(question)

    def ask_and_speak(self, question: str) -> str:
        """
        Ask a question, get a response, and speak it.

        Args:
            question: The question to ask.

        Returns:
            The response text.
        """
        response = self._generate_response(question)
        self._speak(response)
        return response

    def run(self):
        """Main run loop - record, transcribe, respond."""
        print("\n" + "=" * 50)
        print("AMPM Meeting Bot - Ready!")
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
                    response = self._generate_response(question)
                    self._speak(response)
                else:
                    print("(No wake word detected. Say 'Hey AMPM' followed by your question)\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
