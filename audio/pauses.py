def detect_pauses(segments, threshold=2.0):
    pauses = []
    if not segments:
        return pauses

    for i in range(1, len(segments)):
        previous_end = float(segments[i - 1].get("end", 0.0))
        current_start = float(segments[i].get("start", previous_end))
        gap = current_start - previous_end
        if gap > threshold:
            pauses.append(gap)
    return pauses
