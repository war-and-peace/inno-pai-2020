import wave
import pyaudio
import io
from google.cloud import speech
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
import vlc

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050
CREDENTIALS_PATH = 'credentials.json'


def record_to_file(filename, player, seconds=5):
    global FORMAT, CHANNELS, RATE
    RECORD_SECONDS = seconds

    stream = player.open(
                input=True,
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                frames_per_buffer=CHUNK)

    print("Start recording... ", end="")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)  # or you can here detect average magnitude and stop an silence
        frames.append(data)
    print("recorded", seconds, "second(s)")
    stream.stop_stream()
    stream.close()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(player.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


def speech_to_text(filename, language):
    client = speech.SpeechClient.from_service_account_json(CREDENTIALS_PATH)
    with io.open(filename, "rb") as audio_file:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="uz",
    )

    response = client.recognize(config=config, audio=audio)
    texts = []
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))
        texts.append(result.alternatives[0].transcript)
    return texts


def translate_text(text: str, source: str, target: str):
    translate_client = translate.Client.from_service_account_json(CREDENTIALS_PATH)
    result = translate_client.translate(texts[0], target_language=target, source_language=source)
    print(f'Translation from {source} to {target}: {result["translatedText"]}')
    return result["translatedText"]


def text_to_speech(text: str, language: str, output_file='output.mp3'):

    client = texttospeech.TextToSpeechClient.from_service_account_json(CREDENTIALS_PATH)
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=language)

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        effects_profile_id=['headphone-class-device'],
    )

    response = client.synthesize_speech(
        input=input_text, voice=voice,
        audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "%s"' % output_file)

    return output_file


def play_the_recording(file_path):
    p = vlc.MediaPlayer(output_file)
    p.play()


if __name__ == '__main__':
    filename = 'sample.wav'
    while True:
        print()
        command = input('Enter q to stop. Otherwise, press any key: ')
        if command == 'q':
            break

        player = pyaudio.PyAudio()
        record_to_file(filename, player)
        player.terminate()

        # Speech-to-text: Uzbek language
        texts = speech_to_text(filename, 'uz')

        # Translations Uzbek -> English
        textEn = translate_text(texts[0], 'uz', 'en')

        # Translation English -> Uzbek
        textUz = translate_text(textEn, 'en', 'uz')

        # Text-to-Speech: Uzbek language is not supported. Using English instead.
        output_file = text_to_speech(textUz, 'en')

        # Play the generated speech:
        play_the_recording(output_file)
