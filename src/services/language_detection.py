"""
Language detection and multi-language transcription support
"""

import logging
from typing import Dict, List, Optional, Tuple

import whisper
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)


class LanguageDetectionService:
    """Service for detecting and handling multiple languages in audio"""

    # Whisper supported languages mapping
    WHISPER_LANGUAGES = {
        "en": "english",
        "zh": "chinese",
        "de": "german",
        "es": "spanish",
        "ru": "russian",
        "ko": "korean",
        "fr": "french",
        "ja": "japanese",
        "pt": "portuguese",
        "tr": "turkish",
        "pl": "polish",
        "ca": "catalan",
        "nl": "dutch",
        "ar": "arabic",
        "sv": "swedish",
        "it": "italian",
        "id": "indonesian",
        "hi": "hindi",
        "fi": "finnish",
        "vi": "vietnamese",
        "he": "hebrew",
        "uk": "ukrainian",
        "el": "greek",
        "ms": "malay",
        "cs": "czech",
        "ro": "romanian",
        "da": "danish",
        "hu": "hungarian",
        "ta": "tamil",
        "no": "norwegian",
        "th": "thai",
        "ur": "urdu",
        "hr": "croatian",
        "bg": "bulgarian",
        "lt": "lithuanian",
        "la": "latin",
        "mi": "maori",
        "ml": "malayalam",
        "cy": "welsh",
        "sk": "slovak",
        "te": "telugu",
        "fa": "persian",
        "lv": "latvian",
        "bn": "bengali",
        "sr": "serbian",
        "az": "azerbaijani",
        "sl": "slovenian",
        "kn": "kannada",
        "et": "estonian",
        "mk": "macedonian",
        "br": "breton",
        "eu": "basque",
        "is": "icelandic",
        "hy": "armenian",
        "ne": "nepali",
        "mn": "mongolian",
        "bs": "bosnian",
        "kk": "kazakh",
        "sq": "albanian",
        "sw": "swahili",
        "gl": "galician",
        "mr": "marathi",
        "pa": "punjabi",
        "si": "sinhala",
        "km": "khmer",
        "sn": "shona",
        "yo": "yoruba",
        "so": "somali",
        "af": "afrikaans",
        "oc": "occitan",
        "ka": "georgian",
        "be": "belarusian",
        "tg": "tajik",
        "sd": "sindhi",
        "gu": "gujarati",
        "am": "amharic",
        "yi": "yiddish",
        "lo": "lao",
        "uz": "uzbek",
        "fo": "faroese",
        "ht": "haitian creole",
        "ps": "pashto",
        "tk": "turkmen",
        "nn": "nynorsk",
        "mt": "maltese",
        "sa": "sanskrit",
        "lb": "luxembourgish",
        "my": "myanmar",
        "bo": "tibetan",
        "tl": "tagalog",
        "mg": "malagasy",
        "as": "assamese",
        "tt": "tatar",
        "haw": "hawaiian",
        "ln": "lingala",
        "ha": "hausa",
        "ba": "bashkir",
        "jw": "javanese",
        "su": "sundanese",
    }

    def __init__(self):
        self.model = None

    def detect_language_from_text(self, text: str) -> Optional[str]:
        """
        Detect language from text using langdetect

        Args:
            text: Text to analyze

        Returns:
            Language code (ISO 639-1) or None if detection fails
        """
        try:
            if not text or len(text.strip()) < 10:
                return None

            detected = detect(text)
            return detected if detected in self.WHISPER_LANGUAGES else None

        except LangDetectException:
            logger.warning("Could not detect language from text")
            return None

    def detect_language_from_audio(
        self, audio_path: str, model_size: str = "base"
    ) -> Tuple[Optional[str], float]:
        """
        Detect language from audio using Whisper

        Args:
            audio_path: Path to audio file
            model_size: Whisper model size

        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            if (
                not self.model
                or self.model.dims.n_vocab
                != whisper.load_model(model_size).dims.n_vocab
            ):
                self.model = whisper.load_model(model_size)

            # Load audio and pad/trim it to fit 30 seconds
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)

            # Make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            # Detect the spoken language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            confidence = probs[detected_language]

            return detected_language, confidence

        except Exception as e:
            logger.error(f"Error detecting language from audio: {e}")
            return None, 0.0

    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.WHISPER_LANGUAGES.copy()

    def is_language_supported(self, language_code: str) -> bool:
        """Check if language is supported by Whisper"""
        return language_code in self.WHISPER_LANGUAGES

    def get_language_name(self, language_code: str) -> Optional[str]:
        """Get full language name from code"""
        return self.WHISPER_LANGUAGES.get(language_code)

    def transcribe_with_language_detection(
        self,
        audio_path: str,
        model_size: str = "base",
        force_language: Optional[str] = None,
    ) -> Dict:
        """
        Transcribe audio with automatic language detection

        Args:
            audio_path: Path to audio file
            model_size: Whisper model size
            force_language: Force specific language (optional)

        Returns:
            Dictionary with transcription results and language info
        """
        try:
            if (
                not self.model
                or self.model.dims.n_vocab
                != whisper.load_model(model_size).dims.n_vocab
            ):
                self.model = whisper.load_model(model_size)

            # Detect language if not forced
            if force_language:
                language = force_language
                confidence = 1.0
            else:
                language, confidence = self.detect_language_from_audio(
                    audio_path, model_size
                )

            # Transcribe with detected/forced language
            result = self.model.transcribe(
                audio_path, language=language if language else None, task="transcribe"
            )

            # Add language detection info
            result["detected_language"] = language
            result["language_confidence"] = confidence
            result["language_name"] = (
                self.get_language_name(language) if language else None
            )

            return result

        except Exception as e:
            logger.error(f"Error in transcription with language detection: {e}")
            return {
                "text": "",
                "segments": [],
                "detected_language": None,
                "language_confidence": 0.0,
                "language_name": None,
                "error": str(e),
            }
