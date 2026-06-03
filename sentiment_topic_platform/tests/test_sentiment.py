import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sentiment import SentimentAnalyzer

def test_sentiment_positivo():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("Excelente producto, muy recomendado")
    assert result['sentiment'] == 'positivo'
    print("✅ Test positivo pasado")

def test_sentiment_negativo():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("malísimo, se rompió al día")
    assert result['sentiment'] == 'negativo'
    print("✅ Test negativo pasado")

def test_confidence_range():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("producto normal")
    assert 0 <= result['confidence'] <= 1
    print("✅ Test rango de confianza pasado")

if __name__ == "__main__":
    test_sentiment_positivo()
    test_sentiment_negativo()
    test_confidence_range()
    print("\n🎉 Todas las pruebas pasaron!")