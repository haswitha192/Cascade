def calculate_wpm(transcript, duration_seconds):

    words = transcript.split()

    if duration_seconds == 0:
        return 0

    wpm = (len(words) / duration_seconds) * 60

    return round(wpm, 2)