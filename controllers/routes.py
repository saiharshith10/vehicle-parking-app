from flask import render_template,request,redirect,url_for
from app import app
from controllers.models import User,parking_lot


@app.route('/',methods=['GET','POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, passhash=password).first()
        if user:
            if user.is_admin:
                return redirect(url_for('admin_dashboard', username=user.username))
            else:
                return redirect(url_for('user_dashboard', username=user.username))
        else:
            return render_template('register.html')
    return render_template('index.html')


@app.route('/register')
def register():
    return render_template('register.html')
@app.route('/login')
def login():
    return render_template('index.html')
@app.route('/admin_dashboard/<username>')
def admin_dashboard(username):
    return render_template('admin_dashboard.html', username=username)
@app.route('/user_dashboard/<username>')
def user_dashboard(username):
    parking_lots = parking_lot.query.all()
    return render_template('user_dashboard.html', username=username, parking_lots=parking_lots)


