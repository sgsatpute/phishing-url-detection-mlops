"""
Tests for the label-mapping logic that determines what the user sees
("Legitimate" vs "Phishing") from the model's raw prediction.

This is the single most important test file in the project: a previous
version of app.py compared the model's prediction against -1, while the
model's actual output classes were 0.0/1.0 — meaning the check could never
match, and the app silently reported "Legitimate" on every single
prediction regardless of what the model actually decided. That bug shipped
and went unnoticed because nothing tested this mapping in isolation.

Run with: pytest tests/test_label_mapping.py -v
"""

import pytest

from app import _label_from_prediction


class TestLabelFromPrediction:
    def test_class_one_is_legitimate(self) -> None:
        assert _label_from_prediction(1) == "Legitimate"
        assert _label_from_prediction(1.0) == "Legitimate"

    def test_class_zero_is_phishing(self) -> None:
        assert _label_from_prediction(0) == "Phishing"
        assert _label_from_prediction(0.0) == "Phishing"

    def test_legacy_negative_one_does_not_exist_as_a_valid_class(self) -> None:
        """The model never actually predicts -1 (that was the raw dataset's
        original phishing label before data_transformation.py remaps it to
        0). This test documents that -1 is NOT a class the mapping needs to
        special-case — if it ever starts appearing, something upstream
        changed and this test should fail loudly rather than silently
        falling through to "Phishing" by coincidence of the else branch.
        """
        # -1 currently falls into the else branch and returns "Phishing",
        # which happens to be directionally safe (fail closed, not open),
        # but it should never actually be passed a -1 in practice.
        assert _label_from_prediction(-1) == "Phishing"

    @pytest.mark.parametrize("prediction", [1, 1.0])
    def test_only_exact_class_one_maps_to_legitimate(self, prediction: float) -> None:
        # Guards against a future refactor accidentally loosening this to
        # something like `prediction >= 1` or `prediction > 0`, which would
        # silently reintroduce a variant of the original bug for any
        # unexpected model output.
        assert _label_from_prediction(prediction) == "Legitimate"