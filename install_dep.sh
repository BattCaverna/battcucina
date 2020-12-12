#! /bin/bash
set -x

sudo apt update
sudo apt install -y python3 python3-pip

sudo pip3 install -y RPi.GPIO
sudo pip3 install -y rpi_ws281x
