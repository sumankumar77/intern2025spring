import os
import csv
import glob

from minify import process_single_css_file, process_single_js_file


def remove_other_min_files(kept_min_file):
    file_path, file_name = os.path.split(kept_min_file)
    file_name_parts = file_name.split('.')
    if len(file_name_parts) == 3 and file_name_parts[-2] == 'min' and file_name_parts[-3].rfind('-') > 0:
        src_file_name = file_name_parts[0][:file_name_parts[0].rfind('-')]
        file_pattern = file_path + '/' + src_file_name + '-[0-9|a-z]*' + '.'.join(file_name_parts[1:])
        match_files = glob.glob(file_pattern)
        for filename in match_files:
            if filename != kept_min_file:
                os.remove(filename)


cwd = os.getcwd()
proj_path = os.path.dirname(cwd)
static_path = os.path.join(proj_path, 'static')
min_filenames_with_hash = ['main.css', 'simple.css', 'main.js', 'chartables.js', 'Chart.plugins.js',
                           'chartjs-plugin-ant.js', 'chartjs-plugin-gantt.js', 'study.js', 'v2/app.css', 
                           'v2/main.js', 'chart_utils.js', 'dashcards.js', 
                           'v2/chart-utils.css', 'v2/chart-utils.js', 'fsucon/app.css']

rows = []
with open('to_prod_static_input.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)


processed_files = {}
for row in rows:
    src_file, template_name = row[0], row[1]
    src_filename, src_ext = os.path.splitext(src_file)
    # only css and js files are minified
    static_type = src_ext.replace('.', '')
    src_file_path = os.path.join(static_path, static_type)
    full_path_src_file = os.path.join(src_file_path, src_file)
    if not os.path.exists(full_path_src_file):
        # source file is not in static folder, this could be a local file
        template_path, _ = os.path.split(template_name)
        template_full_path = os.path.join(cwd, template_path)
        full_path_src_file = os.path.join(template_full_path, src_file)
        if not os.path.exists(full_path_src_file):
            print('Cannot find source file %s' % src_file)
            continue

    add_hash = True if src_file in min_filenames_with_hash else False
    if static_type == 'css':
        full_path_min_file = process_single_css_file(full_path_src_file, add_hash=add_hash)
    elif static_type == 'js':
        full_path_min_file = process_single_js_file(full_path_src_file, add_hash=add_hash)
    else:
        full_path_min_file = None

    if not full_path_min_file:
        print('Type of static file not found: %s' % src_file)
        continue

    if add_hash:
        remove_other_min_files(full_path_min_file)

    min_file = os.path.basename(full_path_min_file)
    # Check if src_file is in sub folder
    if os.path.dirname(src_file):    # return '' if no sub folder
        min_file = os.path.join(os.path.dirname(src_file), min_file)

    # replace the source static file with minified static file
    template = os.path.join(cwd, template_name)
    with open(template, 'r') as file:
        text = file.read().replace(src_file, min_file)
    with open(template, 'w') as file:
        file.write(text)
