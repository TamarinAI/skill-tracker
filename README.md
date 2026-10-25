# skill-tracker

Standalone Monash Automation skill tracker — split out of
[discordbot](https://github.com/monashautomation/discordbot) (discordbot.monashautomation.com).

Tracks member skill ratings (6-axis hexagon), a points ledger, physical
inductions, and scalable training content (KUKA arm first, then CNC / Prusa /
Doosan). The Discord bot (Tamarin) consumes this API to upgrade Discord roles
as members progress; the KUKA training site calls it to award lesson and
action-item points.

## Stack

- Backend: Django 6 (SQLite for dev, Postgres in prod)
- Auth: shared bearer token (`SKILL_TRACKER_TOKEN` env, or `backend/.token`
  file locally) + `X-Caller-Member: <discord_id>` for on-behalf-of calls

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health/` | liveness (open) |
| GET | `/api/members/` | all members with skills/points/inductions |
| GET | `/api/members/<discord_id>/` | one member's profile |
| POST | `/api/members/<discord_id>/points/` | award points (bounty / engagement / lesson / action_item / manual) |
| POST | `/api/lessons/<id>/complete/` | complete a lesson (enforces induction gate + quiz pass, awards points) |
| PATCH | `/api/inductions/<id>/review/` | admin approves/rejects a physical induction |

## Run locally

```bash
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements.txt
echo "your-dev-token" > .token
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Domain model

`Member` · `MemberRoster` (Notion mirror) · `SkillRating` (6 axes, 0–10) ·
`PointsEntry` (ledger) · `InductionType`/`Induction` (physical gate) ·
`EquipmentGroup`/`Lesson`/`Quiz`/`LessonCompletion` (training) ·
`ActionItem` (Notion action items → points) · `RoleRule` (points → Discord role).
