#!/bin/bash

# Configuration Variables
INSTANCE_NAME="[INSTANCE_NAME]"   # Replace with your GCP instance name
ZONE="[ZONE]"                     # Replace with your GCP instance zone
LOCAL_PORT=27017                  # Local port for MongoDB Compass to connect to
REMOTE_PORT=27017                 # Default MongoDB port

# Function to clean up the tunnel when Compass is closed
cleanup() {
    echo "Closing IAP tunnel..."
    kill $TUNNEL_PID
    echo "Tunnel closed."
    exit 0
}

# Start the IAP tunnel
echo "Starting IAP tunnel to $INSTANCE_NAME on port $REMOTE_PORT..."
gcloud compute start-iap-tunnel $INSTANCE_NAME $REMOTE_PORT \
    --zone=$ZONE \
    --local-host-port=localhost:$LOCAL_PORT &
TUNNEL_PID=$!

# Wait a few seconds for the tunnel to establish
sleep 5
echo "IAP tunnel established. Launching MongoDB Compass..."

# Launch MongoDB Compass with the tunnel connection
# Update the path if Compass is installed elsewhere
COMPASS_PATH="/Applications/MongoDB Compass.app/Contents/MacOS/MongoDB Compass"
"$COMPASS_PATH" "mongodb://localhost:$LOCAL_PORT"

# Once Compass closes, run cleanup
cleanup
