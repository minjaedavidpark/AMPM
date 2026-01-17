"""
Voice Bot Interface
===================
Local voice bot using microphone and speakers.

Flow: Microphone → OpenAI Whisper → Memory Query → ElevenLabs TTS → Speaker

Features:
- Continuous listening without requiring Enter
- Interruption handling: say "Hey Parrot" to ask new question, "stop" to stop, "thank you" for acknowledgment
- Natural, friendly responses
"""

import os
import io
import time
import tempfile
import wave
import threading
import queue
import random
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
INTERRUPT_RECORD_SECONDS = 2  # Shorter recordings during speech for faster interrupt detection

# Wake words that activate the bot (all start with "hey par...")
WAKE_WORDS = ["hey parrot", "hey par rot", "hey par", "hey parrot,", "hey parrot "]

# Stop phrases (all start with "hey par...")
STOP_PHRASES = ["hey parrot stop", "hey parrot, stop", "hey par stop", "hey parrot be quiet", "hey parrot shut up"]

# Thank you phrases (all start with "hey par...")
THANK_YOU_PHRASES = ["hey parrot thank you", "hey parrot thanks", "hey parrot, thank you", "hey parrot, thanks", "hey par thank you", "hey par thanks"]

# Friendly acknowledgment responses
ACKNOWLEDGMENT_RESPONSES = [
    "You're welcome!",
    "Happy to help!",
    "Anytime!",
    "Of course!",
    "Glad I could help!",
    "No problem at all!",
    "You got it!",
]


class VoiceBot:
    """
    Voice-activated bot for querying meeting memory.

    Say "Hey Parrot" followed by your question.

    Interruption handling:
    - Say "Hey Parrot" with a new question to interrupt and ask something else
    - Say "stop" to stop the current response
    - Say "thank you" to get a friendly acknowledgment
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
        self.should_stop_speaking = False
        self.interrupt_queue = queue.Queue()
        self.listening_thread = None
        self.stop_listening = False

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

    def _detect_stop_phrase(self, text: str) -> bool:
        """Check if text contains a stop phrase."""
        text_lower = text.lower().strip()
        for phrase in STOP_PHRASES:
            if phrase in text_lower:
                return True
        return False

    def _detect_thank_you(self, text: str) -> bool:
        """Check if text contains a thank you phrase."""
        text_lower = text.lower().strip()
        for phrase in THANK_YOU_PHRASES:
            if phrase in text_lower:
                return True
        return False

    def _get_acknowledgment_response(self) -> str:
        """Get a random friendly acknowledgment response."""
        return random.choice(ACKNOWLEDGMENT_RESPONSES)

    def _background_listen(self):
        """Background listening thread that runs while bot is speaking."""
        while not self.stop_listening and self.is_speaking:
            try:
                # Record shorter clips for faster interrupt detection
                audio = sd.rec(
                    int(INTERRUPT_RECORD_SECONDS * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype='int16'
                )
                sd.wait()

                # Check audio level
                audio_level = np.abs(audio).mean()
                if audio_level < 50:
                    continue  # Skip silence

                # Transcribe
                transcript = self._transcribe(audio)
                if not transcript.strip():
                    continue

                transcript_lower = transcript.lower().strip()
                print(f"\n[Background heard: \"{transcript}\"]")

                # Check for stop phrases
                if self._detect_stop_phrase(transcript):
                    print("[Stop detected!]")
                    self.should_stop_speaking = True
                    self.interrupt_queue.put(("stop", None))
                    break

                # Check for thank you
                if self._detect_thank_you(transcript):
                    print("[Thank you detected!]")
                    self.should_stop_speaking = True
                    self.interrupt_queue.put(("thank_you", None))
                    break

                # Check for new question (wake word)
                detected, question = self._detect_wake_word(transcript)
                if detected and question:
                    print(f"[New question detected: \"{question}\"]")
                    self.should_stop_speaking = True
                    self.interrupt_queue.put(("new_question", question))
                    break

            except Exception as e:
                # Ignore errors in background thread
                pass

    def _query(self, question: str) -> str:
        """Query the meeting memory."""
        print("Thinking...", end=" ", flush=True)
        start_time = time.time()

        result = self.query_engine.query(question)

        elapsed = time.time() - start_time
        print(f"({elapsed:.2f}s)")

        return result.answer

    def _speak(self, text: str, allow_interrupts: bool = True) -> Optional[bytes]:
        """
        Convert text to speech and play it with interrupt handling.

        Args:
            text: Text to speak
            allow_interrupts: If True, listen for interrupts while speaking

        Returns:
            Audio bytes if available
        """
        print(f"\nParrot: {text}\n")
        self.is_speaking = True
        self.should_stop_speaking = False

        # Clear the interrupt queue
        while not self.interrupt_queue.empty():
            try:
                self.interrupt_queue.get_nowait()
            except queue.Empty:
                break

        try:
            if not self.elevenlabs:
                print("(TTS disabled - no ELEVENLABS_API_KEY)")
                return None

            # Start background listening thread if interrupts are allowed
            if allow_interrupts:
                self.stop_listening = False
                self.listening_thread = threading.Thread(target=self._background_listen, daemon=True)
                self.listening_thread.start()

            # Generate and play audio
            audio = self.elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )

            # Play audio (note: elevenlabs.play is blocking, so we can't easily interrupt mid-playback)
            # For true mid-speech interruption, we'd need to use streaming playback
            if not self.should_stop_speaking:
                play(audio)

            return audio

        except Exception as e:
            print(f"TTS Error: {e}")
            return None
        finally:
            self.is_speaking = False
            self.stop_listening = True
            if self.listening_thread:
                self.listening_thread.join(timeout=1.0)
    
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
        """Main run loop - continuously listen, transcribe, respond."""
        print("\n" + "=" * 50)
        print("Parrot Voice Bot - Ready!")
        print("=" * 50)
        print("\nSay 'Hey Parrot' followed by your question.")
        print("Examples:")
        print("  - 'Hey Parrot, why did we choose Stripe?'")
        print("  - 'Parrot, what happened with Legal approval?'")
        print("  - 'Hey Parrot, who made the checkout decision?'")
        print("\nInterruption commands (while Parrot is speaking):")
        print("  - 'Hey Parrot, [new question]' - ask a new question")
        print("  - 'Hey Parrot, stop' - stop the current response")
        print("  - 'Hey Parrot, thank you' - get a friendly acknowledgment")
        print("\nPress Ctrl+C to stop.\n")

        pending_question = None

        try:
            while True:
                # Check if there's a pending question from an interrupt
                if pending_question:
                    question = pending_question
                    pending_question = None
                    print(f"Question: \"{question}\"")
                    response = self._query(question)
                    self._speak(response)

                    # Check for any interrupts that happened during speech
                    try:
                        interrupt_type, interrupt_data = self.interrupt_queue.get_nowait()
                        if interrupt_type == "new_question":
                            pending_question = interrupt_data
                        elif interrupt_type == "thank_you":
                            acknowledgment = self._get_acknowledgment_response()
                            self._speak(acknowledgment, allow_interrupts=False)
                    except queue.Empty:
                        pass

                    print("")  # Blank line after response
                    continue

                print("Listening...", end=" ", flush=True)

                audio = self._record_audio()

                # Skip if audio is too quiet (silence)
                audio_level = np.abs(audio).mean()
                if audio_level < 50:
                    print("(silence)")
                    continue

                transcript = self._transcribe(audio)

                if not transcript.strip():
                    print("(no speech)")
                    continue

                print(f"Heard: \"{transcript}\"")

                # Check for thank you first (standalone, not during speech)
                if self._detect_thank_you(transcript):
                    acknowledgment = self._get_acknowledgment_response()
                    self._speak(acknowledgment, allow_interrupts=False)
                    print("")
                    continue

                # Check for wake word
                detected, question = self._detect_wake_word(transcript)

                if detected:
                    print(f"Question: \"{question}\"")
                    response = self._query(question)
                    self._speak(response)

                    # Check for any interrupts that happened during speech
                    try:
                        interrupt_type, interrupt_data = self.interrupt_queue.get_nowait()
                        if interrupt_type == "new_question":
                            pending_question = interrupt_data
                        elif interrupt_type == "thank_you":
                            acknowledgment = self._get_acknowledgment_response()
                            self._speak(acknowledgment, allow_interrupts=False)
                    except queue.Empty:
                        pass

                    print("")  # Blank line after response
                else:
                    print("(no wake word)\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
