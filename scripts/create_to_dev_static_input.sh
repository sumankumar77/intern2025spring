#!/bin/bash
#
# Usage:
#	$ create_to_dev_static_input.sh
#

# define patterns and paths
patterns=('main[-|0-9|a-z]*\.min.css' 'main[-|0-9|a-z]*\.min.js' 'chartables[-|0-9|a-z]*\.min.js' \
          'Chart.plugins[-|0-9|a-z]*\.min.js' 'chartjs-plugin-ant[-|0-9|a-z]*\.min.js' \
          'chartjs-plugin-gantt[-|0-9|a-z]*\.min.js' 'dash.min.js' 'logs.min.js' \
          'level.min.js' 'connected_chart.min.js')
#paths=(../templates/chealth/*.html ../apps/*/templates/*/*.html)

# create file for static files info
echo -n "" > to_dev_static_input.csv

for pattern in "${patterns[@]}"
do
  grep "$pattern" ../templates/chealth/*.html | while read -r line ; do
    IFS=':'
    read -r -a strarr <<< "$line"
    echo "$pattern,${strarr[0]}" >> to_dev_static_input.csv
  done
  grep "$pattern" ../apps/*/templates/*/*.html | while read -r line ; do
    IFS=':'
    read -r -a strarr <<< "$line"
    echo "$pattern,${strarr[0]}" >> to_dev_static_input.csv
  done
done

