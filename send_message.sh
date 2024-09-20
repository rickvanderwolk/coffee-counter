#!/bin/bash

if [ -z "$1" ]; then
  echo "Use: ./send_message.sh '<message>'"
  exit 1
fi

MESSAGE="$1"

if ! python3 -c "import json; json.loads('$MESSAGE')" 2>/dev/null; then
  echo "Invalid JSON format"
  exit 1
fi

/home/jan/coffee-counter/bin/python - << EOF
import asyncio
import websockets

async def send_message(message):
    uri = "ws://jan.local:6789"
    async with websockets.connect(uri) as websocket:
        await websocket.send(message)
        print(f"Message send: {message}")

asyncio.run(send_message('''$MESSAGE'''))
EOF
