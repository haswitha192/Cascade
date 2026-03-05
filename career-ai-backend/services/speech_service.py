import azure.cognitiveservices.speech as speechsdk
import os


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio from a file using the Azure Speech SDK.
    The audio_path must point to a true PCM WAV file (which we create via ffmpeg/pydub).
    """

    speech_key    = os.environ["SPEECH_KEY"]
    speech_region = os.environ["SPEECH_REGION"]

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=speech_region
    )
    speech_config.speech_recognition_language = "en-US"

    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return ""
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        raise RuntimeError(f"Speech Recognition canceled: {cancellation_details.reason} - {cancellation_details.error_details}")

    return ""