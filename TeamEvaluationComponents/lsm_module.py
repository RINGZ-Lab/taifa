import logging
import spacy
logger = logging.getLogger(__name__)
nlp = spacy.load('en_core_web_sm')

def LSM(speaker_t, team_t):
    categories = {
        'articles': lambda token: token.pos_ == 'DET' and token.lower_ in ['a', 'an', 'the'],
        'personal_pronouns': lambda token: token.pos_ == 'PRON' and token.lower_ in ['i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them'],
        'impersonal_pronouns': lambda token: token.pos_ == 'PRON' and token.lower_ in ['it', 'its', 'that', 'which', 'this', 'these', 'those'],
        'prepositions': lambda token: token.pos_ == 'ADP',
        'auxiliary_verbs': lambda token: token.pos_ == 'AUX',
        'adverbs': lambda token: token.pos_ == 'ADV',
        'conjunctions': lambda token: token.pos_ in ['CCONJ', 'SCONJ'],
        'negations': lambda token: token.lower_ in ['no', 'not', "n't", 'never', 'none', 'nobody', 'nothing', 'neither', 'nowhere'],
        'quantifiers': lambda token: token.lower_ in ['all', 'any', 'few', 'many', 'much', 'some', 'several', 'most', 'every', 'each']
    }
    speaker_doc = nlp(speaker_t)
    team_doc = nlp(team_t)
    for doc_name, doc in [("Speaker Doc", speaker_doc), ("Team Doc", team_doc)]:
        logger.debug(f"\nTokens in {doc_name}:")
        for category, condition in categories.items():
            logger.debug(f"  Category: {category}")
            for token in doc:
                if condition(token):
                    logger.debug(f"Token: {token.text} (POS: {token.pos_})")

    total_speaker_words = len(speaker_doc)
    total_team_words = len(team_doc)

    lsm_scores = []
    for category_name, category_func in categories.items():
        speaker_count = sum(1 for token in speaker_doc if category_func(token))
        team_count = sum(1 for token in team_doc if category_func(token))
        P_speaker = speaker_count / total_speaker_words if total_speaker_words > 0 else 0
        P_team = team_count / total_team_words if total_team_words > 0 else 0
        numerator = abs(P_speaker - P_team)
        denominator = P_speaker + P_team + 0.0001
        lsm_category = 1 - (numerator / denominator)
        lsm_scores.append(lsm_category)
    overall_lsm = sum(lsm_scores) / len(lsm_scores) if lsm_scores else 0

    return overall_lsm
