import sys

from network_security.exception.exception import NetworkSecurityException


class NetworkModel:
    def __init__(self, preprocessor: object, model: object) -> None:
        try:
            self.preprocessor = preprocessor
            self.model = model
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def predict(self, x: object) -> object:
        try:
            x_transform = self.preprocessor.transform(x)
            y_hat = self.model.predict(x_transform)
            return y_hat
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def predict_proba(self, x: object) -> object:
        """Return class probabilities, mirroring predict()'s transform step.

        Not every underlying estimator supports predict_proba (e.g. an SVC
        trained without probability=True), so callers should check
        hasattr(self.model, "predict_proba") first or catch the resulting
        AttributeError/NetworkSecurityException if they want to degrade
        gracefully instead of erroring out.
        """
        try:
            if not hasattr(self.model, "predict_proba"):
                raise AttributeError(
                    f"Underlying model {type(self.model).__name__} does not "
                    "support predict_proba (was it trained with "
                    "probability=True, if applicable?).",
                )
            x_transform = self.preprocessor.transform(x)
            return self.model.predict_proba(x_transform)
        except Exception as e:
            raise NetworkSecurityException(e, sys)