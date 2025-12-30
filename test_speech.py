"""Test script for Deepgram speech processing."""

import asyncio
import logging
from app.speech.stt import DeepgramSTTSimple
from app.speech.tts import DeepgramTTS, TTSVoiceConfig
from app.speech.processor import SpeechProcessor
from app.utils.audio_utils import validate_telephony_audio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tts():
    """Test Text-to-Speech generation."""
    print("\n" + "="*60)
    print("Testing Deepgram TTS")
    print("="*60)
    
    # Test cases
    test_texts = [
        "Welcome to our banking service. How may I help you today?",
        "Your O T P is 1 2 3 4 5 6. This code is valid for 5 minutes.",
        "Thank you for calling. Your account balance is Rupees 50,000. Goodbye.",
    ]
    
    tts = DeepgramTTS(voice=TTSVoiceConfig.ENGLISH_NEUTRAL)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: Generating TTS for: '{text}'")
        
        try:
            audio_path = await tts.synthesize(text, cache=True)
            
            if audio_path:
                print(f"✓ Success! Audio saved to: {audio_path}")
                
                # Validate audio
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                    if validate_telephony_audio(audio_data):
                        print(f"✓ Audio validated for telephony")
                    else:
                        print(f"✗ Audio validation failed")
            else:
                print(f"✗ Failed to generate audio")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    print("\n" + "="*60)


async def test_stt():
    """Test Speech-to-Text transcription."""
    print("\n" + "="*60)
    print("Testing Deepgram STT")
    print("="*60)
    
    # Note: This requires a valid audio URL
    # For testing, you would need to provide an actual audio file URL
    print("\nSTT Test: Requires valid audio URL")
    print("Skipping automated test - STT will be tested with real calls")
    
    # Example usage (commented out):
    # stt = DeepgramSTTSimple(language="en-IN")
    # transcript = await stt.transcribe_url("https://example.com/audio.wav")
    # print(f"Transcript: {transcript}")
    
    print("\n" + "="*60)


async def test_speech_processor():
    """Test speech processor abstraction."""
    print("\n" + "="*60)
    print("Testing Speech Processor")
    print("="*60)
    
    # Test TTS generation through processor
    test_text = "This is a test of the speech processor abstraction layer."
    
    print(f"\nGenerating speech: '{test_text}'")
    
    try:
        audio_path = await SpeechProcessor.generate_speech(
            text=test_text,
            language="en-IN",
            cache=True
        )
        
        if audio_path:
            print(f"✓ Success! Audio path: {audio_path}")
        else:
            print(f"✗ Failed to generate speech")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # Test text sanitization
    print("\nTesting text sanitization:")
    test_cases = [
        ("Your OTP is 123456", "Your O T P is 123456"),
        ("Pay Rs. 500 via UPI", "Pay Rupees 500 via U P I"),
        ("Complete your KYC & PAN verification", "Complete your K Y C and P A N verification"),
    ]
    
    for original, expected in test_cases:
        sanitized = SpeechProcessor._sanitize_text_for_tts(original)
        status = "✓" if sanitized == expected else "✗"
        print(f"{status} '{original}' → '{sanitized}'")
    
    print("\n" + "="*60)


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DEEPGRAM SPEECH PROCESSING TESTS")
    print("="*60)
    
    try:
        await test_tts()
        await test_stt()
        await test_speech_processor()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
