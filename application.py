import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory,send_file,flash
from werkzeug.utils import secure_filename
import shutil
import uuid

import process_data as prodata
# Initialize the Flask application
app = Flask(__name__)

# This is the path to the templates directory
app.config['CMDB_FOLDER'] = 'CMDB_templates/'
#
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['xlsx','xls'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/', methods=['GET', 'POST'])
def comp():
	msg= None
	if request.method == 'POST':
		company = request.form['company']
		#if os.path.exists(company):
		#	msg='Already in use or someone forgot to clean the data!'
		#else:
		id_folder=company + '_' + str(uuid.uuid1())
		#os.makedirs(company)
		#app.config['COMPANY_NAME_FOLDER'] = company
		msg = 'Successful!'
		#id_folder=str(uuid.uuid1())
		os.makedirs(id_folder)
		os.makedirs(id_folder + '/ITSM_sites')
		os.makedirs(id_folder +'/Report')
		os.makedirs(id_folder + '/File_to_validate')
		app.config['COMPANY_FOLDER'] = id_folder
		app.config['UPLOAD_FOLDER'] = id_folder + '/File_to_validate/'
		app.config['DOWNLOAD_FOLDER'] = id_folder + '/Report/'
		app.config['ITSM_FOLDER'] = id_folder + '/ITSM_sites/'
	return render_template('index_company.html',msg=msg)



@app.route('/return-file/')
def return_file():
	filename='cmdb_templates.zip'
	return send_file(os.path.join(app.config['CMDB_FOLDER'])+filename,attachment_filename=filename, as_attachment=True)


@app.route('/')
def file_downloads():
	return render_template('index_company.html')


@app.route('/files', methods=['GET','POST'])
def index():
	msg=None
	if request.method == 'POST':
		if 'file' not in request.files:
			print('No file attached in request')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			print('No file selected')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['ITSM_FOLDER'], filename))
			msg=filename
		else:
			msg='Please select a valid extension (.xls or .xlsx)'
	return render_template('multi_upload_index.html',msg=msg)


# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
	msg2=None
	# Get the name of the uploaded files
	uploaded_files = request.files.getlist("file[]")
	for file in uploaded_files:
		# Check if the file is one of the allowed types/extensions
		if file and allowed_file(file.filename):
			# Make the filename safe, remove unsupported chars
			filename = secure_filename(file.filename)
			# Move the file form the temporal folder to the upload
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			msg2='blabla'
		else:
			msg2='Please select a valid extension (.xls or .xlsx)'
			return render_template('multi_upload_index.html',msg2=msg2)
	if len(os.listdir(app.config['UPLOAD_FOLDER']))>0:
		prodata.process_file(path=os.path.join(app.config['UPLOAD_FOLDER']),company=app.config['COMPANY_FOLDER'].split('_')[0],report=os.path.join(app.config['DOWNLOAD_FOLDER']),history=os.path.join(app.config['ITSM_FOLDER']))
		filenames=os.listdir(app.config['DOWNLOAD_FOLDER'])

		text = open(app.config['DOWNLOAD_FOLDER']+'/issues.txt', 'r+',encoding='utf8')
		content = text.read()
		text.close()
		#shutil.rmtree(app.config['COMPANY_NAME_FOLDER'])
	# Redirect the user to the uploaded_file route, which
	# will basicaly show on the browser the uploaded file
	# Load an html page with a link to each uploaded file

	return render_template('multi_files_upload.html', filenames=filenames,text=content,msg2=msg2)



# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/Report/<filename>')
def uploaded_file(filename):
	return send_from_directory(app.config['DOWNLOAD_FOLDER'],filename)

@app.route("/refresh/", methods=['POST'])
def refresh():
	#if os.path.exists(app.config['COMPANY_NAME_FOLDER']):
	#	print('bla')
	#	shutil.rmtree(app.config['COMPANY_NAME_FOLDER'])
	#else:
	#	print('bla2')
	if os.path.exists(app.config['COMPANY_FOLDER']):
		shutil.rmtree(app.config['COMPANY_FOLDER'])

	#Moving forward code
	#forward_message = "Moving Forward..."
	return render_template('refresh.html')#, message=forward_message);

if __name__ == '__main__':
	#port = int(os.environ.get("PORT", 5000))
	#app.run(host='10.12.31.98', port=port)
	#app.run(host='0.0.0.0', port=port)
	#app.run(threaded=True,debug=True)
	app.run(debug=True)