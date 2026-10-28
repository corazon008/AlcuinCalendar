# AlcuinCalendar

## Installation
To install the project, use the following command:

```bash
git clone https://github.com/corazon008/AlcuinCalendar.git
```

Then navigate to the project directory:

```bash
docker compose up -d
```

This will set up the necessary Docker containers for the application.

## Usage
To use the application, open your web browser and go to:
```
http://localhost:5000
```

Once registered, subscribe to the generated feed in your calendar app:
```
https://<your-domain>/agenda/<token>.ics
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `REFRESH_ENABLED` | `true` | Enable the daily automatic refresh |
| `REFRESH_CRON` | unset | Cron expression, e.g. `0 2 * * *` (overrides hour/minute) |
| `REFRESH_HOUR` / `REFRESH_MINUTE` | `2` / `0` | Daily refresh time |
| `REFRESH_TIMEZONE` | `Europe/Paris` | Timezone for the refresh schedule |
| `CALENDAR_CACHE_SECONDS` | `3600` | `Cache-Control` max-age for the ICS feed |
| `SELENIUM_HEADLESS` | `true` | Run Firefox headless (set `false` for debugging) |
| `SELENIUM_ALLOW_LOCAL_FALLBACK` | `false` | Fall back to a local Firefox when `SELENIUM_URL` is unreachable |

Check the queue and next scheduled refresh:
```
curl http://localhost:5000/queue_status
```

> Gunicorn must run with a single worker (`--workers 1`, already set in the
> Dockerfile). Multiple workers would each start their own scheduler and
> duplicate the refresh jobs.
