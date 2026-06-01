import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from preprocess import preprocess_text

DATASET_PATH = "dataset/ticket_priority_dataset_1200_rows.xlsx"
MODEL_DIR = "model"

TEXT_COLUMN = "Ticket Description"
PRIORITY_COLUMN = "Priority"
CATEGORY_COLUMN = "Category"
DEPARTMENT_COLUMN = "Department"


def load_dataset(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = [TEXT_COLUMN, PRIORITY_COLUMN, CATEGORY_COLUMN, DEPARTMENT_COLUMN]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in dataset: {missing_columns}")

    df = df.dropna(subset=required_columns).copy()
    df[TEXT_COLUMN] = df[TEXT_COLUMN].astype(str).apply(preprocess_text)
    return df


def main() -> None:
    print(f"Loaded dataset: {DATASET_PATH}")

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}. "
            "Place ticket_priority_dataset_1200_rows.xlsx in the dataset/ folder."
        )

    df = pd.read_excel(DATASET_PATH)
    df = load_dataset(df)

    print(f"Training on {len(df)} tickets...")

    X_text = df[TEXT_COLUMN]

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(X_text)

    print("Training priority model...")
    priority_model = LogisticRegression(max_iter=1000)
    priority_model.fit(X, df[PRIORITY_COLUMN])

    print("Training category model...")
    category_model = LogisticRegression(max_iter=1000)
    category_model.fit(X, df[CATEGORY_COLUMN])

    print("Training department model...")
    department_model = LogisticRegression(max_iter=1000)
    department_model.fit(X, df[DEPARTMENT_COLUMN])

    os.makedirs(MODEL_DIR, exist_ok=True)

    vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")
    priority_path = os.path.join(MODEL_DIR, "priority_model.pkl")
    category_path = os.path.join(MODEL_DIR, "category_model.pkl")
    department_path = os.path.join(MODEL_DIR, "department_model.pkl")

    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(priority_model, priority_path)
    joblib.dump(category_model, category_path)
    joblib.dump(department_model, department_path)

    print(f"Saved: {vectorizer_path}")
    print(f"Saved: {priority_path}")
    print(f"Saved: {category_path}")
    print(f"Saved: {department_path}")
    print("All models trained successfully.")


if __name__ == "__main__":
    main()
