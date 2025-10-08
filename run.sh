#!/usr/bin/env bash
docker compose down && docker rmi apialcuincalendar-api-alcuin-calendar:latest && docker compose up -d
