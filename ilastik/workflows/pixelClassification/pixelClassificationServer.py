def start_pc_server(workflow, port):
    import os
    import tempfile
    from flask import Flask, request, redirect, url_for, send_from_directory
    from werkzeug import secure_filename

    UPLOAD_FOLDER = tempfile.mkdtemp()
    pc_app = Flask(__name__)
    pc_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @pc_app.route("/", methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(pc_app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('process', filename=filename))
        else:
            from jinja2 import Environment, FileSystemLoader
            template_dir = os.path.split(__file__)[0]
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template('submit-data.html')
            project_name = os.path.split(workflow.shell.projectManager.currentProjectPath)[1]
            return template.render(url_for=url_for, project_name=project_name)

    @pc_app.route('/process/<filename>')
    def process(filename):
        filepath = pc_app.config['UPLOAD_FOLDER'] + '/' + filename
        filepath = str(filepath)
        
        parsed_batch_args, unused_args = workflow.batchProcessingApplet.parse_known_cmdline_args( [filepath] )
        output_paths = workflow.batchProcessingApplet.run_export_from_parsed_args(parsed_batch_args)
        assert len(output_paths) == 1
        return send_from_directory(*os.path.split(output_paths[0]))

    pc_app.run(host='0.0.0.0', port=port)
