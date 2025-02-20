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
echo "IAP tunnel established."

# Prompt the user to open Compass manually
echo "Please open MongoDB Compass manually and connect to:"
echo "mongodb://localhost:$LOCAL_PORT"
echo "Press ENTER when you close Compass to shut down the tunnel."
read -p ""

# Cleanup when finished
cleanup
