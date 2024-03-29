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
    with rc.ReportCreator(title=title, description=description) as report:
        view = rc.Block(
            rc.Plot(
                duckdb.query(
                    """
                        select tenantName, count(*) as val
                        from t1
                        group by tenantName
                        order by 2 desc
                        limit 10"""
                )
                .df()
                .plot.bar(x="tenantName", y="val", rot=0),
                label="Top Tenant Names",
            ),
            rc.Group(
                rc.Plot(
                    duckdb.query(
                        """
                            select
                                action as model,
                                count(*) as val
                            from t1
                            where category = 'aqua/custom/deployment/create'
                            group by action
                            order by 2 desc
                            limit 10"""
                    )
                    .df()
                    .plot.bar(
                        x="model",
                        y="val",
                        figsize=(15, 10),
                        fontsize=15,
                    ),
                    label="Top Models used for Deployment",
                ),
                rc.Plot(
                    duckdb.query(
                        """
                            select
                                action as model,
                                count(*) as val
                            from t1
                            where category = 'aqua/evaluation/create'
                            group by action
                            order by 2 desc
                            limit 10"""
                    )
                    .df()
                    .plot.bar(
                        x="model",
                        y="val",
                        figsize=(15, 10),
                        fontsize=15,
                    ),
                    label="Top Models used for Evaluation",
                ),
            ),
            rc.DataTable(
                duckdb.query(
                    """
                        select
                            unquote(value) as error,
                            count(*) as frequency
                        from t1
                        where category = 'aqua/error'
                        group by value
                        order by frequency desc
                """
                ).df(),
                label="Most Common Errors",
            ),
        )
        report.save(view, name, mode="light")


report_month, report_year = (3, 2024)

if __name__ == "__main__":
    duckdb.query(
        f"""
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
            where month(epoch_ms(datetime)) = {report_month} and year(epoch_ms(datetime)) = {report_year}
    """
    )

    gen_report(
        "telemetry-3-2024.html",
        "AQUA Telemetry Integration March 2024",
        "This report contains the telemetry data for the AQUA project in Integration March 2024",
    )
