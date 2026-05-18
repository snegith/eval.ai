import whisper

_model = None
_model_name = None

def transcribe(audio_path, model_name="base"):
    global _model, _model_name
    if _model is None or _model_name != model_name:
        _model = whisper.load_model(model_name)
        _model_name = model_name
    result = _model.transcribe(audio_path)
    return result["text"], result["segments"]
