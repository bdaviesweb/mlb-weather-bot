import analyticsData from "../analytics.json";
import configData from "../config.json";

type Game = {
  date: string;
  time: string;
  opponent: string;
  location: string;
  venue?: string;
  game_pk?: number;
};

type Analytics = {
  metadata?: {
    last_updated?: string;
    season?: string;
  };
  totals?: Record<string, number>;
  accuracy?: Record<string, number>;
  workflow_runs?: Record<string, number>;
  daily_activity?: Record<string, {
    alerts_sent?: number;
    games_monitored?: number;
    alert_types?: Array<{ type: string; timestamp: string }>;
  }>;
};

function formatNumber(value?: number) {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

function formatPercent(value: number) {
  return `${value.toFixed(1)}%`;
}

function formatTime(value?: string) {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function getRecentActivity(analytics: Analytics) {
  return Object.entries(analytics.daily_activity ?? {})
    .sort(([left], [right]) => right.localeCompare(left))
    .slice(0, 7)
    .map(([date, activity]) => ({
      date,
      alerts: activity.alerts_sent ?? 0,
      monitored: activity.games_monitored ?? 0,
      types: activity.alert_types ?? [],
    }));
}

function getAlertMix(totals: Analytics["totals"]) {
  return [
    ["Daily reports", totals?.daily_reports_sent ?? 0],
    ["High-risk alerts", totals?.high_risk_alerts_sent ?? 0],
    ["Delay alerts", totals?.delay_alerts_sent ?? 0],
    ["Resumptions", totals?.resumption_alerts_sent ?? 0],
    ["Postponements", totals?.postponement_alerts_sent ?? 0],
  ];
}

export default function Home() {
  const config = configData as { games: Game[] };
  const analytics = analyticsData as Analytics;
  const totals = analytics.totals ?? {};
  const workflow = analytics.workflow_runs ?? {};
  const accuracy = analytics.accuracy ?? {};
  const recentActivity = getRecentActivity(analytics);
  const alertMix = getAlertMix(totals);
  const totalWorkflowRuns = workflow.total_runs ?? 0;
  const workflowSuccessRate = totalWorkflowRuns
    ? ((workflow.successful_runs ?? 0) / totalWorkflowRuns) * 100
    : 0;
  const uptime = totalWorkflowRuns
    ? (((workflow.successful_runs ?? 0) + (workflow.skipped_runs ?? 0)) / totalWorkflowRuns) * 100
    : 0;
  const delayAccuracy = accuracy.actual_delays
    ? ((accuracy.delays_predicted ?? 0) / accuracy.actual_delays) * 100
    : 0;
  const games = config.games ?? [];

  return (
    <main className="dashboard-shell">
      <section className="top-band">
        <div className="top-copy">
          <p className="eyebrow">MLB Weather Tracker</p>
          <h1>Operations dashboard for game-day weather risk.</h1>
          <p className="lede">
            Live bot state, alert history, schedule coverage, and workflow health in one place.
          </p>
        </div>
        <div className="status-panel" aria-label="System status">
          <span className="status-pill">Operational</span>
          <strong>{formatPercent(uptime)}</strong>
          <span>Last updated {formatTime(analytics.metadata?.last_updated)}</span>
        </div>
      </section>

      <section className="metric-grid" aria-label="Key metrics">
        <article>
          <span>Games monitored</span>
          <strong>{formatNumber(totals.games_monitored)}</strong>
          <p>{games.length} games loaded for the current schedule window.</p>
        </article>
        <article>
          <span>Total alerts</span>
          <strong>{formatNumber(totals.alerts_sent)}</strong>
          <p>Includes daily, high-risk, delay, resumption, and postponement alerts.</p>
        </article>
        <article>
          <span>Workflow success</span>
          <strong>{formatPercent(workflowSuccessRate)}</strong>
          <p>{formatNumber(workflow.failed_runs)} failed runs out of {formatNumber(totalWorkflowRuns)}.</p>
        </article>
        <article>
          <span>Delay prediction</span>
          <strong>{formatPercent(delayAccuracy)}</strong>
          <p>{formatNumber(accuracy.delays_predicted)} predictions across {formatNumber(accuracy.actual_delays)} actual delays.</p>
        </article>
      </section>

      <section className="content-grid">
        <div className="panel schedule-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Today</p>
              <h2>Game Coverage</h2>
            </div>
            <span>{games.length} games</span>
          </div>
          <div className="game-list">
            {games.map((game) => (
              <article className="game-row" key={game.game_pk ?? `${game.opponent}-${game.time}`}>
                <div>
                  <strong>{game.opponent}</strong>
                  <span>{game.venue || game.location}</span>
                </div>
                <time>{game.time}</time>
              </article>
            ))}
          </div>
        </div>

        <aside className="panel run-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Automation</p>
              <h2>Run State</h2>
            </div>
          </div>
          <dl className="run-list">
            <div>
              <dt>Daily report</dt>
              <dd>{formatNumber(totals.daily_reports_sent)}</dd>
            </div>
            <div>
              <dt>High-risk check</dt>
              <dd>{formatNumber(totals.high_risk_alerts_sent)}</dd>
            </div>
            <div>
              <dt>Season</dt>
              <dd>{analytics.metadata?.season ?? "Regular Season"}</dd>
            </div>
            <div>
              <dt>Data refresh</dt>
              <dd>{formatTime(analytics.metadata?.last_updated)}</dd>
            </div>
          </dl>
          <div className="link-stack">
            <a href="https://github.com/bdaviesweb/mlb-weather-bot/actions">GitHub Actions</a>
            <a href="https://github.com/bdaviesweb/mlb-weather-bot/issues">Alert Issues</a>
            <a href="https://github.com/bdaviesweb/mlb-weather-bot">Repository</a>
          </div>
        </aside>
      </section>

      <section className="lower-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Alerts</p>
              <h2>Notification Mix</h2>
            </div>
          </div>
          <div className="bar-list">
            {alertMix.map(([label, value]) => {
              const max = Math.max(...alertMix.map(([, count]) => count), 1);
              return (
                <div className="bar-row" key={label}>
                  <span>{label}</span>
                  <div aria-hidden="true">
                    <i style={{ width: `${(value / max) * 100}%` }} />
                  </div>
                  <strong>{formatNumber(value)}</strong>
                </div>
              );
            })}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Recent</p>
              <h2>Activity Trail</h2>
            </div>
          </div>
          <div className="activity-list">
            {recentActivity.map((day) => (
              <div className="activity-row" key={day.date}>
                <div>
                  <strong>{day.date}</strong>
                  <span>{day.types.map((type) => type.type).slice(0, 3).join(", ") || "No alerts"}</span>
                </div>
                <span>{day.alerts} alerts</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
