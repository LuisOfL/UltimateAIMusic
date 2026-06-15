import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

# 1. Crear la carpeta models si no existe
os.makedirs("models", exist_ok=True)

# 2. Textos simulados para que los modelos aprendan la estructura básica
textos_prueba = [
    "amor corazon cantar feliz fiesta bailar",
    "tristeza soledad llorar dolor melancolia",
    "calle rima barrio beat rap improvisacion",
    "guitarra distorsion bateria rock metal grito"
]
generos_prueba = ["Pop", "Balada", "Hip-Hop", "Rock"]
temas_prueba = ["Romance", "Tristeza", "Social", "Energético"]

# 3. Entrenar y guardar el Vectorizador (TF-IDF)
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(textos_prueba)
joblib.dump(vectorizer, "models/tfidf_vectorizer.joblib")

# 4. Entrenar y guardar el Clasificador de Género
genre_clf = LogisticRegression()
genre_clf.fit(X, generos_prueba)
joblib.dump(genre_clf, "models/logistic_regression_genre.joblib")

# 5. Entrenar y guardar el Clasificador de Temas
topic_clf = LinearSVC()
topic_clf.fit(X, temas_prueba)
joblib.dump(topic_clf, "models/svm_topic_classifier.joblib")

print("[ÉXITO] Archivos .joblib creados falsificados en 'models/'. ¡Ya puedes correr tu ETL!")