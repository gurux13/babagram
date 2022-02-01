from google.cloud import speech


def recognize(data: bytes) -> str:
    # Instantiates a client
    client = speech.SpeechClient()

    # The name of the audio file to transcribe

    audio = speech.RecognitionAudio(content=data)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=48000,
        language_code="ru-RU",
        enable_automatic_punctuation=True,
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        return result.alternatives[0].transcript

    return None

