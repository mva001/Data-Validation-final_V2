import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory,send_file,flash
from werkzeug.utils import secure_filename
import shutil
import uuid
import datetime as dt 
from datetime import datetime
import process_data as prodata

# Initialize the Flask applicationlication
#project_root = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.abspath(__file__))

# Im not sure should be application/templates or app/templates or just templates 
template_path = os.path.join(project_root, 'templates')
application = Flask(__name__, template_folder=template_path)

# This is the path to the templates directory
application.config['CMDB_FOLDER'] = project_root+ '/'+ 'CMDB_templates/'
#
# These are the extension that we are accepting to be uploaded
application.config['ALLOWED_EXTENSIONS'] = set(['xlsx','xls'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1] in application.config['ALLOWED_EXTENSIONS']


@application.route('/', methods=['GET', 'POST'])
def comp():
	data=[s for s in os.listdir(os.getcwd()) if len(s) > 20]
	paths_to_del=[]
	dates=[]
	for i in range(len(data)):
		paths_to_del.append(os.getcwd()+ '/' + data[i])
		dates.append((dt.datetime.now()-datetime.fromtimestamp(os.path.getctime(paths_to_del[i]))).seconds)
		if dates[i]>100:
			shutil.rmtree(paths_to_del[i])
		else:
			None
	msg= None
	if request.method == 'POST':
		company = request.form['company']
		if os.path.exists(company):
			msg='Already in use or someone forgot to clean the data!'
		else:
			id_folder=company + '_' + str(uuid.uuid1())
			os.makedirs(id_folder)
			os.makedirs(id_folder + '/ITSM_sites')
			os.makedirs(id_folder +'/Report')
			os.makedirs(id_folder + '/File_to_validate')
			application.config['COMPANY_FOLDER'] = project_root+ '/' + id_folder
			application.config['UPLOAD_FOLDER'] = project_root+'/' + id_folder + '/File_to_validate/'
			application.config['DOWNLOAD_FOLDER'] = project_root+'/' + id_folder + '/Report/'
			application.config['ITSM_FOLDER'] = project_root+'/' + id_folder + '/ITSM_sites/'
			msg = [
			application.config['COMPANY_FOLDER'],
			application.config['UPLOAD_FOLDER'],
			application.config['DOWNLOAD_FOLDER'],
			application.config['ITSM_FOLDER']]

	return render_template('index_company.html',msg=msg)



@application.route('/return-file/')
def return_file():
	filename='cmdb_templates.zip'
	return send_file(os.path.join(application.config['CMDB_FOLDER'])+filename,attachment_filename=filename, as_attachment=True)


@application.route('/')
def file_downloads():
	return render_template('index_company.html')


@application.route('/files', methods=['GET','POST'])
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
			print(os.path.join(application.config['ITSM_FOLDER']))
			file.save(os.path.join(application.config['ITSM_FOLDER'], filename))
			msg=filename
		else:
			msg='Please select a valid extension (.xls or .xlsx)'
	return render_template('multi_upload_index.html',msg=msg)


# Route that will process the file upload
@application.route('/upload', methods=['GET','POST'])
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
			file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
		else:
			msg2='Please select a valid extension (.xls or .xlsx)'
			return render_template('multi_upload_index.html',msg2=msg2)
	if len(os.listdir(application.config['UPLOAD_FOLDER']))>0:
		prodata.process_file(path=os.path.join(application.config['UPLOAD_FOLDER']),company=application.config['COMPANY_FOLDER'].split('/')[-1].split('_')[0],report=os.path.join(application.config['DOWNLOAD_FOLDER']),history=os.path.join(application.config['ITSM_FOLDER']))
		filenames=os.listdir(application.config['DOWNLOAD_FOLDER'])
		text = open(application.config['DOWNLOAD_FOLDER']+'/issues.txt', 'r+',encoding='utf8')
		content = text.read()
		text.close()
		#shutil.rmtree(application.config['COMPANY_NAME_FOLDER'])
	# Redirect the user to the uploaded_file route, which
	# will basicaly show on the browser the uploaded file
	# Load an html page with a link to each uploaded file

	return render_template('multi_files_upload.html', filenames=filenames,text=content,msg2=msg2)

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@application.route('/Report/<filename>')
def uploaded_file(filename):
	return send_from_directory(application.config['DOWNLOAD_FOLDER'],filename)

@application.route("/refresh/", methods=['POST'])
def refresh():
	if os.path.exists(application.config['COMPANY_FOLDER']):
		shutil.rmtree(application.config['COMPANY_FOLDER'])

	#Moving forward code
	#forward_message = "Moving Forward..."
	return render_template('refresh.html')#, message=forward_message);




if __name__ == '__main__':
	#port = int(os.environ.get("PORT", 5000))
	#application.run(host='10.12.31.98', port=port)
	#application.run(host='0.0.0.0', port=port)
	#application.run(threaded=True,debug=True)
	application.run(debug=True)
