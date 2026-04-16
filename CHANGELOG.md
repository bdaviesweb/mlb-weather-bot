# Changelog

All notable changes to the MLB Weather Monitoring System.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

---

## [1.4.0] - 2026-04-16

### ✨ Added

#### External Cron Trigger via `cron-job.org` — Reliable 10-Minute Monitoring
- **Problem:** GitHub Actions free tier was delaying or skipping
  scheduled `*/10 * * * *` cron runs by 30–60 minutes during peak
  infrastructure hours — causing rain delays to go undetected for
  extended periods requiring manual intervention
- **Solution:** Configured `cron-job.org` (free external service)
  to trigger the MLB Status Monitor workflow every 10 minutes via
  the GitHub API `workflow_dispatch` event — bypassing GitHub's
  unreliable scheduler entirely

#### `cron-job.org` Configuration
- **Title:** MLB Status Monitor
- **URL:** `https://api.github.com/repos/Sports-Weather2/mlb-weather-bot/actions/workflows/mlb-status-monitor-v2.yml/dispatches`
- **Schedule:** Every 10 minutes guaranteed
- **Method:** POST
- **Headers:**
  - `Authorization: Bearer [token]`
  - `Accept: application/vnd.github.v3+json`
  - `Content-Type: application/json`
- **Body:** `{"ref":"main"}`
- **Timezone:** America/Los_Angeles

### 🔧 Changed

#### `mlb-status-monitor-v2.yml`
- Workflow now triggered by `workflow_dispatch` from `cron-job.org`
  instead of relying solely on GitHub's built-in `schedule` cron
- GitHub's native `*/10 * * * *` cron remains as a **backup**
  in case `cron-job.org` is unavailable
- Trigger source now visible in GitHub Actions run history:
  - `workflow_dispatch` = cron-job.org fired ✅
  - `schedule` = GitHub native backup fired

### 🎯 Impact
- **Guaranteed 10-minute detection cycles** — no more 30–60 minute
  gaps during peak GitHub infrastructure hours
- **Rain delays detected within 10 minutes** of MLB API updating
  instead of up to 60 minutes previously
- **Both delays on April 16** (White Sox/Royals and Royals/Tigers)
  required manual triggers due to GitHub cron lag — this fix
  eliminates that need going forward
- **Zero code changes** to Python scripts or alert logic —
  purely an infrastructure reliability improvement

### 📊 Monitoring Reliability (Before vs After)

| | Before | After |
|---|---|---|
| Trigger source | GitHub cron (unreliable) | cron-job.org (reliable) |
| Typical delay | 30–60 min during peak hours | ~10 min guaranteed |
| Missed runs | Frequent during business hours | None expected |
| Manual triggers needed | Yes — when delay spotted | No — automatic |
| Backup trigger | None | GitHub native cron |

### 📋 Full Monitoring Stack

| Layer | Tool | Frequency |
|---|---|---|
| Daily weather report | GitHub cron | 7 AM PT |
| High risk alert | GitHub cron | 10 AM PT |
| Game status monitor | cron-job.org ✅ | Every 10 min guaranteed |
| Manual backup | GitHub Run workflow | On demand |

---

## [1.3.4] - 2026-04-08

### 🐛 Fixed

#### `mlb-status-monitor-v2.yml` — Commit Step Failing with Exit Code 1
- **Root cause:** `git add` was staging all files in a single line
  with `2>/dev/null || true` which silently suppressed staging
  errors, leaving files modified but unstaged. The commit condition
  `git diff --quiet && git diff --staged --quiet` then detected
  unstaged working directory changes and exited with code 1,
  failing the entire job
- **Symptom:** GitHub Actions showed red ❌ on
  **"Commit game state tracking and analytics"** step with:
