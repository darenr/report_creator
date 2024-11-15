import report_creator as rc

with rc.ReportCreator(
    title="My Report",
    description="My Report Description",
    footer="My Report Footer",
) as report:
    view = rc.Block(
        rc.Group(
            rc.Gauge(value=312, label="Trump", min_value=0, max_value=538),
            rc.Gauge(value=226, label="Harris", min_value=0, max_value=538),
        ),
    )

    report.save(view, "gauge.html")
