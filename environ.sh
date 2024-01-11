#!/bin/sh
. ${PYENV_ROOT}/versions/mcps-venv/bin/activate
tmux new-session -d -s mcps-scheduler-v2
# Split pane horizontally
tmux split-window -h
# Split pane horizontally
tmux split-window -v
# Select pane 1
tmux select-pane -t 2
# run flask
tmux send-keys "python app.py" C-m

# Attach to session
tmux attach-session -t mcps-scheduler-v2
