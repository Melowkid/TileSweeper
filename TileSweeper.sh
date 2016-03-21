#!bin/bash
cd ~/experiment

echo "Please enter your subject ID"
read id

echo "The experiment will start momentarily..."
python TileSweeper.py $id