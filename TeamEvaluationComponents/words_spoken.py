def words_spoken(conversation, participant_name):
    total_words = 0
    participant_words = 0

    for participant, message in conversation:
        if not message:
            continue
        words = len(message.split())
        total_words += words
        if participant == participant_name:
            participant_words += words

    if total_words == 0:
        percentage = 0
    else:
        percentage = (participant_words / total_words) * 100

    return {'participant_words': participant_words, 'percentage': percentage}