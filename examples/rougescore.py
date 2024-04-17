import json
import logging
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


def grade_grade(rouge1: float, rouge2: float, rougeL: float) -> tuple[str, str]:
    # Define the thresholds for each metric
    rouge1_thresholds = [0.4, 0.3, 0.2]
    rouge2_thresholds = [0.2, 0.15, 0.1]
    rougeL_thresholds = [0.4, 0.3, 0.2]

    # Initialize the score for each metric
    rouge1_score = 0
    rouge2_score = 0
    rougeL_score = 0

    # Calculate the score for ROUGE-1
    if rouge1 >= rouge1_thresholds[0]:
        rouge1_score = 4
    elif rouge1 >= rouge1_thresholds[1]:
        rouge1_score = 3
    elif rouge1 >= rouge1_thresholds[2]:
        rouge1_score = 2
    else:
        rouge1_score = 1

    # Calculate the score for ROUGE-2
    if rouge2 >= rouge2_thresholds[0]:
        rouge2_score = 4
    elif rouge2 >= rouge2_thresholds[1]:
        rouge2_score = 3
    elif rouge2 >= rouge2_thresholds[2]:
        rouge2_score = 2
    else:
        rouge2_score = 1

    # Calculate the score for ROUGE-L
    if rougeL >= rougeL_thresholds[0]:
        rougeL_score = 4
    elif rougeL >= rougeL_thresholds[1]:
        rougeL_score = 3
    elif rougeL >= rougeL_thresholds[2]:
        rougeL_score = 2
    else:
        rougeL_score = 1

    # Calculate the average score
    average_score = (rouge1_score + rouge2_score + rougeL_score) / 3

    # Determine the grade based on the average score
    if average_score >= 3.5:
        grade = "Excellent"
        explanation = "The ROUGE scores are consistently high across all metrics, indicating a strong similarity between the generated summary and the reference summary."
    elif average_score >= 2.5:
        grade = "Good"
        explanation = "The ROUGE scores are above average, suggesting a reasonable similarity between the generated summary and the reference summary."
    elif average_score >= 1.5:
        grade = "Moderate"
        explanation = "The ROUGE scores are moderate, indicating some similarity between the generated summary and the reference summary, but there is room for improvement."
    else:
        grade = "Poor"
        explanation = "The ROUGE scores are low, suggesting a weak similarity between the generated summary and the reference summary. Consider revising the summarization approach."

    return grade, explanation


def gen_report(
    name: str,
    title: str,
    data: dict,
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

    model_name = model_details["name"]

    # rouge1 (unigrams)
    mean_rouge1 = df_results["rouge1"].mean()
    median_rouge1 = df_results["rouge1"].median()
    std_rouge1 = df_results["rouge1"].std()
    min_rouge1 = df_results["rouge1"].min()
    max_rouge1 = df_results["rouge1"].max()

    # rouge2 (bigrams)

    median_rouge2 = df_results["rouge2"].median()
    std_rouge2 = df_results["rouge2"].std()
    min_rouge2 = df_results["rouge2"].min()
    max_rouge2 = df_results["rouge2"].max()

    # rougeL (length based metric)
    median_rougeL = df_results["rougeL"].median()
    std_rougeL = df_results["rougeL"].std()
    min_rougeL = df_results["rougeL"].min()
    max_rougeL = df_results["rougeL"].max()

    # rougeLsum (sentence level length based metric)
    median_rougeLsum = df_results["rougeLsum"].median()
    std_rougeLsum = df_results["rougeLsum"].std()
    min_rougeLsum = df_results["rougeLsum"].min()
    max_rougeLsum = df_results["rougeLsum"].max()

    worst_performers = df_results.iloc[df_results["rouge1"].nsmallest(1).index]
    best_performers = df_results.iloc[df_results["rouge1"].nlargest(1).index]

    evaluation_metric = metric_results["name"]
    description = metric_results["description"]

    generic_description = """Evaluating Large Language Models (LLMs) involves assessing the quality, relevance, coherence, and
        sometimes the factual accuracy of the text generated by these models. This evaluation is crucial for understanding
        a model's performance across various tasks like translation, summarization, and text generation. Several automated
        metrics have been developed to facilitate this evaluation process, each with its own focus and methodology. Some
        prominent evaluation methods including BERTScore, BLEU, and ROUGE.
    """

    grade, grade_description = grade_grade(median_rouge1, median_rouge2, median_rougeL)

    with rc.ReportCreator(title=title, description=generic_description) as report:
        view = rc.Block(
            rc.Html(description, label="Evaluation Metric"),
            rc.Group(
                rc.Html(
                    f"""<h2>Summary:</h2>The model <b>"{model_name}"</b> created {human_readable_model_created(model_details)} was
                    evaluated (<b>{evaluation_metric}</b>) against the <b>"{dataset['name']}"</b> dataset scoring an overal median F1 score
                    of <b>{median_rouge1:0.3f}</b> (meaning at least half
                    of the evaluations scored at, or better than, {median_rouge1:0.3f}) with a standard deviation of <b>{std_rouge1:0.3f}</b>. The
                    lowest performing evaluation was <b>{min_rouge1:0.3f}</b> and the highest was <b>{max_rouge1:0.3f}</b>.
                    <br /><br />
                    <dd>
                    <li><b>Model:</b> {model_name}</li>
                    <li><b>Metric:</b> {evaluation_metric}</li>
                    <li><b>Dataset:</b> {dataset['name']}</li>
                    </dd>
                    """
                ),
                label=f"""Model: {model_name}""",
            ),
            rc.Group(
                rc.Metric(heading="Grade", value=grade, label=grade_description),
                rc.Metric(
                    heading="Evaluations",
                    value=len(df_results),
                    label=f"Number of {evaluation_metric} evaluations performed",
                ),
                label="Grade",
            ),
            rc.Group(
                rc.Metric(
                    heading="Median",
                    value=f"{median_rouge1:0.3f}",
                    label="The mean overlap of unigrams (each word) between the system and reference summaries",
                ),
                rc.Metric(
                    heading="Standard deviation (σ)",
                    value=f"{std_rouge1:0.3f}",
                    label="Standard deviation is a statistical measurement that indicates how spread out a set of data is in relation to its mean.",
                ),
                rc.Metric(
                    heading="Min/Max",
                    value=f"{min_rouge1:0.3f}/{max_rouge1:0.3f}",
                    label="The minimum/maximum overlap of unigrams (each word) between the system and reference summaries",
                ),
                label="rouge1 - overlap of unigrams (each word)",
            ),
            rc.Group(
                rc.Metric(
                    heading="Median",
                    value=f"{median_rouge2:0.3f}",
                    label="The mean overlap of bigrams (phrases) between the system and reference summaries",
                ),
                rc.Metric(
                    heading="Standard deviation (σ)",
                    value=f"{std_rouge2:0.3f}",
                    label="Standard deviation is a statistical measurement that indicates how spread out a set of data is in relation to its mean.",
                ),
                rc.Metric(
                    heading="Min/Max",
                    value=f"{min_rouge2:0.3f}/{max_rouge2:0.3f}",
                    label="The minimum/maximum overlap of unigrams (each word) between the system and reference summaries",
                ),
                label="rouge2 - overlap of bigrams (phrases)",
            ),
            rc.Group(
                rc.Metric(
                    heading="Median",
                    value=f"{median_rougeL:0.3f}",
                    label="The mean measure of the longest matching sequence of words using longest common subsequences, computed as an average over individual sentences",
                ),
                rc.Metric(
                    heading="Standard deviation (σ)",
                    value=f"{std_rougeL:0.3f}",
                    label="Standard deviation is a statistical measurement that indicates how spread out a set of data is in relation to its mean.",
                ),
                rc.Metric(
                    heading="Min/Max",
                    value=f"{min_rougeL:0.3f}/{max_rougeL:0.3f}",
                    label="The minimum/maximum overlap of unigrams (each word) between the system and reference summaries",
                ),
                label="rougeL - longest matching sequence of words (summary level)",
            ),
            rc.Group(
                rc.Metric(
                    heading="Median",
                    value=f"{median_rougeLsum:0.3f}",
                    label="The mean measure of the longest matching sequence of words using longest common subsequences, computed over the entire summary",
                ),
                rc.Metric(
                    heading="Standard deviation (σ)",
                    value=f"{std_rougeLsum:0.3f}",
                    label="Standard deviation is a statistical measurement that indicates how spread out a set of data is in relation to its mean.",
                ),
                rc.Metric(
                    heading="Min/Max",
                    value=f"{min_rougeLsum:0.3f}/{max_rougeLsum:0.3f}",
                    label="The minimum/maximum overlap of unigrams (each word) between the system and reference summaries",
                ),
                label="rougeLsum- longest matching sequence of word (sentence level)",
            ),
            rc.Group(
                rc.Widget(
                    df_results.boxplot(column="rouge1", by="categories").get_figure(),
                    label="ROUGE1 Score Distribution by category",
                ),
                rc.Widget(
                    df_results.boxplot(column="rouge2", by="categories").get_figure(),
                    label="ROUGE2 Score Distribution by category",
                ),
            ),
            rc.Group(
                rc.Html(
                    f"{best_performers[['responses']].to_html(index=False, escape=True, justify='left')}{best_performers[['references']].to_html(index=False, escape=True, justify='left')}",
                ),
                label="Best Performing Evaluation",
            ),
            rc.Group(
                rc.Html(
                    f"{worst_performers[['responses']].to_html(index=False, escape=True, justify='left')}{worst_performers[['references']].to_html(index=False, escape=True, justify='left')}",
                ),
                label="Worst Performing Evaluation",
            ),
            rc.Heading("Parameters", level=2),
            rc.Collapse(
                rc.Table(
                    model_parms_to_table(model_params),
                ),
                label="Model Parameters",
            ),
            rc.Heading(label="Results", level=2),
            rc.Collapse(
                rc.DataTable(data, wrap_text=True),
                label="Results Table",
            ),
            label=evaluation_metric,
        )
        # save the report, light, dark, or auto mode (follow browser settings)
        report.save(view, name)


if __name__ == "__main__":
    with open("rouge.json") as f:
        data, dataset, model_params, model_details, metric_results = itemgetter(
            "data", "dataset", "model_params", "model_details", "metric_results"
        )(json.load(f))

    gen_report(
        "rougescore.html",
        "Model Evaluation Report",
        data,
        dataset,
        model_params,
        model_details,
        metric_results["rougescore"],
    )
