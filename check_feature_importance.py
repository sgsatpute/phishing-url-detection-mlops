"""
One-off diagnostic: print feature importances from the currently trained
model, so we can confirm whether the features hardcoded to a neutral 0 in
extract_features() (URL_of_Anchor, Links_in_tags, web_traffic, Page_Rank,
Links_pointing_to_page) are actually high-importance ones the model relies
on. If they are, live single-URL predictions are losing real signal.

Run from the project root:
    python check_feature_importance.py
"""

from network_security.utils.ml_utils.feature_extraction import FEATURE_COLUMNS
from network_security.utils.main_utils.utils import load_object

NEUTRAL_DEFAULTED_FEATURES = {
    "URL_of_Anchor",
    "Links_in_tags",
    "web_traffic",
    "Page_Rank",
    "Links_pointing_to_page",
}


def main() -> None:
    network_model = load_object("final_model/model.pkl")

    if not hasattr(network_model, "feature_importances_"):
        print(
            f"Model type {type(network_model).__name__} doesn't expose "
            "feature_importances_ (only tree-based models like RandomForest, "
            "GradientBoosting, DecisionTree, AdaBoost do). If you trained "
            "LogisticRegression, check .coef_ instead.",
        )
        return

    importances = network_model.feature_importances_
    ranked = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)

    print(f"{'Feature':<32} {'Importance':>10}   Neutral-defaulted in live inference?")
    print("-" * 80)
    for name, importance in ranked:
        flag = "  <-- YES, always 0 for live URLs" if name in NEUTRAL_DEFAULTED_FEATURES else ""
        print(f"{name:<32} {importance:>10.4f}{flag}")

    neutral_total = sum(imp for name, imp in ranked if name in NEUTRAL_DEFAULTED_FEATURES)
    print("-" * 80)
    print(f"Total importance concentrated in neutral-defaulted features: {neutral_total:.4f} "
          f"({neutral_total * 100:.1f}% of total model importance)")


if __name__ == "__main__":
    main()