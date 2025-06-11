# TTS Context for HypeWriter Project

## Current Status
- Successfully tested MCP speech server with text-to-speech functionality
- **Preferred voice**: `bf_emma` (Emma - British Female)
- Audio group configuration working correctly (alsa-utils + audio group membership)

## MCP Speech Server Limitations
- **Text limit**: 1000 characters maximum per request
- **No file export**: Audio plays directly through system audio only
- **Real-time only**: Cannot create audio files for distribution
- **Good for**: Writing feedback, dialogue testing, proofreading by ear

## Kokoro-FastAPI Alternative (Better for Audiobooks)
- **Location**: `/home/djole/dev/orbat/kokoro-fastapi/`
- **Capabilities**:
  - ✅ No length limits (can process full chapters)
  - ✅ File export (MP3, WAV, FLAC, etc.)
  - ✅ 60+ voices available
  - ✅ OpenAI compatibility
  - ✅ Production-ready quality
  - ✅ Local & private

## Quick Start for Kokoro-FastAPI
```bash
cd /home/djole/dev/orbat/kokoro-fastapi
./start-cpu.sh  # or ./start-gpu.sh for NVIDIA GPU
```

## Usage Example for Chapter Reading
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8880/v1", api_key="not-needed")

# Convert full chapter to audio file
with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="bf_emma",  # Your preferred voice
    input="Your entire chapter text here...",
    response_format="mp3"
) as response:
    response.stream_to_file("chapter_1.mp3")
```

## Available MCP Tools
- `mcp__speech__text_to_speech` - Basic TTS with voice selection
- `mcp__speech__text_to_speech_with_options` - TTS with speed control
- `mcp__speech__list_voices` - See all available voices
- `mcp__speech__get_model_status` - Check TTS model status

## Recommendations for HypeWriter
- Use MCP speech server for quick feedback during writing
- Use Kokoro-FastAPI for creating actual audiobook chapters
- Emma voice (`bf_emma`) provides good quality for both systems