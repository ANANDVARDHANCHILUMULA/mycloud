from flask import (
    Flask,
    abort,
    render_template, 
    request,
    redirect,
    session
)    
import pymongo
from flask_pymongo import PyMongo
import json
from cfg import config
from hashlib import sha256
from utils import get_random_string
from datetime import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = config['mongo_uri']
app.config["UPLOAD_FOLDER"] = 'C/work/mycloud/uploads'
app.secret_key=b'afckaglsyp^^&*))&$&'
mongo = PyMongo(app)
############## INDEX PAGE ########################
@app.route('/')
def show_index():
    if not 'userToken' in session :
        session['error']='You must login to access this page.'
        return redirect('/login')

    #validate usertoken
    token_document =mongo.db.user_tokens.find_one({
        'sessionHash': session['userToken'],
    })

    if token_document is None :
        session.pop('userToken', None)
        session['error']='You must login again to access this page.'
        return redirect('/login')
    #return 'This is my secure Homepage'
    
    error=''
    if 'error' in session:
        error=session['error']
        session.pop('error', None)

    userId=token_document['userId']
    user = mongo.db.users.find_one({
        '_id':userId
    })
    uploaded_files=mongo.db.files.find({
        'userId':userId,
        'isActive':True
    }).sort([("createdAt", pymongo.DESCENDING)])

    return render_template(
        'files.html',
        uploaded_files=uploaded_files,
        user=user,
        error=error
    ) 

#####################    LOGIN PAGE    #############################
@app.route('/login')
def show_login():
    error=''
    if 'error' in session:
        error=session['error']
        session.pop('error', None)

    signupSuccess=''
    if 'signupSuccess' in session:
        signupSuccess=session['signupSuccess']
        session.pop('signupSuccess',None)

    return render_template('login.html', signupSuccess = signupSuccess, error=error)

##################  SIGNUP PAGE        ##############################################    
@app.route('/signup')
def show_signup():
    error=''
    if 'error' in session:
        error=session['error']
        session.pop('error', None)
    return render_template('signup.html', error=error)

####################     CHECK LOGIN        ########################################
@app.route('/check_login', methods=['POST'])
def checklogin():
    
    try :
        email = request.form['email5']
    except KeyError:
        email = ''

    try :        
        password = request.form['password5']
    except KeyError:
        password =''

    #check if email is blank
    if not len(email) > 0 :
        session['error']='Email is required'
        return redirect('/login')
   
    # check if pw is blank
    if not len(password) > 0:
        session['error']='Password is required'
        return redirect('/login')

    # find email in db
    user_document = mongo.db.users.find_one({"email":email})
    if user_document is None :
        # if document is not present
        session['error']='No account exists with this email address'
        return redirect('/login')

    # verify pw hash matches with original
    password_hash= sha256(password.encode('utf-8')).hexdigest()
    if user_document['password'] != password_hash :
        session['error']='your password is wrong'
        return redirect('/login')

    #  Generate token and save it in session    
    random_string = get_random_string()
    randomSessionHash = sha256(random_string.encode('utf-8')).hexdigest()
    token_object =mongo.db.user_tokens.insert_one({
        'userId' : user_document['_id'],
        'sessionHash': randomSessionHash,
        'createdAt': datetime.utcnow(),
    })
    session['userToken']= randomSessionHash
          

    # redirect to index page
    return redirect('/')  
     


############## HANDLE SIGNUP  #################################
@app.route('/handle_signup', methods=['POST'])
def handlesignup():
    try :
        email = request.form['email5']
    except KeyError:
        email = ''

    try :        
        password = request.form['password5']
    except KeyError:
        password =''

    # checking if email is blank
    if not len(email) > 0 :
        session['error']='Email is required'
        return redirect('/signup')

    # checking if email is valid
    if not '@' in email or not '.' in email :
        session['error']='Email is invalid'
        return redirect('/signup')    

    #checking if password is blank
    if not len(password) > 0:
        session['error']='Password is required'
        return redirect('/signup')

    #checking if email already exists
    matching_user_count = mongo.db.users.count_documents({"email":email})
    if matching_user_count > 0:
        session['error']='Email already exists'
        return redirect('/signup')

    password= sha256(password.encode('utf-8')).hexdigest()

    # user record
    result=mongo.db.users.insert_one({
        'email' : email,
        'password':password,
        'name':'',
        'lastLoginDate': None,
        'createdAt': datetime.utcnow(),
        'updateAt': datetime.utcnow(),
    })
        
    session['signupSuccess'] ='Your account is ready. You can Login now!'
    return redirect('/login')    

@app.route('/logout')
def logout_user():
    session.pop('userToken', None)
    session['signupSuccess'] ='You are logged out.'
    return redirect('/login')

def allowed_file(filename):
    ALLOWED_EXTENSIONS=['jpg','jpeg','gif','png','doc','docx','xls','xlsx','ppt','pptx','pdf','csv']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/handle_file_upload', methods=['POST'])
def handle_file_upload():
    if 'uploadedFile' not in request.files:
        session['error']="no file uploaded"
        return redirect('/')
    file=request.files['uploadedFile']    
    print('i have got the file')
    print(file)

    if file.filename == '': 
        session['error']='No selected file'
        return redirect('/')

    if not allowed_file(file.filename):
        session['error']='file type not allowed'
        return redirect('/')

    #TODO file size check

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return "file upload is not handled yet"