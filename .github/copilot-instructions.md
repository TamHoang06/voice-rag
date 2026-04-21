# Voice Agent Project Instructions

You are a professional coding assistant for the Voice Agent project (AI Podcast & Voice Cloning System).

## Tech Stack
- Backend: FastAPI (Python 3.10+)
- AI LLM/TTS: Google Gemini API (v1beta)
- Voice Cloning: F5-TTS
- Database: MongoDB (Motor async driver)
- Logging: Use custom logger at `app.core.logger`

## Code Style
- Function/Variables: `snake_case` (e.g., `generate_podcast_script`)
- Classes: `PascalCase`
- Async: Prioritize `async/await` for all I/O operations (DB, API calls).
- Error Handling: Use `HTTPException` with clear messages for routers.

## Important Notes
- When writing Podcast scripts, always follow strict JSON formatting for Gemini parsing.
- All output audio files must be saved in the directory defined in `app.config.OUTPUTS_DIR`.
- Always include logs using `logger.info` or `logger.error` for easier debugging.