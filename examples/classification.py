import logging
import warnings
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn import datasets
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)

warnings.filterwarnings("ignore")

np.set_printoptions(precision=2)

logging.basicConfig(level=logging.INFO)

import report_creator as rc

# pip install scikit-learn scikit-plot

X, Y = datasets.load_breast_cancer(return_X_y=True)


X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, train_size=0.80, test_size=0.20, stratify=Y, random_state=1
)


log_reg = LogisticRegression(random_state=123)

log_reg.fit(X_train, Y_train)

Y_preds = log_reg.predict(X_test)

print(Y_preds[:15])
print(Y_test[:15])


conf_mat = confusion_matrix(Y_test, Y_preds)
print(conf_mat)

import scikitplot as skplt

skplt.metrics.plot_confusion_matrix(
    Y_test,
    Y_preds,
    normalize=False,
    title="Confusion Matrix",
    cmap="Purples",
)


# fpr, tpr, thresholds = roc_curve(Y_test, log_reg.predict_proba(X_test)[:, 1])
fpr, tpr, thresholds = roc_curve(Y_test, log_reg.decision_function(X_test))

# auc = roc_auc_score(Y_test, log_reg.predict_proba(X_test)[:,1])
auc = roc_auc_score(Y_test, log_reg.decision_function(X_test))


print("False Positive Rates : {}".format(fpr))
print("True  Positive Rates : {}".format(tpr))
print("Threshols            : {}".format(thresholds))

skplt.metrics.plot_roc_curve(
    Y_test, log_reg.predict_proba(X_test), title="ROC Curve", figsize=(12, 6)
)

with open(__file__, "r") as f:
    example_python = f.read()


with rc.ReportCreator("Classification Report") as report:
    view = rc.Block(
        rc.Collapse(
            rc.Python(example_python),
            label="Source Code",
        ),
        rc.Group(
            rc.Metric(
                heading="Test Accuracy",
                value=accuracy_score(Y_test, Y_preds),
            ),
            rc.Metric(
                heading="Train Accuracy",
                value=log_reg.score(X_train, Y_train),
            ),
            rc.Metric(
                heading="Precision",
                value=precision_score(Y_test, Y_preds),
            ),
            rc.Metric(
                heading="Recall",
                value=recall_score(Y_test, Y_preds),
            ),
            rc.Metric(
                heading="F1-Score",
                value=f1_score(Y_test, Y_preds),
            ),
            rc.Metric(
                heading="Balanced Accuracy Score",
                value=balanced_accuracy_score(Y_test, Y_preds, adjusted=True),
            ),
            rc.Metric(
                heading="Balanced Accuracy Adjusted",
                value=balanced_accuracy_score(Y_test, Y_preds, adjusted=True),
                label="Number of correct predictions Total number of predictions",
            ),
            label="Metrics",
        ),
    )

    # save the report, light, dark, or auto mode (follow browser settings)
    report.save(view, "classification.html", mode="light")
