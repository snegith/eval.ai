import re


FILLERS = ["um", "uh", "like", "you know", "so", "actually"]


def count_fillers(transcript):
    text = (transcript or "").lower()
    counts = {}
    for filler in FILLERS:
        if " " in filler:
            pattern = re.escape(filler)
        else:
            pattern = rf"\b{re.escape(filler)}\b"
        counts[filler] = len(re.findall(pattern, text))
    return counts
