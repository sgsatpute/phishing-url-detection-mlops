import sys

from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV

from network_security.exception.exception import NetworkSecurityException


def evaluate_models(X_train: object, y_train: object, X_test: object, y_test: object, models: dict, param: dict) -> dict:
    try:
        report = {}

        for i in range(len(list(models))):
            model = list(models.values())[i]
            para = param[list(models.keys())[i]]

            # scoring="f1" so GridSearchCV's own internal model selection
            # (choosing best_params_ within each model's grid) optimizes the
            # same metric we report below — previously this defaulted to
            # each estimator's default scorer (accuracy for classifiers),
            # which can disagree with the f1-based ranking used afterward.
            gs = GridSearchCV(model, para, cv=3, n_jobs=-1, scoring="f1")
            gs.fit(X_train, y_train)

            model.set_params(**gs.best_params_)
            model.fit(X_train, y_train)

            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)

            # This is a binary classification task (phishing vs legitimate),
            # so we score with f1_score, not r2_score (r2_score is a
            # regression metric — it's not a meaningful measure of
            # classification quality and can even be negative on discrete
            # 0/1 or -1/1 predictions).
            train_model_score = f1_score(y_train, y_train_pred)
            test_model_score = f1_score(y_test, y_test_pred)

            report[list(models.keys())[i]] = test_model_score

        return report

    except Exception as e:
        raise NetworkSecurityException(e, sys)