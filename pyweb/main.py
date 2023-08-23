from datetime import datetime
from flask import Flask,render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
from flask_mail import Mail
import os.path
import os

with open('config.json', 'r') as c:
    params = json.load(c)["params"]


# scriptpath = os.path.dirname(__file__)
# filename = os.path.join(scriptpath, 'config.json')
# c=open(filename)
# # c= open('config.json','r')
# params = json.load(c)["params"]
# c.close()

local_server = True

app = Flask(__name__) # creation of Flask class object
app.secret_key = 'super-secret-key' # diving secret key


app.config['UPLOAD_FOLDER'] = params['upload_loc'] 

# Notification satup with email for contact page.
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']

)

mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

#for database connection.
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/contact'

db = SQLAlchemy(app) #Obj creation of SQLalchemy

# Assigning var for CONTACT US page.
class Contactus(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    mo_no = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    sub_head = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    # email = db.Column(db.String(20), nullable=False)

@app.route("/home")
def home():
    posts = Posts.query.filter_by().all()
    return render_template("index.html",params=params,posts=posts)


@app.route("/about")
def about():
    return render_template("about.html",params=params)

@app.route("/dashboard", methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']) : 
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)
    

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass== params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html",params=params,posts = posts)
    
    return render_template("login.html",params=params)




# USER LOGIN 
@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']) :
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle =  request.form.get('sub_title')
            slug =  request.form.get('slug')
            content =  request.form.get('content')
            img_file = request.form.get('img_file')
            date =datetime.now()
            if sno == '0':
                post = Posts(title = box_title,sub_head=subtitle,slug=slug,content=content,img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.subtitle = subtitle
                post.img_file = img_file
                post.date = date
                db.session.commit()
            return redirect('/edit/'+sno)
                
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("Edit.html",params=params,post=post)


# File Uploader 
@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']) :
        if request.method == 'POST':
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "UPLOADED SUCCESFULLY"


# TO LOGOUT session
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

#To dalete post 
@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']) :
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


# Contact form backend
@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contactus(name=name, mo_no = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New msg from ' + name, 
                          sender=email,
                          recipients=[params['gmail-user']],
                          body = message + "\n" + phone 
                          )
    return render_template("contact.html",params=params)

# To switch between posts
@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)


app.run(debug=True)
