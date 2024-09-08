#!/bin/bash

input_theme=$1
echo "Theme: $input_theme"

cd build
if [ "$input_theme" == "dark" ]; then
      echo "Dark theme selected"
      #start dark theme
      python ../launchUI_custom.py
elif [ "$input_theme" == "light" ]; then
      echo "Light theme selected"
      #start light theme
      python ../launchUI_custom.py --theme light
else
      echo "No theme selected, will start default theme"
      #start default theme
      python ../launchUI.py
fi

