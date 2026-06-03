from .preprocess import TextPreprocessor
from .sentiment import SentimentAnalyzer
from .topics import TopicExtractor
import pandas as pd

class ReviewPipeline:
    def __init__(self, lang='es', n_topics=10):
        self.preprocessor = TextPreprocessor(lang)
        self.sentiment = SentimentAnalyzer()
        self.topics = TopicExtractor(n_topics=n_topics)
    
    def process_single(self, text):
        # Limpiar
        clean_text = self.preprocessor.process(text)
        
        # Sentimiento
        sentiment_result = self.sentiment.analyze(clean_text)
        
        # Tópico (requiere modelo entrenado)
        topic_result = None
        if self.topics.fitted:
            topic_id, prob = self.topics.predict(clean_text)
            topic_result = {
                'topic_id': topic_id,
                'confidence': prob,
                'keywords': self.topics.get_topic_words(topic_id)
            }
        
        return {
            'original_text': text,
            'clean_text': clean_text,
            **sentiment_result,
            'topic': topic_result
        }
    
    def batch_process(self, texts):
        results = []
        for text in texts:
            results.append(self.process_single(text))
        return pd.DataFrame(results)
    
    def train_topics(self, texts):
        clean_texts = [self.preprocessor.process(t) for t in texts]
        return self.topics.fit(clean_texts)