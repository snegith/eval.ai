def speaking_pace(transcript, duration_sec):
    words = (transcript or "").split()
    duration_sec = float(duration_sec or 0.0)
    minutes = duration_sec / 60.0
    if minutes <= 0:
        return 0.0
    return round(len(words) / minutes, 2)
