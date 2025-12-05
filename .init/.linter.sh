#!/bin/bash
cd /home/kavia/workspace/code-generation/ocpp-16-j-charger-simulator-27-721/ChargerSimulatorService
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

