import os
import re
import sys
import getopt
import shutil


def slugify(input_str):
    output_str = ''
    for c in input_str:
        if c in 'abcdefghijklmnopqrstuvwxyz0123456789-_':
            output_str += c
    return output_str


def process_output_css_file(chiron_path, dest_static_dir):
    print('Processing output.min.css file')
    ref_text = ''
    ref_file = os.path.join(chiron_path, 'sleep/html5/data/css/output.min.css')
    with open(ref_file, 'r', encoding='UTF-8-sig') as file:
        lines = file.readlines()
    ref = False
    for line in lines:
        if '{' in line:
            if '.cs-HTML' or '.cs-npxnabnsnfns10111000101' in line:
                ref = True
            else:
                ref = False
        if ref:
            ref_text += line

    target_file = os.path.join(dest_static_dir, 'html5/data/css/output.min.css')
    with open(target_file, 'r', encoding='UTF-8-sig') as file:
        lines = file.readlines()
    text = ''
    replace = False
    copy_ref = True
    for line in lines:
        if '{' in line:
            if '.cs-pxabnsnfns00011000101' in line:
                replace = True
                if copy_ref:
                    text += ref_text
                    copy_ref = False
            else:
                replace = False
        if not replace:
            text += line
    text = text.replace('.cs-npxnabnsnfns10111000101', '.cs-pxabnsnfns00011000101')
    with open(target_file, 'w', encoding='utf8') as file:
        file.write(text)


def main(argv):
    src_dir = ''
    overwrite = False
    opts, args = getopt.getopt(argv, "s:o", ["src=", "override"])
    for opt, arg in opts:
        if opt in ("-s", "--src"):
            src_dir = arg
        elif opt in ("-o", "--override"):
            overwrite = True
    if not src_dir:
        print("Source directory is missing. add_articulate_storyline.py -s path_to_articulate_lesson_folder")
        return
    if not os.path.isdir(src_dir):
        print("Source directory does not exist.")
        return
    # Check if all dirs and files exist
    folders = ['story_content', 'mobile', 'html5/data/css', 'html5/data/js']
    files = ['story.html']
    for folder in folders:
        if not os.path.isdir(os.path.join(src_dir, folder)):
            print('Directory {} does not exist.'.format(folder))
            return
    for lesson_file in files:
        if not os.path.isfile(os.path.join(src_dir, lesson_file)):
            print('File {} does not exist.'.format(lesson_file))
            return

    # Create lesson folder in the destination directory
    cwd = os.getcwd()
    proj_path = os.path.dirname(cwd)
    chiron_path = os.path.join(proj_path, 'static/chiron')
    sub_dir, original_lesson_folder = os.path.split(src_dir)
    lesson_folder = slugify(original_lesson_folder.replace(' ', '-').lower())
    dest_static_dir = os.path.join(chiron_path, lesson_folder)
    if os.path.exists(dest_static_dir) and not overwrite:
        print('Lesson already exists in target directory.')
        return
    elif not os.path.exists(dest_static_dir):
        os.mkdir(dest_static_dir)
    # lesson_path does not exist or override
    dest_template_dir = os.path.join(proj_path, 'studies/chiron/templates/chiron', lesson_folder)
    if not os.path.exists(dest_template_dir):
        os.mkdir(dest_template_dir)
    try:
        print('Start copying lesson files')
        # Create all folders if they don't exist
        target_folders = ['html5', 'html5/data', 'html5/data/css', 'html5/data/js', 'mobile', 'story_content']
        for folder in target_folders:
            path = os.path.join(dest_static_dir, folder)
            if not os.path.exists(path):
                os.mkdir(path)
        copy_static_folders = ['html5/data/css', 'html5/data/js', 'mobile', 'story_content']
        for folder in copy_static_folders:
            s_dir, d_dir = os.path.join(src_dir, folder), os.path.join(dest_static_dir, folder)
            files = os.listdir(s_dir)
            for file_name in files:
                src_file = os.path.join(s_dir, file_name)
                dest_file = os.path.join(d_dir, file_name)
                if os.path.isfile(src_file):
                    shutil.copy(src_file, dest_file)
        process_output_css_file(chiron_path, dest_static_dir)

        copy_template_files = ['story.html']
        for file_name in copy_template_files:
            src_file = os.path.join(src_dir, file_name)
            dest_file = os.path.join(dest_template_dir, file_name)
            shutil.copy(src_file, dest_file)
        print('Start editing story.html')
        target_file = os.path.join(dest_template_dir, 'story.html')
        bootstrapper_replacement = \
            '<script src="{% static \'chiron/html5/lib/scripts/bootstrapper.js\' %}"></script>\n' + \
            '<script type="text/javascript">\n' + \
            '(function () {\n' + \
            '  window.addEventListener("message", (event) => {\n' + \
            '    const data = JSON.parse(event.data);\n' + \
            '    console.log("Received:", data);\n' + \
            '  }, false);\n' + \
            '})();\n' + \
            '</script>'
        # replace the source static file
        with open(target_file, 'r', encoding='UTF-8-sig') as file:
            text = file.read() \
                .replace("'story_content/user.js'",
                         '"{% static \'chiron/' + lesson_folder + '/story_content/user.js\' %}"') \
                .replace('"story_content/user.js"',
                         '"{% static \'chiron/' + lesson_folder + '/story_content/user.js\' %}"') \
                .replace('"html5/data/css/output.min.css"',
                         '"{% static \'chiron/' + lesson_folder + '/html5/data/css/output.min.css\' %}"') \
                .replace("'html5/data/css/output.min.css'",
                         '"{% static \'chiron/' + lesson_folder + '/html5/data/css/output.min.css\' %}"') \
                .replace("DATA_PATH_BASE: '',",
                         "DATA_PATH_BASE: '/static/chiron/" + lesson_folder +
                         "/',\n" + "      LIB_PATH_BASE: '/static/chiron/',") \
                .replace('<script src="html5/lib/scripts/bootstrapper.min.js"></script>',
                         bootstrapper_replacement) \
                .replace("<script src='html5/lib/scripts/bootstrapper.min.js'></script>",
                         bootstrapper_replacement) \
                .replace('<!-- Created using Storyline 3 - http://www.articulate.com  -->',
                         '<!-- Created using Storyline 360 - http://www.articulate.com  -->') \
                .replace("features: '',", "features: 'AccessibleVideo,ConnectionMessages,FullScreenToggle,"
                                          "InsertSvgPicture,LayerPresentAsDialog,MultipleQuizTracking,"
                                          "PlayerSpeedControl,UpdatedThemeEditor,UseAudioElement',") \
                .replace("themeName: 'classic',", "themeName: 'unified',") \
                .replace("preloaderColor: '#FFFFFF',", "preloaderColor: '#8C8C8C',") \
                .replace("productChannel: 'perpetual',", "productChannel: 'stable',") \
                .replace("aid: '',", "aid: 'aid|f1171579-8d22-4aee-85e6-84a58c8ed8b5',") \
                .replace("playerVersion: '3.20.30234.0',", "playerVersion: '3.72.29699.0',") \
                .replace("connectionSettings: { },",
                         "connectionSettings: { message: 'You%20are%20offline.%20Trying%20to%20reconnect...', "
                         "useDarkTheme: true },") \
                .replace('<body style="background: #FFFFFF" class="cs-HTML theme-classic">',
                         '<body style="background: #FFFFFF" class="cs-HTML theme-unified">') \
                .replace("if (window.globals.deviceView.isMobile) { var doc = document, loader = "
                         "doc.body.querySelector('.slide-loader'); [ 1, 2, 3 ].forEach(function(n) "
                         "{ var d = doc.createElement('div'); d.style.backgroundColor = "
                         "window.globals.preloaderColor; d.classList.add('mobile-loader-dot'); "
                         "d.classList.add('dot' + n); loader.appendChild(d); }); }",
                         "var doc = document, loader = doc.body.querySelector('.slide-loader'); "
                         "[ 1, 2, 3 ].forEach(function(n) { var d = doc.createElement('div'); "
                         "d.style.backgroundColor = window.globals.preloaderColor; "
                         "d.classList.add('mobile-loader-dot'); d.classList.add('dot' + n); "
                         "loader.appendChild(d); });")
        title = re.search('<title>.*</title>', text)
        if title:
            title_replacement = title[0] + '\n' + \
                '  <link rel="icon" href="{% static \'main/favicon.png\' %}"/>'
            text = text.replace(title[0], title_replacement)
        text = re.sub(r'<!-- version: [\d.]+ -->', '<!-- version: 3.72.29699.0 -->', text)
        text = re.sub(r"cid: '[0-9a-z\-]+',", r"cid: '7a559957-a366-4604-80b5-9199c79e3720',", text)
        text = "{% load static %}\n\n" + text
        with open(target_file, 'w', encoding='utf8') as file:
            file.write(text)
        print('Completed.')
    except Exception as e:
        print('Exception: {}'.format(e))


if __name__ == "__main__":
    main(sys.argv[1:])
