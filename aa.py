import json

import evaluate

with open("report.json") as f:
    report = json.load(f)


metric_results = report["metric_results"]

# get the data from bertscore then create a new rougescore section in metric results

predictions = [
    x["references"] for x in metric_results["bertscore"]["data"]
]  # list of tuples]

# add rouge

model = evaluate.load("rouge")


report["metric_results"]["rougescore"] = {
    "key": "rougescore",
    "name": "Rouge Score",
    "description": """ROUGE scores compare a candidate document to a collection of reference documents to evaluate the similarity between them. 
    The metrics range from 0 to 1, with higher scores indicating greater similarity. ROUGE is more suitable for models that don't include paraphrasing and do not generate new text units that don't appear in the references. 
    The metrics are ROUGE-1 (unigram overlap), ROUGE-2 (bigram overlap), and ROUGE-L (longest common subsequence). The ROUGE scoreis calculated between the model's predictions and the human-produced references. A perfect model 
    would have a ROUGE score of 1.0, meaning the outputs from the model and the human-produced references are identical.    
    """,
    "data": [
        dict(
            {
                "prompts": x["prompts"],
                "references": x["references"],
                "responses": x["responses"],
                "categories": x["categories"],
            },
            **model.compute(predictions=[x["responses"]], references=[x["references"]]),
        )
        for x in metric_results["bertscore"]["data"]
    ],
}

with open("report_2.json", "w") as f:
    json.dump(report, f, indent=2)
