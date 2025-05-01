def get_max_speaker(speaker_contributions):
    max_speaker = max(speaker_contributions, key=lambda x: speaker_contributions[x]["word_count"])
    max_words = speaker_contributions[max_speaker]["word_count"]
    return max_speaker, max_words