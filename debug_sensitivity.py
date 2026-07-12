"""
One-off diagnostic: take the extracted feature vector for a URL, then flip
each feature to its most "suspicious" value (-1) one at a time, and show
how the model's predicted probability changes. This tells us which
features the trained model actually responds to vs. ones it effectively
ignores — useful for checking whether neutral-defaulted (0) features are
silently behaving as "legitimate-leaning" rather than truly neutral.

Usage:
    python debug_sensitivity.py http://paypal-secure-verify.tk
"""

import sys

from network_security.utils.main_utils.utils import load_object
from network_security.utils.ml_utils.feature_extraction import (
    FEATURE_COLUMNS,
    extract_features,
)
from network_security.utils.ml_utils.model.estimator import NetworkModel


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python debug_sensitivity.py <url>")
        return

    url = sys.argv[1]

    preprocessor = load_object("final_model/preprocessor.pkl")
    model = load_object("final_model/model.pkl")
    network_model = NetworkModel(preprocessor=preprocessor, model=model)

    base_df = extract_features(url)
    base_proba = network_model.predict_proba(base_df)[0]
    # class order: model.classes_ tells us which column is which label
    classes = list(model.classes_)
    print(f"Model classes order: {classes}")
    print(f"Baseline probabilities: {dict(zip(classes, base_proba))}\n")

    print(f"{'Feature':<32} {'Current':>8} {'-> -1 gives P(legit)':>22} {'-> 1 gives P(legit)':>22}")
    print("-" * 90)

    legit_label = 1  # Result: 1 = legitimate, -1 = phishing, per app.py's convention
    legit_idx = classes.index(legit_label)

    for col in FEATURE_COLUMNS:
        current_val = base_df[col].iloc[0]
        row = base_df.copy()

        row[col] = -1
        p_neg = network_model.predict_proba(row)[0][legit_idx]

        row[col] = 1
        p_pos = network_model.predict_proba(row)[0][legit_idx]

        print(f"{col:<32} {current_val:>8} {p_neg:>22.3f} {p_pos:>22.3f}")


if __name__ == "__main__":
    main()