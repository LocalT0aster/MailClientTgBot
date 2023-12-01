#!/bin/bash
docker stop mailbot || true
docker rm mailbot || true
docker rmi mailbot-img
docker compose up -d --build
