#!/bin/bash
#
# Usage:
#	$ create_to_prod_static_input.sh
#

# define patterns and paths
patterns=('main.css' 'simple.css' 'main.js' 'chartables.js' 'Chart.plugins.js' \
          'chartjs-plugin-ant.js' 'chartjs-plugin-gantt.js' \
          'dash.js' 'logs.js' 'level.js' 'connected_chart.js')
#paths=(../templates/chealth/*.html ../apps/*/templates/*/*.html)

# create file for static files info
echo -n "" > to_prod_static_input.csv

for pattern in "${patterns[@]}"
do
  grep "$pattern" ../templates/chealth/*.html | while read -r line ; do
    IFS=':'
    read -r -a strarr <<< "$line"
    echo "$pattern,${strarr[0]}" >> to_prod_static_input.csv
  done
  grep "$pattern" ../apps/*/templates/*/*.html | while read -r line ; do
    IFS=':'
    read -r -a strarr <<< "$line"
    echo "$pattern,${strarr[0]}" >> to_prod_static_input.csv
  done
done

