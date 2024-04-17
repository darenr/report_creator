import collections
import logging
import urllib
import warnings

import duckdb

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)

import report_creator as rc


def unquote(u: str) -> str:
    return urllib.parse.unquote_plus(u.replace("value=", ""))


duckdb.create_function("unquote", unquote)


def gen_report(name: str, title: str, description: str):
    # take all the telemetry categories and count each portion of the category

    l2r = collections.defaultdict(lambda: 0)
    for _, row in duckdb.query("select category, action from t1").df().iterrows():
        parts = row.category.split("/") + [row.action]
        for i in range(len(parts)):
            prefix = "/".join(parts[: i + 1])
            l2r[prefix] += 1

    with rc.ReportCreator(title=title, description=description) as report:
        view = rc.Block(
            rc.Group(
                rc.Bar(
                    duckdb.query(
                        """
                            select
                                action as model,
                                count(*) as val,
                                region
                            from t1
                            where category = 'aqua/evaluation/create'
                            group by action, region
                            order by 2 desc"""
                    ).df(),
                    x="model",
                    y="val",
                    dimension="region",
                    label="Evaluations",
                ),
                rc.Bar(
                    duckdb.query(
                        """
                            select
                                action as model,
                                count(*) as val,
                                region
                            from t1
                            where category = 'aqua/service/deployment/create'
                            group by action, region
                            order by 2 desc
                            limit 10"""
                    ).df(),
                    x="model",
                    y="val",
                    dimension="region",
                    label="Deployments",
                ),
            ),
        )
        report.save(view, name)


if __name__ == "__main__":
    duckdb.query(
        """
        create table t1 as
            select
                epoch_ms(datetime) as date,
                "category",
                "action",
                "value",
                "ipType",
                "region",
                "authenticationType",
                "tenantName"
            from read_json('20240327_aqua_telemetry_int.json')
    """
    )

    gen_report(
        "telemetry-3-2024.html",
        "AQUA Telemetry Integration March 2024",
        "This report contains the telemetry data for the AQUA project in Integration March 2024",
    )
