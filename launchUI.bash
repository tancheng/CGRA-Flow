#!/bin/bash

input_theme=$1
echo "Theme: $input_theme"

cd build
if [ "$input_theme" == "classic" ]; then
      echo "classic theme selected"
      #start dark theme
      python ../launchUI_classic.py
elif [ "$input_theme" == "light" ]; then
      echo "light theme selected"
      #start light theme
      python ../launchUI.py --theme light
else
      echo "No theme selected, will start default theme (dark mode)"
      #start default theme (dark mode)
      python ../launchUI.py
fi

