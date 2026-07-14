from bertopic import BERTopic
import pandas as pd

class TopicExtractor:
    def __init__(self, n_topics=10):
        # BERTopic > LDA para textos cortos como reseñas
        # Forzamos la creación de tópicos con grupos más pequeños (min_topic_size=3)
        # y le indicamos explícitamente que los textos están en español/multilingüe.
        self.model = BERTopic(
            verbose=True, 
            nr_topics=n_topics,
            min_topic_size=3,
            language="multilingual"
        )
        self.fitted = False
    
    def fit(self, texts):
        self.topics, self.probs = self.model.fit_transform(texts)
        self.fitted = True
        return self.model.get_topic_info()
    
    def predict(self, text):
        if not self.fitted:
            raise ValueError("Modelo no entrenado")
        topic, prob = self.model.transform([text])
        return topic[0], prob[0]
    
    def get_topic_words(self, topic_id=None):
        if topic_id is None:
            return self.model.get_topic_info()
        return self.model.get_topic(topic_id)