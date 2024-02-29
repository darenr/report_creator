import json
import logging
import os
import warnings
from datetime import datetime
from operator import itemgetter

import humanize
import pandas as pd

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)

import report_creator as rc


def model_parms_to_table(model_params: dict) -> pd.DataFrame:
    return pd.DataFrame(model_params.items(), columns=["Parameter", "Value"])


def human_readable_model_created(model_details: dict) -> str:
    return f"""{humanize.naturaltime(datetime.fromisoformat(model_details["Time created"]))}"""


def gen_report(
    name: str,
    title: str,
    dataset: dict,
    model_params: dict,
    model_details: dict,
    metric_results: dict,
):
    assert "data" in metric_results, "No data found in metric_results"
    assert "name" in metric_results, "No name found in metric_results"
    assert "description" in metric_results, "No description found in metric_results"
    assert len(metric_results["data"]) > 0, "No data found in metric_results['data']"

    df_results = pd.DataFrame(metric_results["data"])
    mean_f1 = df_results["f1"].mean()
    median_f1 = df_results["f1"].median()
    f1_std = df_results["f1"].std()
    min_f1 = df_results["f1"].min()
    max_f1 = df_results["f1"].max()

    evaluation_metric = metric_results["name"]
    description = metric_results["description"]
    evaluation_model = os.path.basename(metric_results["data"][0]["hashcode"])

    with rc.ReportCreator(title=title, description=description) as report:
        view = rc.Block(
            rc.Group(
                rc.Html(
                    f"""<h2>Summary:</h2>The model <b>"{model_details['Model name']}"</b> created {human_readable_model_created(model_details)} was
                    evaluated (<b>{evaluation_metric}</b>) against the <b>"{dataset['name']}"</b> dataset scoring an overal median F1 score
                    of <b>{median_f1:0.3f}</b> (meaning at least half 
                    of the evaluations scored at, or better than, {median_f1:0.3f}) with a standard deviation of <b>{f1_std:0.3f}</b>. The
                    lowest performing evaluation was <b>{min_f1:0.3f}</b> and the highest was <b>{max_f1:0.3f}</b>. The evaluation model 
                    used to calculate {evaluation_metric} was <b>{evaluation_model}</b>"""
                ),
                label=f"""Model: {model_details['Model name']}""",
            ),
            rc.Group(
                rc.Metric(
                    heading=f"Mean {evaluation_metric} F1",
                    value=mean_f1,
                    label="F1 score is a measure of the harmonic mean of precision and recall.",
                ),
                rc.Metric(
                    heading="Standard deviation (σ)",
                    value=f1_std,
                    label="Standard deviation is a statistical measurement that indicates how spread out a set of data is in relation to its mean.",
                ),
                rc.Metric(
                    heading="Evaluations",
                    value=len(df_results),
                    label=f"Number of {evaluation_metric} evaluations performed",
                ),
                label=f"{evaluation_metric} Metrics",
            ),
            rc.Plot(
                df_results.boxplot(column="f1", by="categories").get_figure(),
                label="Score Distribution",
            ),
            rc.Collapse(
                rc.Table(
                    model_parms_to_table(model_params),
                ),
                label="Model Parameters",
            ),
        )
        # save the report, light, dark, or auto mode (follow browser settings)
        report.save(view, name, mode="light")


if __name__ == "__main__":
    with open("report.json") as f:
        data, dataset, model_params, model_details, metric_results = itemgetter(
            "data", "dataset", "model_params", "model_details", "metric_results"
        )(json.load(f))

    gen_report(
        "bertscore.html",
        "Model Evaluation Report",
        dataset,
        model_params,
        model_details,
        metric_results["bertscore"],
    )
