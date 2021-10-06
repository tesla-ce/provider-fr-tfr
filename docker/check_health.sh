#!/bin/bash

/venv/bin/celery -A tesla_ce_provider inspect ping -d celery@"$HOSTNAME" --timeout=30

