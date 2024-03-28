import json
import logging
import warnings
import json

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)

import report_creator as rc


def gen_report(name: str, title: str, description: str, data: dict):
    with rc.ReportCreator(title=title, description=description) as report:
        view = rc.Block()
        report.save(view, name, mode="light")


if __name__ == "__main__":
    with open("20240327_aqua_telemetry_int.json") as f:
        gen_report(
            "telemetry.html",
            "AQUA Telemetry Integration March 2024",
            "This report contains the telemetry data for the AQUA project in Integration MArch 2024",
            json.load(f),
        )
