import re
import spacy
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

class TextPreprocessor:
    def __init__(self, lang='es'):
        self.lang = lang
        self.nlp = spacy.load(f'{lang}_core_news_sm')
        self.stop_words = set(stopwords.words('spanish'))
    
    def clean(self, text):
        # limpieza básica
        text = text.lower()
        text = re.sub(r'http\S+', '', text)  # URLs
        text = re.sub(r'@\w+', '', text)     # menciones
        text = re.sub(r'[^\w\s]', '', text)  # puntuación
        return text.strip()
    
    def lemmatize(self, text):
        doc = self.nlp(text)
        tokens = [token.lemma_ for token in doc 
                 if token.text not in self.stop_words and not token.is_punct]
        return ' '.join(tokens)
    
    def process(self, text):
        cleaned = self.clean(text)
        lemmatized = self.lemmatize(cleaned)
        return lemmatized