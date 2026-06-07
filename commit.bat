@echo off
git add .
git commit -m "Update log dan context (postpone web app)"
git log -1 --format="%%h"
