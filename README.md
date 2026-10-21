# Southern Company Grid Demand Data Pipeline
End-to end automated daily scheduled pipeline through GitHub Actions (Python → BigQuery → dbt) that feeds into Power BI Dashboard 

![daily-pipeline](https://github.com/ksampath0/energy-demand-pipeline/actions/workflows/daily.yml/badge.svg)

This is an automated scheduled daily pipeline measuring how accurate the Georgia grid operator forecasts
day-ahead electricity demand and determines when it is inaccurate 

The main question being answered here: When grid operators (Southern Company) release their daily day-ahead demand forecast, how accurate are they, and if there are inaccuracies, can they be predicted? 