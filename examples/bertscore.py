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
    return (
        f"""{humanize.naturaltime(datetime.fromisoformat(model_details["created"]))}"""
    )


def get_grade(mean_f1: float) -> tuple[str, str]:
    return (
        ("Excellent", "High precision and recall")
        if mean_f1 > 0.9
        else (
            "Very good",
            "The model has a strong balance between precision and recall",
        )
        if mean_f1 > 0.8
        else (
            "Good",
            "The model is suitable for many practical applications, especially when dealing with complex or challenging tasks",
        )
        if mean_f1 > 0.7
        else (
            "Acceptable",
            "The model is acceptable in some contexts, especially in difficult problems where achieving high precision and recall is challenging",
        )
        if mean_f1 > 0.6
        else (
            "Poor",
            "There is significant room for improvement, either in the model's ability to generalize from its training data or in the data itself (e.g., it might be imbalanced or noisy)",
        )
    )


def gen_markdown_report(
    dataset: dict,
    model_params: dict,
    model_details: dict,
    metric_results: dict,
):
    rows = []
    rows.append("|Metric|Score|Grade|")
    rows.append("|:---|---:|---:|")
    for _, metric in metric_results.items():
        metric_name = metric["name"]
        median_f1 = metric["summary_data"]["overall"]["f1"]["0.5"]
        grade, grade_description = get_grade(median_f1)
        std = metric["summary_data"]["overall"]["f1"]["std"]
        rows.append(
            f"|{metric_name}|Median F1: **{median_f1:0.3f}** (SDV: {std:0.3f})|**{grade}**, {grade_description}|"
        )

    print("\n".join(rows))


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
    model_name = model_details["name"]

    generic_description = """Evaluating Large Language Models (LLMs) involves assessing the quality, relevance, coherence, and
        sometimes the factual accuracy of the text generated by these models. This evaluation is crucial for understanding
        a model's performance across various tasks like translation, summarization, and text generation. Several automated
        metrics have been developed to facilitate this evaluation process, each with its own focus and methodology. Some
        prominent evaluation methods including BERTScore, BLEU, and METEOR.
    """

    grade, grade_description = get_grade(mean_f1)

    with rc.ReportCreator(title=title, description=generic_description) as report:
        view = rc.Block(
            rc.Select(
                blocks=[
                    rc.Block(
                        rc.Html(description, label="Evaluation Metric"),
                        rc.Group(
                            rc.Html(
                                f"""<h2>Summary:</h2>The model <b>"{model_name}"</b> created {human_readable_model_created(model_details)} was
                    evaluated (<b>{evaluation_metric}</b>) against the <b>"{dataset['name']}"</b> dataset scoring an overal median F1 score
                    of <b>{median_f1:0.3f}</b> (meaning at least half
                    of the evaluations scored at, or better than, {median_f1:0.3f}) with a standard deviation of <b>{f1_std:0.3f}</b>. The
                    lowest performing evaluation was <b>{min_f1:0.3f}</b> and the highest was <b>{max_f1:0.3f}</b>. The evaluation model
                    used to calculate {evaluation_metric} was <b>{evaluation_model}</b>
                    <br><br>
                    <dd>
                    <li><b>Model:</b> {model_name}</hli2>
                    <li><b>Metric:</b> {evaluation_metric}</li>
                    <li><b>Dataset:</b> {dataset['name']}</li>
                    </dd>
                    """
                            ),
                            label=f"""Model: {model_name}""",
                        ),
                        rc.Group(
                            rc.Metric(
                                heading="Grade", value=grade, label=grade_description
                            ),
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
                            label="Metrics",
                        ),
                        rc.Group(
                            rc.Plot(
                                df_results.boxplot(
                                    column="f1", by="categories"
                                ).get_figure(),
                                label="Score Distribution",
                            )
                        ),
                        rc.Collapse(
                            rc.Table(
                                model_parms_to_table(model_params),
                            ),
                            label="Model Parameters",
                        ),
                        label=evaluation_metric,
                    ),
                ],
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

    gen_markdown_report(
        dataset,
        model_params,
        model_details,
        metric_results,
    )
