"""
Tests for NetworkModel (network_security.utils.ml_utils.model.estimator)
using lightweight fake preprocessor/model stubs, so these run without a
real trained pickle on disk.

Run with: pytest tests/test_estimator.py -v
"""

import pytest

from network_security.exception.exception import NetworkSecurityException
from network_security.utils.ml_utils.model.estimator import NetworkModel


class FakePreprocessor:
    def transform(self, x):
        return x  # identity transform for test purposes


class FakeModelWithProba:
    def predict(self, x):
        return [1.0]

    def predict_proba(self, x):
        return [[0.27, 0.73]]


class FakeModelWithoutProba:
    def predict(self, x):
        return [0.0]
    # deliberately no predict_proba, to mirror an estimator trained
    # without probability support (e.g. an SVC without probability=True)


class TestNetworkModelPredict:
    def test_predict_transforms_then_predicts(self) -> None:
        model = NetworkModel(preprocessor=FakePreprocessor(), model=FakeModelWithProba())
        result = model.predict("some_features")
        assert result == [1.0]


class TestNetworkModelPredictProba:
    def test_predict_proba_returns_probabilities_when_supported(self) -> None:
        model = NetworkModel(preprocessor=FakePreprocessor(), model=FakeModelWithProba())
        proba = model.predict_proba("some_features")
        assert proba == [[0.27, 0.73]]

    def test_predict_proba_raises_clean_error_when_unsupported(self) -> None:
        # This is the case that matters for app.py's confidence-score
        # feature: it must fail in a way app.py's except block can catch
        # and degrade gracefully from, not crash the whole request.
        model = NetworkModel(preprocessor=FakePreprocessor(), model=FakeModelWithoutProba())
        with pytest.raises(NetworkSecurityException):
            model.predict_proba("some_features")