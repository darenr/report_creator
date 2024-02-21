# pip install bert-score evaluate pandas

import evaluate
import logging
import warnings
import pandas as pd

from statistics import mean

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)

import report_creator as rc

candicates = [
    "28-year-old chef found dead in San Francisco mall",
    "A 28-year-old chef who recently moved to San Francisco was found dead in the staircase of a local shopping center.",
    'The victim\'s brother said he cannot imagine anyone who would want to harm him,"Finally, it went uphill again at him."',
    "The corpse, found Wednesday morning in the Westfield Mall, was identified as the 28-year-old Frank Galicia from San Francisco, the Justice Department said in San Francisco.",
    "The San Francisco Police Department said the death was classified as murder and the investigation is on the running.",
    "The victim's brother, Louis Galicia, told the ABS broadcaster KGO in San Francisco that Frank, who formerly worked as a cook in Boston, had his dream job as a cook at the Sons & Daughters restaurant in San Francisco six months ago.",
    'A spokesman for the Sons & Daughters said they were "shocked and destroyed on the ground" over his death.',
    '"We are a small team that works like a close family and we are going to miss him painfully," said the spokesman.',
    "Our thoughts and condolences are in this difficult time at Franks's family and friends.",
    'Louis Galicia admitted that Frank initially lived in hostels, but that "things for him finally went uphill."',
]

references = [
    "28-Year-Old Chef Found Dead at San Francisco Mall",
    "A 28-year-old chef who had recently moved to San Francisco was found dead in the stairwell of a local mall this week.",
    "But the victim's brother says he can't think of anyone who would want to hurt him, saying, \"Things were finally going well for him.\"",
    "The body found at the Westfield Mall Wednesday morning was identified as 28-year-old San Francisco resident Frank Galicia, the San Francisco Medical Examiner's Office said.",
    "The San Francisco Police Department said the death was ruled a homicide and an investigation is ongoing.",
    "The victim's brother, Louis Galicia, told ABC station KGO in San Francisco that Frank, previously a line cook in Boston, had landed his dream job as line chef at San Francisco's Sons & Daughters restaurant six months ago.",
    'A spokesperson for Sons & Daughters said they were "shocked and devastated" by his death.',
    '"We are a small team that operates like a close knit family and he will be dearly missed," the spokesperson said.',
    "Our thoughts and condolences are with Frank's family and friends at this difficult time.",
    'Louis Galicia said Frank initially stayed in hostels, but recently, "Things were finally going well for him."',
]

df = pd.DataFrame(
    list(zip(candicates, references)), columns=["candidates", "references"]
)

df_results = pd.DataFrame(
    evaluate.load("bertscore").compute(
        predictions=df["candidates"],
        references=df["references"],
        lang="en",
        model_type="distilbert-base-uncased",
    )
)

mean_f1 = df_results["f1"].mean()
mean_precision = df_results["precision"].mean()
mean_recall = df_results["recall"].mean()

min_f1 = df_results["f1"].min()
max_f1 = df_results["f1"].max()

worst_performers = df.iloc[df_results["f1"].nsmallest(5).index]
best_performers = df.iloc[df_results["f1"].nlargest(5).index]

print(worst_performers)

with rc.ReportCreator("Bert Score Report") as report:
    view = rc.Block(
        rc.Markdown(
            """
            # BERTScore 
            
            Bert Score is a metric for evaluating the quality of text generation models, such as machine translation or summarization. It utilizes pre-trained BERT contextual embeddings for both the generated and reference texts, and then calculates the cosine similarity between these embeddings.
            
            BERTScore significantly outperforms other text evaluation metrics, primarily because it utilizes contextual embeddings. These embeddings address the limitations of traditional word- or character-based metrics.
            """
        ),
        rc.Collapse(rc.DataTable(df), label="Source Data"),
        rc.Group(
            rc.Metric(heading="Mean F1", value=mean_f1),
            rc.Metric(heading="Min F1", value=min_f1),
            rc.Metric(heading="Max F1", value=max_f1),
            label="Bert Score Metrics",
        ),
        rc.Group(
            rc.Metric(
                heading="LLM response", value=best_performers.iloc[0]["candidates"]
            ),
            rc.Metric(
                heading="LLM Reference",
                value=best_performers.iloc[0]["references"],
            ),
            label=f"Best Performer, score: {max_f1:.3f}",
        ),
        rc.Group(
            rc.Metric(
                heading="LLM response",
                value=worst_performers.iloc[0]["candidates"],
            ),
            rc.Metric(
                heading="LLM Reference",
                value=worst_performers.iloc[0]["references"],
            ),
            label=f"Worst Performers, score: {min_f1:.3f}",
        ),
    )

    # save the report, light, dark, or auto mode (follow browser settings)
    report.save(view, "bertscore.html", mode="light")
