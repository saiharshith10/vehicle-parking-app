from flask import render_template,request,redirect,url_for,session
from app import app
from controllers.models import db, User, parking_lot,parking_spot,reserve_parking_spot
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
         username = request.form.get('username')
         password = request.form.get('password')
         if not username or not password:
            flash('All fields are required!','error')
            return redirect(url_for('login'))
         user = User.query.filter_by(username=username).first()

         if not user:
              flash('User not found!','error')
              return redirect(url_for('register'))
         
         if user.passhash!=password:
              flash('Incorrect password!','error')
              return redirect(url_for('login'))
         
         session['username'] = user.username
         session['is_admin'] = user.is_admin

         if user.username == 'admin':
                return redirect(url_for('admin_dashboard'))
            
         else:
                flash('Login successful!','success')
                return redirect(url_for('user_dashboard'))


@app.route('/register',methods=['POST'])
def register_post():
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('full_name')
        address = request.form.get('Address')
        pincode = request.form.get('Pincode')
        
        if not username or not password or not confirm_password:
           flash('All fields are required!','error')
           return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match! Registration failed.','danger')
            return redirect(url_for('register'))
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
             flash('Username already exists!','error')
             return redirect(url_for('register'))
        if username == 'admin':
            flash('Username cannot be "admin"!')
            return redirect(url_for('register'))
        if username != 'admin':
            new_user = User(username=username, email = email,passhash=password, name=name, address=address, pincode=pincode)
            db.session.add(new_user)
            db.session.commit()
        return redirect(url_for('login'))
        
        
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/user_dashboard')
def user_dashboard():
     return render_template('user_dashboard.html')

@app.route('/logout')
def logout():
     session.pop('username', None)
     flash('You have been logged out successfully!')
     return redirect(url_for('login'))




