#!/bin/bash

echo "Starting containers..."
docker-compose up --build

echo "Waiting for services to start..."
sleep 5

echo "Opening browser..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost:8080
elif command -v kde-open &> /dev/null; then
    kde-open http://localhost:8080
else
    echo "Please open http://localhost:8080 in your browser"
fi

echo "Showing logs..."
docker-compose logs -f 