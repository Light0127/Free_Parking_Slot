from flask import Flask, json,redirect,render_template,flash,request
from flask.globals import request, session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash

from flask_login import login_required,logout_user,login_user,login_manager,LoginManager,current_user

from flask_mail import Mail
import json

# mydatabase connection
local_server=True
app=Flask(__name__)
app.secret_key="bhuvan"

with open('config.json','r') as c:
    params=json.load(c)["params"]

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

#this is for getting the unique user access
login_manager = LoginManager(app)
login_manager.login_view='login'

# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/databsename'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/parking_slots'
db=SQLAlchemy(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id) or Parkinguser.query.get(user_id)

class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(15))
    email=db.Column(db.String(50))
    phone=db.Column(db.String(13),unique=True)
    password=db.Column(db.String(1000))
    
class Parkinguser(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    pcode=db.Column(db.String(20),unique=True)
    email=db.Column(db.String(50))
    password=db.Column(db.String(1000))

class padata(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    pcode=db.Column(db.String(20),unique=True)
    pname=db.Column(db.String(100))
    fwslots=db.Column(db.Integer)
    twslots=db.Column(db.Integer)
    
class parking(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    vehnum=db.Column(db.String(20),unique=True)
    ptype=db.Column(db.String(20))
    pcode=db.Column(db.String(20))
    name=db.Column(db.String(50))
    phone=db.Column(db.String(12))      

@app.route("/")
def home():
   
    return render_template("index.html")

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=="POST":
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone_no')
        password=request.form.get('password')
        #print(name,email,phone, password)
        encpassword=generate_password_hash(password)
        userph=User.query.filter_by(phone=phone).first()
        usermail=User.query.filter_by(email=email).first()
        if usermail or userph:
            flash("Email or Phone number is already present","warning")
            return render_template("usersignup.html")
        new_user=db.engine.execute(f"INSERT INTO `user`(`name`,`email`,`phone`,`password`) VALUES ('{name}','{email}','{phone}','{encpassword}') ")
        flash("Successfully Registered, please login","success")
        return render_template("userlogin.html")     
    return render_template("usersignup.html")

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":        
        email=request.form.get('email')       
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")   
    return render_template("userlogin.html")

@app.route('/parkinglogin',methods=['POST','GET'])
def parkinglogin():
    if request.method=="POST":        
        email=request.form.get('email')       
        password=request.form.get('password')
        user=Parkinguser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("parkinglogin.html") 
    return render_template("parkinglogin.html")

@app.route('/admin',methods=['POST','GET'])
def admin():
    if request.method=="POST":        
        username=request.form.get('username')       
        password=request.form.get('password')
        if(username==params['user'] and password==params['password']):
            session['user']=username
            return render_template("addpsuser.html")
        else:
            flash("Invalid Credentials","danger")
    return render_template("admin.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful","warning")
    return redirect(url_for('login'))

@app.route('/addparkinguser',methods=['POST','GET'])
def parkinguser():
    if('user' in session and session['user']==params['user']):       
        if request.method=="POST":
            pcode=request.form.get('pcode')
            email=request.form.get('email')
            password=request.form.get('password')
            encpassword=generate_password_hash(password)
            pcode=pcode.upper()
            usermail=Parkinguser.query.filter_by(email=email).first()
            if usermail:
                flash("Email is already present","warning")        
            db.engine.execute(f"INSERT INTO `parkinguser`(`pcode`,`email`,`password`) VALUES ('{pcode}','{email}','{encpassword}')")       
            mail.send_message('SKIE PARKING',sender=params['gmail-user'],recipients=[email],body=f"Welcome, thanks for choosing us\nYour Login Credentials Are:\n\n\tEmail Address: {email}\n\n\tPassword: {password}\n\n\tParking Code: {pcode}\n\n Do not share your password\n\n\nThank You..." )
            flash("Data Sent and Inserted Successfully","warning")
            return render_template("addpsuser.html")       
    else:
        flash("Login and try again",'warning')
        return render_template("addpsuser.html")

@app.route('/logoutadmin')
def logoutadmin(): 
    session.pop('user')
    flash("Logout Successful","warning")
    return redirect('/admin')

@app.route('/addpainfo',methods=['POST','GET'])
def addpainfo():
    email=current_user.email
    posts=Parkinguser.query.filter_by(email=email).first()
    code=posts.pcode
    postsdata=padata.query.filter_by(pcode=code).first()
    if request.method=="POST":
        pcode=request.form.get('pcode')
        pname=request.form.get('pname')
        fwslots=request.form.get('fwslots')
        twslots=request.form.get('twslots')
        pcode=pcode.upper()
        puser=Parkinguser.query.filter_by(pcode=pcode).first()
        pduser=padata.query.filter_by(pcode=pcode).first()
        if pduser:
            flash("Parking Area alread added. Update opotion available","primary")
            return render_template("parkingareadata.html",postsdata=postsdata)
        if puser:            
            db.engine.execute(f"INSERT INTO `padata` (`pcode`,`pname`,`fwslots`,`twslots`) VALUES ('{pcode}','{pname}','{fwslots}','{twslots}')")
            flash("Data is added","primary")  
        else:
            flash("Parking Code does not Exist","warning")    
    return render_template("parkingareadata.html",postsdata=postsdata)

#TESTING
@app.route("/test")
def test():
    try:
        a=Test.query.all()
        print(a)
        return 'My database is connected'
    except Exception as e:
        print(e)
        return f'Not connected {e}'
    
@app.route("/hedit/<string:id>",methods=['POST','GET'])
@login_required
def hedit(id):
    posts=padata.query.filter_by(id=id).first()
  
    if request.method=="POST":
        pcode=request.form.get('pcode')
        pname=request.form.get('pname')
        fwslots=request.form.get('fwslots')
        twslots=request.form.get('twslots')
        pcode=pcode.upper()
        db.engine.execute(f"UPDATE `padata` SET `pcode` ='{pcode}',`pname`='{pname}',`fwslots`='{fwslots}',`twslots`='{twslots}' WHERE `padata`.`id`={id}")
        flash("Slot Updated","info")
        return redirect("/addpainfo")

    # posts=Hospitaldata.query.filter_by(id=id).first()
    return render_template("hedit.html",posts=posts)

@app.route("/hdelete/<string:id>",methods=['POST','GET'])
@login_required
def hdelete(id):
    db.engine.execute(f"DELETE FROM `padata` WHERE `padata`.`id`={id}")
    flash("Data Deleted","danger")
    return redirect("/addpainfo")

@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query=db.engine.execute(f"SELECT * FROM `padata` ")
    if request.method=="POST":
        name=request.form.get('name')
        ptype=request.form.get('ptype')
        pcode=request.form.get('pcode')
        vehnum=request.form.get('vehnum')
        phone=request.form.get('phone')  
        check2=padata.query.filter_by(pcode=pcode).first()
        if not check2:
            flash("Parking Code not exist","warning")
            return render_template("booking.html",query=query)
        
        check3=parking.query.filter_by(vehnum=vehnum).first()
        if check3:
            flash("A Slot is already booked for your vehicle","warning")
            return render_template("booking.html")

        code=pcode
        dbb=db.engine.execute(f"SELECT * FROM `padata` WHERE `padata`.`pcode`='{code}' ")        
        ptype=ptype
        if ptype=="twslots":       
            for d in dbb:
                seat=d.twslots
                print(seat)
                ar=padata.query.filter_by(pcode=code).first()
                ar.twslots=seat-1
                db.session.commit()

        elif ptype=="fwslots":      
            for d in dbb:
                seat=d.fwslots
                print(seat)
                ar=padata.query.filter_by(pcode=code).first()
                ar.fwslots=seat-1
                db.session.commit()

        else:
            pass

        check=padata.query.filter_by(pcode=pcode).first()
        if(seat>0 and check):
            res=parking(vehnum=vehnum,ptype=ptype,pcode=pcode,name=name,phone=phone)
            db.session.add(res)
            db.session.commit()
            flash("Slot is Booked, Happy Parking XD","success")
        else:
            flash("Something Went Wrong","danger")
    return render_template("booking.html",query=query)

@app.route("/avail",methods=['GET'])
def avail():
    query=db.engine.execute(f"SELECT * FROM `padata` ")
    return render_template("avail.html",query=query)    
    
    
    
app.run(debug=True)