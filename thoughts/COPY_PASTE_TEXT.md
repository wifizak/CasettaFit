# Copy-Paste Text for Quick Setup

## GitHub Repository Description
```
A powerful self-hosted workout tracking web app for home gyms. Track exercises, log workouts with RPE, manage training programs, and monitor progress. Built with Flask & Python. Mobile-optimized interface with rest timers and smart weight suggestions.
```

---

## GitHub Topics (copy and paste into topics field, comma-separated)
```
fitness, workout-tracker, gym, fitness-app, workout-log, strength-training, weightlifting, flask, python, self-hosted, exercise-tracker, progressive-overload, home-gym, flask-application, sqlite, nginx, bootstrap5, workout-planner, fitness-tracking, rpe-tracking
```

---

## Reddit Post for r/SideProject

### Title:
```
Built CasettaFit - A self-hosted workout tracker for home gym enthusiasts 💪
```

### Body:
```
Hey everyone! 👋

I've been working on **CasettaFit**, a self-hosted web application for tracking workouts, and I wanted to share it with this community.

## What is it?

CasettaFit is a comprehensive workout tracking platform designed for people who:
- Work out at home gyms
- Value data privacy (self-hosted = your data stays yours)
- Want detailed workout logging with RPE (Rate of Perceived Exertion)
- Need mobile-friendly workout execution

## Key Features:

✅ Create custom training programs with multiple weeks/days
✅ Log workouts with weight, reps, and RPE for each set
✅ Smart suggestions based on previous performance
✅ Rest timers between sets (with skip option)
✅ View previous workout history inline
✅ Mobile-optimized interface for gym use
✅ Multiple gym locations & equipment tracking
✅ Progress charts and analytics

## Tech Stack:

- Backend: Flask (Python)
- Frontend: Bootstrap 5 + Vanilla JS
- Database: SQLite + SQLAlchemy
- Server: Gunicorn + NGINX
- One-command setup with systemd service

## Why I built it:

I got tired of fitness apps that:
- Cost monthly subscriptions
- Send my workout data to the cloud
- Have clunky mobile interfaces
- Don't support home gym workflows

So I built my own! It's completely free, self-hosted, and designed specifically for how I actually work out.

## Current Status:

✅ Fully functional and production-ready
✅ Running on my own server for several months
✅ Mobile-responsive design tested on iOS/Android
🚧 Documentation is complete
🚧 Looking for feedback and contributors!

## What's Next:

- Export/import workout data
- Workout templates
- Progressive overload calculator
- Body measurements tracking
- Exercise instruction images/videos

## Links:

- **GitHub**: https://github.com/YOUR_USERNAME/CasettaFit
- **License**: MIT (free & open source)
- **Setup**: One bash script handles everything

Would love to hear your feedback! What features would you want to see in a workout tracker?

---

*PS: This is my first major Flask project, so constructive criticism is very welcome!*
```

---

## For r/homegym (slightly modified):

### Title:
```
Built a free self-hosted workout tracker specifically for home gyms
```

### Body:
```
Hey home gym fam! 🏋️

I've been running a home gym for a while and got frustrated with existing workout tracking apps. They're either expensive, cloud-based (privacy concerns), or have terrible mobile interfaces for actually logging workouts.

So I built **CasettaFit** - a self-hosted workout tracker designed specifically for home gym workflows.

## What makes it different for home gyms:

🏠 **Multi-gym support** - Track your home gym, commercial gym, or anywhere you work out
🔧 **Equipment tracking** - Link exercises to your specific equipment
📱 **Mobile-optimized** - Large buttons, one-at-a-time set logging perfect for using between sets
⏱️ **Smart rest timers** - Auto-countdown between sets (with skip option when you're feeling strong)
📊 **Previous set history** - See exactly what weight/reps you did last time, right on the logging screen
💪 **RPE tracking** - Log how each set felt (too heavy, just right, could do more)

## Tech details:

- Self-hosted (runs on your own server/Raspberry Pi)
- Free and open source (MIT license)
- One-command setup script
- Works on any device (desktop/tablet/phone)
- Your data stays yours

## Features:

- Create multi-week training programs
- Log weight, reps, and RPE for every set
- Smart weight suggestions based on previous workouts
- Workout history and progress tracking
- Superset support
- Exercise library with custom additions

It's been running smoothly for me for months. Figured others in this community might benefit!

**GitHub**: https://github.com/YOUR_USERNAME/CasettaFit

Happy to answer any questions or take feature requests. What do you track that I'm missing?
```

---

## For r/selfhosted:

### Title:
```
CasettaFit - Self-hosted workout and exercise tracking application
```

### Body:
```
**Project:** CasettaFit
**Type:** Workout/Fitness Tracker
**License:** MIT (Open Source)
**Language:** Python (Flask)

## Overview

A comprehensive self-hosted workout tracking application for gym enthusiasts who value data privacy.

## Why self-host a workout tracker?

- **Privacy**: Your workout data stays on your server
- **No subscriptions**: One-time setup, no monthly fees
- **Customization**: Fork and modify as needed
- **Offline capability**: Works on local network
- **Data ownership**: Full control over exports/backups

## Features

- Multi-week training program creation
- Exercise library with custom additions
- Workout execution with mobile-optimized UI
- RPE (Rate of Perceived Exertion) tracking
- Rest timer with skip option
- Progress charts and analytics
- Multi-gym support
- Equipment tracking
- Workout history
- Previous set history (see last performance inline)
- User management (admin/regular users)

## Tech Stack

- **Backend:** Flask (Python 3.8+)
- **Database:** SQLite + SQLAlchemy ORM
- **Frontend:** Bootstrap 5, Vanilla JS
- **Server:** Gunicorn + NGINX reverse proxy
- **Service:** Systemd for auto-start
- **SSL:** Let's Encrypt, self-signed, or custom cert support

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/CasettaFit.git /opt/CasettaFit
cd /opt/CasettaFit/app
sudo bash setup.sh
```

One script handles:
- Python venv setup
- Database initialization
- Systemd service creation
- NGINX configuration
- Admin user creation

Then optionally configure SSL:
```bash
sudo bash setup_ssl.sh
```

## System Requirements

- Ubuntu/Debian-based Linux
- Python 3.8+
- 512MB RAM minimum
- ~100MB disk space
- Port 80/443 available

## Resource Usage

- **Memory:** ~100-150MB
- **CPU:** Minimal (idle <1%)
- **Storage:** ~50MB + your workout data

## Screenshots

[Add when ready]

**Links:**
- GitHub: https://github.com/YOUR_USERNAME/CasettaFit
- Documentation: See README and SSL_SETUP.md

Been running it for months without issues. Open to feedback and contributions!
```

---

Remember to replace `YOUR_USERNAME` with your actual GitHub username!
