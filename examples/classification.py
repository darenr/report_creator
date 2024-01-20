import logging
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn import datasets
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

np.set_printoptions(precision=2)

logging.basicConfig(level=logging.INFO)

import report_creator as rc

# pip install scikit-learn scikit-plot

cancer = datasets.load_breast_cancer()

df_cancer = pd.DataFrame(
    np.c_[cancer["data"], cancer["target"]],
    columns=np.append(cancer["feature_names"], ["target"]),
)
X, Y = cancer.data, cancer.target


X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, train_size=0.80, test_size=0.20, stratify=Y, random_state=1
)

log_reg = LogisticRegression(random_state=123)

log_reg.fit(X_train, Y_train)

Y_preds = log_reg.predict(X_test)

# make a dataframe from y_preds and y_test
df_yhat = pd.DataFrame(data={"predictions": Y_preds, "actual": Y_test})


conf_mat = confusion_matrix(Y_test, Y_preds)
print(conf_mat)

import scikitplot as skplt

fig_confusion_matrix = skplt.metrics.plot_confusion_matrix(
    Y_test,
    Y_preds,
    normalize=False,
    title="Confusion Matrix",
    cmap="Purples",
).get_figure()


# auc = roc_auc_score(Y_test, log_reg.predict_proba(X_test)[:,1])
auc = roc_auc_score(Y_test, log_reg.decision_function(X_test))


fig_roc_curve = skplt.metrics.plot_roc_curve(
    Y_test, log_reg.predict_proba(X_test), title="ROC Curve", figsize=(12, 6)
).get_figure()


with rc.ReportCreator("Classification Report") as report:
    view = rc.Block(
        rc.Collapse(
            rc.Python(open(__file__, "r").read()),
            label="Source Code",
        ),
        rc.Group(
            rc.Metric(
                heading="Train Accuracy",
                value=log_reg.score(X_train, Y_train),
            ),
            rc.Metric(
                heading="Test Accuracy",
                value=accuracy_score(Y_test, Y_preds),
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
            label="Classification Metrics",
        ),
        rc.Separator(),
        rc.Select(
            rc.DataTable(df_cancer, label="Cancer Data"),
            rc.DataTable(df_yhat, label="Predictions vs Actual"),
        ),
        rc.Plot(fig_confusion_matrix, label="Confusion Matrix"),
        rc.Plot(fig_roc_curve, label="ROC Curve"),
    )

    # save the report, light, dark, or auto mode (follow browser settings)
    report.save(view, "classification.html", mode="light")
