# backend/train_model.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Load dataset
df = pd.read_csv("data/messages.csv")

# Features and labels
X = df["message"]
y = df["label"]

# Vetorização
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

# Dividir em treino/teste
X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

# Classificador com balanceamento
model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
model.fit(X_train, y_train)

# Avaliação
y_pred = model.predict(X_test)
print("📊 Relatório de classificação:")
print(classification_report(y_test, y_pred))

# Salvar modelo e vetorizador
joblib.dump(model, "model/scam_detector.joblib")
joblib.dump(vectorizer, "model/vectorizer.joblib")

print("✅ Modelo treinado e salvo com sucesso.")
