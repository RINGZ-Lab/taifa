from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def get_team_sentiment(conversation_text):
    team_sentiment = analyzer.polarity_scores(conversation_text)
    return team_sentiment