# Python Adventure

A GUI-based Python learning app that grows with you — from a child typing
their very first `print("Hello!")` to an experienced developer keeping
their skills sharp. One offline app, no accounts, no cloud, nothing to
sign up for.

## Who it's for

- **Kids learning Python for the first time** — a guided, game-like path
  through the basics, with encouragement, rewards, and friendly error
  messages instead of intimidating stack traces.
- **Anyone brushing up or going deeper** — hundreds of bite-sized practice
  levels across every core topic, mini-games, and a quiz bank to test
  yourself.
- **Experienced programmers** — the **Advanced Code Crackers** category is
  built specifically for people who already know how to code and want to
  keep their instincts fast: real-world Python gotchas (closures, mutable
  defaults, floating-point precision, aliasing vs. copying, and more) to
  debug, not tutorials to sit through.

## Look & feel

**Dashboard**

![Dashboard](docs/app-screenshots/welcome-screen.jpg)

**Practice by Category**

![Practice by Category](docs/app-screenshots/learn-python-1.jpg)

**Lesson: Meet Python**

![Lesson: Meet Python](docs/app-screenshots/learn-python-2.jpg)

**Settings**

![Settings](docs/app-screenshots/learn-python-3.jpg)

## What's inside

- **Today's Mission** — a guided daily path that starts with the basics
  and works through Numbers, Addition, Subtraction, Multiplication,
  Division, Variables, Strings, Input, Decisions, Loops, Functions, and
  Lists a level at a time, looping back around for deeper levels as you go.
- **Python Learning course** — a structured 6-chapter course (Intro &
  Setup, Variables & Data Types, Control Flow, Functions, Lists & Data
  Structures, and a Capstone To-Do App) that pairs every topic with a
  "What is it?" explanation, a hands-on sample program, and a topic quiz
  before moving on to the next chapter.
- **Practice by Category** — jump into any topic directly and work through
  its full 20-level progression at your own pace, independent of Today's
  Mission.
- **Code Crackers** — 40 short "find the bug and fix it" puzzles covering
  common beginner mistakes: typos, off-by-one errors, wrong comparisons,
  bad indentation, and more.
- **Advanced Code Crackers** — 15 tougher puzzles for people who already
  know Python, covering the kind of subtle bugs that trip up even
  experienced developers. A great way to refresh your memory in a few
  minutes rather than starting a whole new project.
- **Mini-games and projects** — Guess the Number, Rock-Paper-Scissors, the
  Snake project (build a real game step by step), Creative Arts, RPG
  Quests, Arcade Lab, and Robot Adventure.
- **Quiz** — a 300-question multiple-choice quiz covering the whole
  curriculum, reshuffled every time you play, with your best score tracked.
- **Practice Quest** — if you get stuck on the same lesson a few times in a
  row, the app gently suggests related practice to help instead of leaving
  you stuck.
- **Rewards that actually mean something** — stars, badges, player levels,
  day streaks, and a Trophy Room to look back on what you've earned.
- **A Settings screen that's actually comfortable to use** — multiple color
  themes (including dark mode), adjustable font size and font style so
  text is easy to read on anything from a phone to a desktop monitor, and
  a sound toggle.
- **A Parent Area** — PIN-protected (set the first time you open it),
  showing a summary of progress, recent activity, and a way to reset
  progress if needed.
- **100% offline and private** — everything runs and stays on your device.
  No accounts, no network access, no data collection.

## Getting started

**Easiest way (no terminal needed):** double-click `run.bat` (Windows) or
run `./run.sh` (git-bash/macOS/Linux). The first run takes a minute to set
itself up; every run after that launches straight into the app.

First launch walks you through a short setup — just a name — and lands you
on the dashboard, ready to go. The first time you open the Parent Area,
you'll be asked to set a PIN to protect it.

## For developers

- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — project layout, how each
  subsystem works, running it/testing it.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system context, class
  diagrams, sequence diagrams, the persistence model, and the design
  decisions behind them.
