#! /bin/bash
set -x

sudo apt update
sudo apt install -y python3 python3-pip

sudo pip3 install RPi.GPIO
sudo pip3 install rpi_ws281x
