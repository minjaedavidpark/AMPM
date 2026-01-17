"""
Google Meet Bot Interface
=========================
Bot that joins Google Meet and responds to questions.

Two modes:
- DemoMeetBot: Type questions in terminal, bot speaks in meeting
- MeetBot: Live audio - listens to meeting and responds
"""

import os
import sys
import asyncio
import time
import tempfile
import wave
import io
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright
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
RECORD_SECONDS = 6

# Browser profile directory
PROFILE_DIR = Path(__file__).parent.parent.parent / ".browser_profile"

# Wake words
WAKE_WORDS = ["hey ampm", "ampm,", "ampm ", "hey am pm", "hey amp", "a]mpm"]


class DemoMeetBot:
    """
    Google Meet bot - Demo version.

    Type questions in the terminal and the bot speaks the answer
    through your speakers into the meeting.

    Uses Backboard API for persistent memory across sessions.
    """

    def __init__(
        self,
        meeting_url: str,
        data_path: Optional[str] = None,
        use_backboard: bool = True,
        fast_mode: bool = True
    ):
        """
        Initialize the demo meet bot.

        Args:
            meeting_url: Google Meet URL to join.
            data_path: Optional path to meeting data JSON file.
            use_backboard: Use Backboard API for memory (default True).
            fast_mode: Use Backboard's integrated RAG for faster responses (default True).
        """
        self.meeting_url = meeting_url
        self.elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.browser = None
        self.page = None
        self.fast_mode = fast_mode and use_backboard

        # Initialize memory system with persistence
        config_dir = str(PROFILE_DIR.parent / ".ampm")
        self.graph = MeetingGraph()
        self.embeddings = EmbeddingStore(
            use_backboard=use_backboard,
            config_dir=config_dir,
            persist=True
        )
        self.loader = MeetingLoader(self.graph, self.embeddings)
        self.query_engine = QueryEngine(self.graph, self.embeddings)

        # Load meeting data
        if data_path:
            self.loader.load_file(data_path)
        else:
            try:
                self.loader.load_sample_data()
            except FileNotFoundError:
                print("Note: No sample data found, using Backboard memory only")

    async def start(self):
        """Launch browser and join meeting."""
        print(f"\n{'='*60}")
        print("AMPM Google Meet Bot - DEMO MODE")
        print(f"{'='*60}")
        print(f"\nMeeting: {self.meeting_url}")

        PROFILE_DIR.mkdir(exist_ok=True)

        async with async_playwright() as p:
            print("\nLaunching browser...")

            self.browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                permissions=['microphone', 'camera'],
                viewport={'width': 1280, 'height': 800},
            )

            self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()

            await self._ensure_google_login()
            await self._join_meeting()
            await self._demo_loop()

    async def _ensure_google_login(self):
        """Check Google login."""
        print("\nChecking Google login...")
        await self.page.goto("https://accounts.google.com", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(2)

        url = self.page.url
        if "myaccount.google.com" in url or "SignOutOptions" in url:
            print("Logged into Google!")
        else:
            print("\nLog into Google in the browser, then press Enter...")
            await asyncio.get_event_loop().run_in_executor(None, input)

    async def _join_meeting(self):
        """Join the meeting."""
        print(f"\nOpening meeting...")
        # Use domcontentloaded instead of load - faster and more reliable for SPAs
        # Increase timeout to 60 seconds for slow connections
        await self.page.goto(self.meeting_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)

        # Turn off camera/mic
        try:
            cam = await self.page.query_selector('[aria-label*="Turn off camera"]')
            if cam:
                await cam.click()
        except:
            pass

        try:
            mic = await self.page.query_selector('[aria-label*="Turn off microphone"]')
            if mic:
                await mic.click()
        except:
            pass

        await asyncio.sleep(1)

        # Click join
        try:
            join = await self.page.wait_for_selector(
                'button:has-text("Join now"), button:has-text("Ask to join")',
                timeout=10000
            )
            if join:
                await join.click()
        except:
            print("Click 'Join' manually")

        await asyncio.sleep(5)
        print("\nIn meeting!")

    async def _demo_loop(self):
        """Main demo loop - type questions."""
        print("\n" + "=" * 60)
        print("DEMO MODE - Type questions, AMPM responds with voice")
        print("=" * 60)
        print("\nExample questions:")
        print("  - Why did we choose Stripe?")
        print("  - What happened with Legal approval?")
        print("  - Who is on the team?")
        print("\nType 'q' to quit.\n")

        while True:
            try:
                question = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input(">>> Question: ")
                )

                if question.lower() == 'q':
                    break

                if question.strip():
                    await self._respond(question)

            except KeyboardInterrupt:
                break

        await self._cleanup()

    async def _respond(self, question: str):
        """Generate and speak response with timing."""
        total_start = time.time()

        # Query memory - use fast mode (Backboard RAG) if available
        print("Thinking...", end=" ", flush=True)
        llm_start = time.time()

        if self.fast_mode:
            result = self.query_engine.query_fast(question)
        else:
            result = self.query_engine.query(question)
        answer = result.answer

        llm_time = time.time() - llm_start
        print(f"({llm_time:.2f}s)")

        print(f"\nAMPM: {answer}\n")

        # TTS
        print("Speaking...", end=" ", flush=True)
        tts_start = time.time()

        audio = self.elevenlabs.text_to_speech.convert(
            text=answer,
            voice_id=self.voice_id,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128"
        )
        play(audio)

        tts_time = time.time() - tts_start
        total_time = time.time() - total_start

        print(f"Done!")
        print(f"LLM: {llm_time:.2f}s | TTS: {tts_time:.2f}s | Total: {total_time:.2f}s\n")

    async def _cleanup(self):
        """Leave meeting."""
        print("\nLeaving...")
        if self.browser:
            await self.browser.close()
        print("Goodbye!")


class MeetBot:
    """
    Google Meet bot - Live audio version.

    Listens to meeting audio and responds when wake word is detected.
    Requires virtual audio routing (e.g., BlackHole on macOS).

    Uses Backboard API for persistent memory across sessions.
    """

    def __init__(
        self,
        meeting_url: str,
        data_path: Optional[str] = None,
        use_backboard: bool = True,
        fast_mode: bool = True
    ):
        """
        Initialize the live meet bot.

        Args:
            meeting_url: Google Meet URL to join.
            data_path: Optional path to meeting data JSON file.
            use_backboard: Use Backboard API for memory (default True).
            fast_mode: Use Backboard's integrated RAG for faster responses (default True).
        """
        self.meeting_url = meeting_url
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.browser = None
        self.page = None
        self.is_listening = True
        self.is_speaking = False
        self.fast_mode = fast_mode and use_backboard

        # Initialize memory system with persistence
        config_dir = str(PROFILE_DIR.parent / ".ampm")
        self.graph = MeetingGraph()
        self.embeddings = EmbeddingStore(
            use_backboard=use_backboard,
            config_dir=config_dir,
            persist=True
        )
        self.loader = MeetingLoader(self.graph, self.embeddings)
        self.query_engine = QueryEngine(self.graph, self.embeddings)

        # Load meeting data
        if data_path:
            self.loader.load_file(data_path)
        else:
            try:
                self.loader.load_sample_data()
            except FileNotFoundError:
                print("Note: No sample data found, using Backboard memory only")

    async def start(self):
        """Launch browser and join meeting."""
        print(f"\n{'='*60}")
        print("AMPM Google Meet Bot")
        print(f"{'='*60}")
        print(f"\nMeeting URL: {self.meeting_url}")
        print("\nUse headphones to prevent audio feedback!")

        PROFILE_DIR.mkdir(exist_ok=True)

        async with async_playwright() as p:
            print("\nLaunching browser...")

            self.browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--use-fake-ui-for-media-stream',
                ],
                permissions=['microphone', 'camera', 'notifications'],
                viewport={'width': 1280, 'height': 800},
            )

            self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()

            await self._ensure_google_login()
            await self._join_meeting()
            await self._listen_loop()

    async def _ensure_google_login(self):
        """Check Google login status."""
        print("\nChecking Google login...")
        await self.page.goto("https://accounts.google.com", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(2)

        url = self.page.url
        if "myaccount.google.com" in url or "accounts.google.com/SignOutOptions" in url:
            print("Already logged into Google!")
        else:
            print("\n" + "=" * 60)
            print("Please log into your Google account in the browser window")
            print("Then press Enter here to continue...")
            print("=" * 60)
            await asyncio.get_event_loop().run_in_executor(None, input)
            print("Continuing...")

    async def _join_meeting(self):
        """Navigate to meeting and handle join flow."""
        print(f"\nOpening meeting: {self.meeting_url}")
        # Use domcontentloaded instead of load - faster and more reliable for SPAs
        # Increase timeout to 60 seconds for slow connections
        await self.page.goto(self.meeting_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)

        # Turn off camera
        try:
            await asyncio.sleep(2)
            camera_btn = await self.page.query_selector(
                '[aria-label*="Turn off camera"], [aria-label*="camera" i][data-is-muted="false"]'
            )
            if camera_btn:
                await camera_btn.click()
                print("Camera off")
        except Exception as e:
            print(f"Camera: {e}")

        # Turn off mic
        try:
            mic_btn = await self.page.query_selector(
                '[aria-label*="Turn off microphone"], [aria-label*="microphone" i][data-is-muted="false"]'
            )
            if mic_btn:
                await mic_btn.click()
                print("Meet mic off")
        except Exception as e:
            print(f"Mic: {e}")

        await asyncio.sleep(1)

        # Click Join
        try:
            join_btn = await self.page.wait_for_selector(
                'button:has-text("Join now"), button:has-text("Ask to join")',
                timeout=10000
            )
            if join_btn:
                await join_btn.click()
                print("Joining...")
        except:
            print("Click 'Join now' manually in the browser")

        print("\nWaiting to enter meeting...")
        await asyncio.sleep(5)

        print("\n" + "=" * 60)
        print("AMPM is ready!")
        print("=" * 60)
        print("\nSay 'Hey AMPM' followed by your question.")
        print("Example: 'Hey AMPM, why did we choose Stripe?'")
        print("\nPress Ctrl+C to leave.\n")

    async def _listen_loop(self):
        """Continuously listen for questions."""
        while self.is_listening:
            if self.is_speaking:
                await asyncio.sleep(0.5)
                continue

            try:
                print("Listening...", end=" ", flush=True)

                audio = await asyncio.get_event_loop().run_in_executor(
                    None, self._record_audio
                )

                transcript = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._transcribe(audio)
                )

                if transcript.strip():
                    print(f"Heard: \"{transcript}\"")
                    detected, question = self._detect_wake_word(transcript)

                    if detected:
                        print(f"\nQuestion: \"{question}\"")
                        await self._respond(question)
                else:
                    print("(silence)")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")
                await asyncio.sleep(1)

    def _record_audio(self) -> np.ndarray:
        """Record from microphone."""
        audio = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16'
        )
        sd.wait()
        return audio

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe with Whisper."""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        buffer.seek(0)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(buffer.read())
            temp_path = f.name

        try:
            with open(temp_path, "rb") as audio_file:
                result = self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            return result.text
        finally:
            os.unlink(temp_path)

    def _detect_wake_word(self, text: str) -> tuple:
        """Check for wake word."""
        text_lower = text.lower().strip()
        for wake in WAKE_WORDS:
            if wake in text_lower:
                idx = text_lower.find(wake)
                question = text[idx + len(wake):].strip().lstrip(",.:;!? ")
                return True, question if question else text
        return False, ""

    async def _respond(self, question: str):
        """Generate and speak response."""
        self.is_speaking = True
        print("Thinking...", end=" ", flush=True)
        start_time = time.time()

        try:
            # Use fast mode (Backboard RAG) if available
            if self.fast_mode:
                result = self.query_engine.query_fast(question)
            else:
                result = self.query_engine.query(question)
            answer = result.answer

            llm_time = time.time() - start_time
            print(f"({llm_time:.2f}s)")

            print(f"\nAMPM: {answer}\n")

            print("Speaking...", end=" ", flush=True)
            tts_start = time.time()
            audio = self.elevenlabs.text_to_speech.convert(
                text=answer,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )
            play(audio)
            tts_time = time.time() - tts_start

            total_time = time.time() - start_time
            print(f"Total response time: {total_time:.2f}s")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.is_speaking = False
            print("Listening again...\n")

    async def cleanup(self):
        """Clean up."""
        self.is_listening = False
        if self.browser:
            await self.browser.close()
