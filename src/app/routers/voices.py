from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ..config import AVAILABLE_VOICES

SUPPORTED_BUILTIN_VOICE_PROVIDERS = ["gemini"]

router = APIRouter(prefix="/voices", tags=["Voices"])

def _supported_voices() -> Dict[str, List[Dict[str, Any]]]:
    return {k: v for k, v in AVAILABLE_VOICES.items() if k in SUPPORTED_BUILTIN_VOICE_PROVIDERS}


@router.get("/available", response_model=Dict[str, List[Dict[str, Any]]])
async def get_available_voices():
    """Get all available voices from supported providers."""
    return _supported_voices()


@router.get("/available/{provider}", response_model=List[Dict[str, Any]])
async def get_provider_voices(provider: str):
    """Get available voices for a specific provider."""
    supported = _supported_voices()
    if provider not in supported:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found or unsupported")
    return supported[provider]


@router.get("/providers")
async def get_voice_providers():
    """Get list of available voice providers."""
    return {"providers": list(_supported_voices().keys())}
