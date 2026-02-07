#!/bin/bash
# SentinelAI Stop Script
pkill -f "uvicorn main:app" 2>/dev/null
echo "✓ Backend gestoppt"
