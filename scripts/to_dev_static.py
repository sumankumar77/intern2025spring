import os
import re
import csv


cwd = os.getcwd()

rows = []
with open('to_dev_static_input.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

for row in rows:
    grep_pattern, template_name = row[0], row[1]
    # bash grep pattern backslash dot (\.) creates double backslashes in python string
    min_name = grep_pattern.replace('\\', '')
    # get the static source file name by replacing hash and .min
    src_name = min_name.replace('[-|0-9|a-z]*', '').replace('.min', '')
    # replace the min file with non-min file
    template = os.path.join(cwd, template_name)
    if os.path.exists(template):
        with open(template, 'r') as f:
            text = re.sub(min_name, src_name, f.read())
        with open(template, 'w') as f:
            f.write(text)
    else:
        print('%s does not exist.' % template)
