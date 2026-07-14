# QueueSmart

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

> A queue management system for smart appointment scheduling. Users can join virtual queues, receive notifications, and track their position in real-time.

**[🌐 Live on GitHub Pages](https://urmat26.github.io/QueueSmart/)**

---

## ✨ Features

- 🎫 **Virtual queue joining** — get in line from anywhere
- 📊 **Real-time position tracking** — know your place in queue
- 🔔 **Status notifications** — get alerted when it's your turn
- 📱 **Responsive design** — works on mobile and desktop

---

## 🛠️ Tech Stack

- **Python 3**
- **Flask** — web framework
- **HTML / CSS / JavaScript** — frontend
- **Heroku / Render** — deployment ready (Procfile + render.yaml included)

---

## 📁 Project Structure

```
QueueSmart/
├── app.py           # Flask application
├── models.py        # Data models
├── config.py        # Configuration
├── routes/          # URL routes
├── services/        # Business logic
├── static/          # CSS, JS, images
├── templates/       # HTML templates
├── requirements.txt
├── Procfile         # Heroku deployment
└── render.yaml      # Render deployment
```

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python app.py
```

---

## ⚠️ Status

Early-stage project. Core queue logic implemented, UI in development.