from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self):
        self.classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )

    def analyze(self, text):
        result = self.classifier(text[:512])[0]

        label = result["label"]
        score = float(result["score"])

        # EXTRAER RATING SEGURO
        try:
            rating = int(label[0])
        except:
            rating = 3

        # MAPEO CONSISTENTE (ESTO ES CLAVE)
        if rating <= 2:
            sentiment = "negativo"
        elif rating == 3:
            sentiment = "neutral"
        else:
            sentiment = "positivo"

        return {
            "sentiment": sentiment,
            "rating": rating,
            "confidence": score
        }