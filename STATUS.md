# 🌤️ System Status

**MLB Weather Monitoring System**

---

## 🟢 OPERATIONAL

**Current Status:** All systems functioning normally
**Last Updated:** May 12, 2026 12:30 PM PT
**Season:** Regular Season 2026

---

## Component Health

| Component | Status | Last Successful Run | Next Run |
|-----------|--------|---------------------|----------|
| 📊 Daily Weather Report (7 AM) | 🟢 Operational | May 12, 2026 7:00 AM PT | May 13, 2026 7:00 AM PT |
| 🚨 High Risk Alert (10 AM) | 🟢 Operational | May 12, 2026 10:00 AM PT | May 13, 2026 10:00 AM PT |
| ⚾ Game Status Monitor | 🟢 Operational | Real-time during game hours | Every 10 min (10 AM - 10 PM PT) |
| 🔌 MLB Stats API | 🟢 Connected | Real-time | Continuous |
| 🌦️ National Weather Service API | 🟢 Connected | Real-time | Continuous |
| 💾 State Persistence | 🟢 Working | May 12, 2026 | Automatic |
| 🏟️ Roof Status API | 🟢 Connected | May 12, 2026 | Continuous |
| ⏰ External Cron Trigger | 🟢 Operational | May 12, 2026 12:30 PM PT | Every 10 min via cron-job.org |

---

## Live Performance Metrics

| Metric | Value |
|--------|-------|
| **Games Monitored** | 327 |
| **Total Alerts Sent** | 157 |
| **Delay Prediction Accuracy** | 45.0% (9/20) |
| **False Positives** | 0 |
| **System Uptime** | 55.6% |
| **Monitoring Interval** | Every 10 min (via cron-job.org) |

---

## 🏟️ Stadium Coverage

**30 MLB Teams** monitored with intelligent filtering:

| Roof Type | Count | Monitoring Strategy |
|-----------|-------|-------------------|
| ☀️ Open-Air | 22 stadiums | Always monitored for weather |
| 🔄 Retractable | 6 stadiums | Monitored when roof is open |
| 🏟️ Fixed Dome | 2 stadiums | Excluded from weather alerts |

**Smart Filtering Benefits:**
- 27% reduction in false weather alerts
- Real-time delay monitoring still covers ALL games
- Roof status included in delay alerts for operational context

---

## Alert Schedule

| Time (PT) | Alert Type | Channel |
|-----------|-----------|---------|
| 7:00 AM | Daily Weather Report | #gameday-weather |
| 10:00 AM | High-Risk Weather Check | #high-risk-weather-alert |
| 10 AM - 10 PM | Real-Time Delay Monitoring | #high-risk-weather-alert |
| Overnight | System Silent | — |

---

## Known Issues

**None currently.**

---

## Scheduled Maintenance

**Next Review:** May 1, 2026
**No manual maintenance required** - System is fully automated.

---

## System Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Scheduling | cron-job.org + GitHub Actions | Reliable 10-min monitoring cycles |
| Game Data | MLB Stats API | Real-time game status and venue info |
| Weather Data | National Weather Service (NWS) API | Hourly forecasts — free, no API key, ~92-95% accuracy |
| Alerts | Slack Webhooks | Real-time notifications to ops team |
| State | game_states.json in GitHub repo | Prevents duplicate alerts |
| Analytics | analytics.json + ANALYTICS.md | Performance tracking and reporting |
| Roof Logic | MLB API + venue mapping | Reduces false positive weather alerts |

---

## Quick Links

- **📖 User Guide:** [Confluence Documentation](https://confluence.dtveng.net/spaces/~le805s/pages/793701279/)
- **💬 Slack Channels:** #gameday-weather, #high-risk-weather-alert
- **📝 Changelog:** [CHANGELOG.md](./CHANGELOG.md)
- **📊 Analytics:** [ANALYTICS.md](./ANALYTICS.md)
- **🔧 GitHub Repo:** https://github.com/Sports-Weather2/mlb-weather-bot

---

## Emergency Contact

**System Owner:** Luis Evangelista
**Slack:** @le805s
**Response Time:** Within 2 hours during business hours for
critical issues

---

_Last generated: May 12, 2026 12:30 PM PT_
