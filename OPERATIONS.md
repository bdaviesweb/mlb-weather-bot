# Operations Handoff

This repo is ready to run from GitHub Actions after the readiness commit is pushed to `main`.

## Required GitHub Secrets

- `SLACK_WEBHOOK_URL`: posts the daily weather report to `#gameday-weather`.
- `HIGH_RISK_WEBHOOK_URL`: posts high-risk, delay, postponement, and resumption alerts to `#high-risk-weather-alert`.

No weather API key is required. Forecasts use the free National Weather Service API.

## Validation Gates

- `Python CI` runs unit tests and compiles Python entrypoints on Python 3.10.
- `Workflow Lint` runs Actionlint for GitHub Actions workflow changes.
- `Test Venue Locations` remains manual because it calls the live NWS API for every venue.

Local equivalent:

```bash
python -m unittest discover -p 'test_*.py'
python -m py_compile weather_bot.py high_risk_alert.py mlb_game_status_monitor.py analytics.py update_schedule.py test_venues.py venues.py weather.py test_analytics.py test_venues_shared.py test_weather.py test_workflows.py
```

## State Commit Behavior

The daily weather, high-risk alert, and game status monitor workflows share a concurrency group:

```yaml
group: sports-weather-state-${{ github.ref }}
```

That queues state-writing jobs instead of letting scheduled runs race each other. Skipped/off-hours runs still log in workflow output, but they no longer commit analytics-only updates back to `main`.

## First Push Checklist

1. Push the readiness commit to `main`.
2. Confirm `Python CI` passes.
3. Confirm `Workflow Lint` passes.
4. Manually run `Test Venue Locations` after workflow lint passes.
5. Manually dispatch `Daily Weather Report` or `High Risk Weather Alerts` only when Slack posting is expected.

## Current Delivery Blocker

Local SSH authentication works as `bdaviesweb`, but that user does not currently have write permission to `Sports-Weather2/mlb-weather-bot`. Grant write access or push this branch from an account that can write to the repo.
