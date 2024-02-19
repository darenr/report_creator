import logging
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import scikitplot as skplt
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

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

steps = [
    ("standard_scaler", StandardScaler()),
    (
        "classifier",
        RandomForestClassifier(
            n_estimators=100, max_samples=0.3, oob_score=True, random_state=42
        ),
    ),
]
pipeline = Pipeline(steps)

pipeline.fit(X_train, Y_train)

Y_preds = pipeline.predict(X_test)

# make a dataframe from y_preds and y_test
df_yhat = pd.DataFrame(data={"predictions": Y_preds, "actual": Y_test})

fig_confusion_matrix = skplt.metrics.plot_confusion_matrix(
    Y_test,
    Y_preds,
    normalize=False,
    title="Confusion Matrix",
    cmap="Purples",
)


fig_roc_curve = skplt.metrics.plot_roc_curve(
    Y_test, pipeline.predict_proba(X_test), title="ROC Curve", figsize=(12, 6)
)

fi = px.bar(
    x=(cancer.feature_names), y=(pipeline["classifier"].feature_importances_)
).update_xaxes(categoryorder="total descending")


with rc.ReportCreator("RandomForest Classifier Report") as report:
    view = rc.Block(
        rc.Collapse(
            rc.Python(open(__file__, "r").read()),
            label="Source Code",
        ),
        rc.Group(
            rc.Metric(
                heading="Train Accuracy",
                value=pipeline.score(X_train, Y_train),
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
            blocks=[
                rc.DataTable(df_cancer, label="Cancer Data"),
                rc.DataTable(df_yhat, label="Predictions vs Actual"),
            ]
        ),
        rc.Plot(fig_confusion_matrix, label="Confusion Matrix"),
        rc.Plot(fig_roc_curve, label="ROC Curve"),
        rc.Separator(),
        rc.Widget(pipeline, label="Pipeline Model"),
        rc.Widget(fi, label="feature_importances"),
    )

    # save the report, light, dark, or auto mode (follow browser settings)
    report.save(view, "classification.html", mode="light")
