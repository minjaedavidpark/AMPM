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
import base64
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright
import sounddevice as sd
import numpy as np
from openai import OpenAI
from elevenlabs import ElevenLabs
from elevenlabs.play import play
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

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
# WAKE_WORDS = ["hey ampm", "ampm,", "ampm ", "hey am pm", "hey amp", "a]mpm"]
WAKE_WORDS = ["hey parrot", "parrot,", "parrot ", "hey parrot pm", "hey parrot", "a]parrot"]


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
        self.last_spoken_audio = None  # Store last spoken audio for echo detection
        self.last_speak_time = 0  # Track when bot last spoke
        self.audio_context_initialized = False  # Track if audio context is set up

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
        print("Parrot Google Meet Bot")
        print(f"{'='*60}")
        print(f"\nMeeting URL: {self.meeting_url}")
        print("\n🔴 CRITICAL: Use HEADPHONES (not speakers) to prevent echo!")
        print("   If you use speakers, your voice will echo back through bot's mic!")

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

        # Turn off camera (but keep mic ON for audio injection)
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

        # Keep mic ON - we need it to inject audio into the meeting
        # The mic will be controlled by virtual audio routing
        # We'll unmute/mute programmatically when speaking
        print("Microphone enabled (will be controlled automatically)")
        
        # Wait a bit for meeting to fully load
        await asyncio.sleep(3)
        
        # Ensure mic is initially muted (we'll unmute when speaking)
        await self._set_mic_muted(True)

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
        print("Parrot is ready!")
        print("=" * 60)
        print("\n🎤 Audio Setup")
        print("=" * 60)
        print("\nLISTENING:")
        print("  • Bot will try to capture from Google Meet tab")
        print("  • Falls back to system microphone if needed")
        print("  • Make sure your mic can hear the meeting:")
        print("    - If using speakers: Mic should pick up meeting audio")
        print("    - If using headphones: Use headphones with mic")
        print("\nSPEAKING:")
        print("  • Bot uses BlackHole to inject audio into Google Meet")
        print("  • Make sure:")
        print("    1. System Output = Multi-Output Device (with BlackHole)")
        print("    2. Bot's Google Meet → Settings → Microphone = BlackHole 2ch")
        print("\n💡 TIPS:")
        print("  • Speak clearly: 'Hey AMPM' followed by your question")
        print("  • Wait 4 seconds after bot speaks (prevents echo)")
        print("  • Use headphones to prevent echo")
        print("\nExample: 'Hey AMPM, why did we choose Stripe?'")
        print("\nPress Ctrl+C to leave.\n")

    async def _setup_meeting_audio_capture(self):
        """Set up JavaScript to capture audio from Google Meet using screen capture."""
        try:
            # Use getDisplayMedia to capture tab audio
            # This requires user permission but captures the actual meeting audio
            setup_script = """
            (async function() {
                window.ampmAudioCapture = {
                    mediaRecorder: null,
                    audioChunks: [],
                    stream: null,
                    initialized: false,
                    lastAudioTime: 0
                };
                
                // Function to capture audio from meeting tab
                window.ampmAudioCapture.init = async function() {
                    try {
                        // Request screen/tab capture with audio
                        // This will show a permission dialog - user needs to select the Google Meet tab
                        console.log('Parrot: Requesting screen capture with audio...');
                        console.log('Parrot: Please select the Google Meet tab when prompted');
                        
                        // Note: This requires user interaction, so we'll use a different approach
                        // Instead, we'll capture from the audio elements in the page
                        const audioElements = document.querySelectorAll('audio');
                        console.log('Parrot: Found', audioElements.length, 'audio elements');
                        
                        if (audioElements.length > 0) {
                            // Create audio context and connect to first audio element
                            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            const audioElement = audioElements[0];
                            
                            // Create source from audio element
                            const source = audioContext.createMediaElementSource(audioElement);
                            
                            // Create analyser
                            const analyser = audioContext.createAnalyser();
                            analyser.fftSize = 2048;
                            analyser.smoothingTimeConstant = 0.3;
                            
                            source.connect(analyser);
                            analyser.connect(audioContext.destination);
                            
                            this.analyser = analyser;
                            this.audioContext = audioContext;
                            this.bufferLength = analyser.frequencyBinCount;
                            this.dataArray = new Uint8Array(this.bufferLength);
                            
                            this.initialized = true;
                            console.log('Parrot: Audio capture initialized from audio element');
                            return true;
                        }
                        
                        return false;
                    } catch (error) {
                        console.error('Parrot: Error initializing audio capture:', error);
                        return false;
                    }
                };
                
                // Function to get audio data
                window.ampmAudioCapture.getAudioData = function() {
                    if (!this.initialized || !this.analyser) {
                        return null;
                    }
                    this.analyser.getByteTimeDomainData(this.dataArray);
                    const now = Date.now();
                    if (now - this.lastAudioTime > 100) {  // Sample every 100ms
                        this.lastAudioTime = now;
                        return Array.from(this.dataArray);
                    }
                    return null;
                };
                
                // Try to initialize after a delay
                setTimeout(() => {
                    window.ampmAudioCapture.init().then(success => {
                        if (!success) {
                            console.log('Parrot: Audio capture initialization failed, will use system mic');
                        }
                    });
                }, 3000);
                
                return true;
            })();
            """
            
            await self.page.evaluate(setup_script)
            await asyncio.sleep(3)  # Wait for initialization
            
            # Check if it worked
            initialized = await self.page.evaluate("""
                () => window.ampmAudioCapture && window.ampmAudioCapture.initialized
            """)
            
            if initialized:
                self.audio_context_initialized = True
                print("✅ Audio capture from Google Meet initialized")
            else:
                print("⚠️  Meeting audio capture not available, using system microphone")
                self.audio_context_initialized = False
            
        except Exception as e:
            print(f"⚠️  Could not set up meeting audio capture: {e}")
            print("   Using system microphone instead...")
            self.audio_context_initialized = False

    async def _capture_meeting_audio(self) -> Optional[np.ndarray]:
        """Capture audio from Google Meet tab."""
        if not self.audio_context_initialized:
            return None
            
        try:
            # Get audio data from JavaScript
            audio_data = await self.page.evaluate("""
                () => {
                    if (window.ampmAudioCapture && window.ampmAudioCapture.initialized) {
                        return window.ampmAudioCapture.getAudioData();
                    }
                    return null;
                }
            """)
            
            if audio_data is None or len(audio_data) == 0:
                return None
            
            # Convert to numpy array and process
            audio_array = np.array(audio_data, dtype=np.float32)
            # Normalize from 0-255 to -1 to 1, then to int16
            audio_array = ((audio_array - 128) / 128.0 * 32767).astype(np.int16)
            
            # Resample if needed (analyser gives us frequency data, we need time domain)
            # For now, just return what we have
            return audio_array
            
        except Exception as e:
            # Silently fail and fall back to system mic
            return None

    async def _listen_loop(self):
        """Continuously listen for questions from Google Meet."""
        while self.is_listening:
            if self.is_speaking:
                await asyncio.sleep(0.5)
                continue

            try:
                print("Listening...", end=" ", flush=True)

                # Try to capture from meeting first, fallback to system mic
                audio = await self._capture_meeting_audio()
                using_meeting_audio = audio is not None
                
                if audio is None:
                    # Fallback to system mic
                    audio = await asyncio.get_event_loop().run_in_executor(
                        None, self._record_audio
                    )
                    using_meeting_audio = False
                
                # Quick check: if all zeros, skip transcription
                if audio is None or len(audio) == 0 or np.all(audio == 0):
                    print("(no audio detected)")
                    await asyncio.sleep(0.5)
                    continue

                # Check audio level
                audio_level = np.abs(audio).mean()
                max_level = np.abs(audio).max()
                source = "meeting" if using_meeting_audio else "mic"
                print(f"[{source} Level: {audio_level:.0f}, Max: {max_level:.0f}]", end=" ", flush=True)

                # Skip audio if too soon after bot spoke (echo prevention)
                time_since_speak = time.time() - self.last_speak_time
                if time_since_speak < 4.0:  # Wait 4 seconds after bot speaks
                    print("(skipping - too soon after bot spoke, preventing echo)")
                    continue

                # Check audio level - be more lenient for system mic
                threshold = 5 if using_meeting_audio else 20  # Higher threshold for mic (more noise)
                if audio_level < threshold:
                    print("(silence - audio too quiet)")
                    continue
                
                # Additional echo check: if audio is very loud right after speaking, skip it
                if time_since_speak < 6.0 and audio_level > 5000:
                    print("(skipping - likely echo, too loud too soon)")
                    continue

                transcript = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._transcribe(audio)
                )

                if transcript.strip():
                    print(f"Heard: \"{transcript}\"")
                    detected, question = self._detect_wake_word(transcript)

                    if detected:
                        print(f"\n✅ Wake word detected! Question: \"{question}\"")
                        await self._respond(question)
                    else:
                        print(" (no wake word)")
                else:
                    print("(no speech)")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

    async def _set_mic_muted(self, muted: bool):
        """
        Mute or unmute the microphone in Google Meet.
        
        Args:
            muted: True to mute, False to unmute
        """
        try:
            await asyncio.sleep(0.2)
            
            # Try multiple selectors for the mic button
            selectors = [
                f'button[aria-label*="{"Turn off" if not muted else "Turn on"} microphone" i]',
                f'button[aria-label*="microphone" i][data-is-muted="{"false" if muted else "true"}"]',
                f'button[data-is-muted="{"false" if muted else "true"}"]',
                '[data-mute-state="false"]' if muted else '[data-mute-state="true"]',
            ]
            
            for selector in selectors:
                try:
                    mic_btn = await self.page.query_selector(selector)
                    if mic_btn:
                        aria_label = await mic_btn.get_attribute('aria-label') or ''
                        is_muted = 'Turn on' in aria_label or 'unmute' in aria_label.lower()
                        
                        if (muted and not is_muted) or (not muted and is_muted):
                            await mic_btn.click()
                            await asyncio.sleep(0.3)
                            return True
                        return True  # Already in desired state
                except:
                    continue
            
            # Fallback: try JavaScript
            result = await self.page.evaluate(f"""
                (() => {{
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const micBtn = buttons.find(btn => {{
                        const label = btn.getAttribute('aria-label') || '';
                        return label.toLowerCase().includes('microphone') || 
                               label.toLowerCase().includes('mic');
                    }});
                    if (micBtn) {{
                        const label = micBtn.getAttribute('aria-label') || '';
                        const isMuted = micBtn.getAttribute('data-is-muted') === 'true' ||
                                       label.includes('Turn on');
                        const shouldMute = {str(muted).lower()};
                        if (isMuted !== shouldMute) {{
                            micBtn.click();
                            return true;
                        }}
                        return true; // Already in desired state
                    }}
                    return false;
                }})();
            """)
            
            return result if result else False
            
        except Exception as e:
            print(f"  ⚠️  Could not {'mute' if muted else 'unmute'} mic: {e}")
            return False

    async def _check_mic_muted(self) -> bool:
        """Check if the microphone is currently muted in Google Meet."""
        try:
            result = await self.page.evaluate("""
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const micBtn = buttons.find(btn => {
                        const label = btn.getAttribute('aria-label') || '';
                        return label.toLowerCase().includes('microphone') || 
                               label.toLowerCase().includes('mic');
                    });
                    if (micBtn) {
                        const label = micBtn.getAttribute('aria-label') || '';
                        const isMuted = micBtn.getAttribute('data-is-muted') === 'true' ||
                                       label.includes('Turn on');
                        return isMuted;
                    }
                    return null;
                })();
            """)
            return result if result is not None else True  # Default to muted if can't determine
        except:
            return True  # Default to muted on error

    def _record_audio(self) -> np.ndarray:
        """
        Record from microphone.
        
        IMPORTANT: Use HEADPHONES to prevent echo!
        - If using speakers: Your voice will echo back through bot's mic
        - If using headphones: No echo, bot only hears your direct voice
        
        This records from your system's DEFAULT INPUT DEVICE.
        Make sure your earphones mic is set as the default input.
        
        NOTE: If Google Meet is using the mic, you might need to:
        - Use a different mic for the bot, OR
        - Make sure the mic can be shared between processes
        """
        # List available devices for debugging
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            input_device = devices[default_input]
            # Only print once to avoid spam
            if not hasattr(self, '_device_logged'):
                print(f"\n📱 Using input device: {input_device['name']} (index {default_input})")
                print(f"   Sample rate: {input_device.get('default_samplerate', 'unknown')} Hz")
                print(f"   Channels: {input_device.get('max_input_channels', 'unknown')}")
                print(f"\n⚠️  If bot doesn't hear you:")
                print(f"   1. Check mic permissions: System Preferences → Security → Microphone")
                print(f"   2. Make sure Google Meet isn't blocking mic access")
                print(f"   3. Try speaking louder or closer to mic")
                print(f"   4. Check audio levels in terminal output\n")
                self._device_logged = True
        except Exception as e:
            print(f"⚠️  Could not query audio devices: {e}")
        
        try:
            audio = sd.rec(
                int(RECORD_SECONDS * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype='int16',
                device=default_input if 'default_input' in locals() else None
            )
            sd.wait()
            
            # Check if we actually got audio (not just zeros)
            if np.all(audio == 0):
                if not hasattr(self, '_zero_audio_warned'):
                    print("⚠️  WARNING: Recording returned all zeros - mic might not be working!")
                    print("   Check: System Preferences → Security → Microphone → Terminal permission")
                    self._zero_audio_warned = True
            
            return audio
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
            # Return silent audio to prevent crash
            return np.zeros((int(RECORD_SECONDS * SAMPLE_RATE), CHANNELS), dtype='int16')

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
        """Check for wake word with improved detection."""
        text_lower = text.lower().strip()
        
        # Remove common transcription errors
        text_lower = text_lower.replace("hey parrot par", "hey parrot")
        text_lower = text_lower.replace("hey parrot", "hey parrot")
        text_lower = text_lower.replace("parrot parrot", "parrot")
        text_lower = text_lower.replace("part", "parrot")
        
        # Check for wake words (more flexible matching)
        for wake in WAKE_WORDS:
            # Try exact match first
            if wake in text_lower:
                idx = text_lower.find(wake)
                question = text[idx + len(wake):].strip().lstrip(",.:;!? ")
                return True, question if question else text
            
            # Try fuzzy match (wake word might be split)
            wake_parts = wake.split()
            if len(wake_parts) > 1:
                # Check if all parts appear in order
                last_idx = -1
                all_found = True
                for part in wake_parts:
                    idx = text_lower.find(part, last_idx + 1)
                    if idx == -1:
                        all_found = False
                        break
                    last_idx = idx
                
                if all_found:
                    question = text[last_idx + len(wake_parts[-1]):].strip().lstrip(",.:;!? ")
                    return True, question if question else text
        
        return False, ""

    async def _respond(self, question: str):
        """Generate and speak response into the meeting."""
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

            print(f"\Parrot: {answer}\n")

            print("Speaking into meeting...", end=" ", flush=True)
            tts_start = time.time()
            
            # Generate TTS audio (returns generator, need to convert to bytes)
            audio_generator = self.elevenlabs.text_to_speech.convert(
                text=answer,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio_generator)
            
            # Store audio and time for echo detection
            self.last_spoken_audio = audio_bytes
            self.last_speak_time = time.time()
            
            # CRITICAL: Unmute mic in Google Meet BEFORE playing audio
            print("\n🔓 Unmuting bot's mic in Google Meet...")
            await self._set_mic_muted(False)
            await asyncio.sleep(0.5)  # Wait for unmute to take effect
            
            # Verify unmute worked
            is_muted = await self._check_mic_muted()
            if is_muted:
                print("⚠️  WARNING: Bot's mic is still muted! Audio won't be heard in meeting.")
                print("   → Manually unmute the bot in Google Meet, then try again")
            else:
                print("✓ Bot's mic is unmuted")
            
            # Inject audio into Google Meet
            audio_duration = await self._inject_audio_to_meeting(audio_bytes)
            
            # Wait for audio to finish playing (with buffer)
            await asyncio.sleep(audio_duration + 0.5)
            
            # Mute mic again after speaking
            print("🔇 Muting bot's mic...")
            await self._set_mic_muted(True)
            await asyncio.sleep(0.3)
            
            # Wait a bit more before resuming listening (echo prevention)
            await asyncio.sleep(1.0)
            
            tts_time = time.time() - tts_start
            total_time = time.time() - start_time
            print(f"Done! (Total: {total_time:.2f}s)")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            # Make sure to mute again on error
            try:
                await self._set_mic_muted(True)
            except:
                pass
        finally:
            self.is_speaking = False
            print("Listening again...\n")

    async def _inject_audio_to_meeting(self, audio_bytes: bytes) -> float:
        """
        Inject audio into Google Meet meeting via BlackHole.
        
        The audio is played to system output, which should be Multi-Output Device.
        Multi-Output Device routes to both:
        - Built-in Output (you hear it)
        - BlackHole 2ch (Google Meet captures it)
        
        Returns:
            float: Estimated duration of the audio in seconds
        """
        estimated_duration = (len(audio_bytes) * 8) / 128000
        
        print("\n🔊 Playing audio...")
        print("   → Make sure System Output = Multi-Output Device (with BlackHole)")
        print("   → Make sure Bot's Google Meet → Microphone = BlackHole 2ch")
        
        try:
            # Play audio to system output
            # If Multi-Output Device is set as system output, it will go to:
            # 1. Built-in Output (you hear it)
            # 2. BlackHole 2ch (Google Meet captures it)
            play(audio_bytes)
            
            print(f"✓ Audio played to system output")
            print(f"   Duration: ~{estimated_duration:.1f}s")
            print(f"   → Check if others in meeting can hear it")
            
            return estimated_duration
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            print("\n" + "="*60)
            print("AUDIO ROUTING SETUP REQUIRED")
            print("="*60)
            print("\nTo fix this:")
            print("  1. System Preferences → Sound → Output")
            print("     → Select 'Multi-Output Device' (with BlackHole)")
            print("  2. In Bot's Google Meet → Settings → Audio")
            print("     → Microphone = 'BlackHole 2ch'")
            print("  3. Make sure Multi-Output Device includes:")
            print("     ✅ Built-in Output")
            print("     ✅ BlackHole 2ch")
            print("\nSee SETUP_BLACKHOLE.md for detailed instructions.")
            print("="*60 + "\n")
            return estimated_duration

    async def _inject_audio_via_cdp(self, audio_bytes: bytes):
        """
        Attempt to inject audio via Chrome DevTools Protocol.
        
        Note: This is a workaround that may not work reliably. The proper solution
        is to use virtual audio routing (BlackHole, VB-Audio, etc.) as documented
        in the README.
        """
        try:
            # Encode audio as base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Try to play audio in the browser context
            # This won't route to the mic automatically, but might work if
            # virtual audio is already configured
            result = await self.page.evaluate(f"""
                (async function() {{
                    try {{
                        const audio = new Audio('data:audio/mp3;base64,{audio_base64}');
                        audio.volume = 1.0;
                        await audio.play();
                        await new Promise(resolve => {{
                            audio.onended = resolve;
                            setTimeout(resolve, 30000); // 30s timeout
                        }});
                        return true;
                    }} catch (error) {{
                        console.error('Audio playback error:', error);
                        return false;
                    }}
                }})();
            """)
            
            if not result:
                raise Exception("Audio playback in browser failed")
                
        except Exception as e:
            raise Exception(f"CDP audio injection failed: {e}")

    async def _play_to_device(self, audio_bytes: bytes, device_name: str):
        """Play audio to a specific audio device using PyAudio."""
        # This would require PyAudio and device enumeration
        # For now, we'll use the CDP method as primary
        await self._inject_audio_via_cdp(audio_bytes)

    async def cleanup(self):
        """Clean up."""
        self.is_listening = False
        if self.browser:
            await self.browser.close()
