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
              flash('User not found!','danger')
              return redirect(url_for('register'))
         
         if user.passhash!=password:
              flash('Incorrect password!','danger')
              return redirect(url_for('login'))
         
         session['username'] = user.username
         session['is_admin'] = user.is_admin

         if user.username == 'admin' and user.is_admin == True:
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
        if len(password) < 8:
            flash('Password must be at least 8 characters long!','danger')
            return redirect(url_for('register'))
        if existing_user:
             flash('Username already exists!','danger')
             return redirect(url_for('register'))
        if username == 'admin':
            flash('Username cannot be "admin"!','danger')
            return redirect(url_for('register'))
        if username != 'admin':
            new_user = User(username=username, email = email,passhash=password, name=name, address=address, pincode=pincode)
            db.session.add(new_user)
            db.session.commit()
        return redirect(url_for('login'))
        
@app.route('/logout')
def logout():
     session.pop('username', None)
     session.clear() 
     flash('You have been logged out successfully!','success')
     return redirect(url_for('login'))

 
@app.route('/edit_profile',methods=['GET', 'POST'])
def edit_profile():
    if request.method=='GET':
        if 'username' not in session:
            flash('You need to login first!','warning')
            return redirect(url_for('login'))
        
        return render_template('edit_profile.html')
    if request.method == 'POST':
        old_username = request.form.get('username')
        old_password = request.form.get('password')
        user = User.query.filter_by(username=old_username).first()
        if not user:
            flash('User not found!','danger')
            return redirect(url_for('edit_profile'))
        if user.passhash != old_password:
            flash('Incorrect password!','danger')
            return redirect(url_for('edit_profile'))
        #this is updating the profile
        user.username = request.form.get('new_username')
        user.password = request.form.get('new_password')  # Note: hash this in production!
        session['username'] = user.username  # Update session
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('edit_profile.html')


@app.route('/add_lot', methods=['POST'])
def add_lot():
    if 'username' not in session or not session.get('is_admin'):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('login'))

    # Get form fields
    location_name = request.form.get('location_name')
    max_spots = request.form.get('max_spots')
    price = request.form.get('price')
    address = request.form.get('address')
    pincode = request.form.get('pincode')

    # Validation
    if not location_name or not max_spots or not price or not address or not pincode:
        flash('All fields are required!', 'error')
        return redirect(url_for('admin_dashboard'))

    if not max_spots.isdigit() or not price.replace('.', '', 1).isdigit():
        flash('Max spots and price must be valid numbers!', 'error')
        return redirect(url_for('admin_dashboard'))

    if int(max_spots) <= 0 or float(price) <= 0:
        flash('Max spots and price must be greater than zero!', 'error')
        return redirect(url_for('admin_dashboard'))

    # Add new parking lot
    new_lot = parking_lot(
        location_name=location_name,
        max_spots=int(max_spots),
        available_spots=int(max_spots),
        price=float(price),
        address=address,
        pincode=pincode
    )
    db.session.add(new_lot)
    db.session.commit()

    # Add spots to the lot
    for _ in range(new_lot.max_spots):
        new_spot = parking_spot(
            parking_lot_id=new_lot.id,
            status="available"
        )
        db.session.add(new_spot)

    db.session.commit()

    flash(f"{location_name} created with {new_lot.max_spots} spots!", "success")
    return redirect(url_for('admin_dashboard'))



@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or not session.get('is_admin'):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('login'))

    lots = parking_lot.query.all()
    # for lot in lots:
    #     lot.spots = parking_spot.query.filter_by(parking_lot_id=lot.id).all()

    return render_template('admin_dashboard.html', parking_lots=lots)


@app.route('/edit_parking_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_parking_lot(lot_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('login'))

    lot = parking_lot.query.get_or_404(lot_id)

    if request.method == 'POST':
        lot.location_name = request.form.get('location_name')
        lot.price = float(request.form.get('price'))
        lot.address = request.form.get('address')
        lot.pincode = request.form.get('pincode')

        # Correct field name from form
        new_max_spots = int(request.form.get('max_spots'))
        current_max_spots = lot.max_spots

        # Count occupied spots
        occupied_count = sum(1 for s in lot.spots if s.status == 'occupied')
        available_spots = [s for s in lot.spots if s.status == 'available']

        # CASE 1: Increase spots
        if new_max_spots > current_max_spots:
            to_add = new_max_spots - current_max_spots
            for _ in range(to_add):
                new_spot = parking_spot(status='available', parking_lot_id=lot.id)
                db.session.add(new_spot)

        # CASE 2: Decrease spots
        elif new_max_spots < current_max_spots:
            to_remove = current_max_spots - new_max_spots

            if occupied_count > new_max_spots:
                flash("Cannot reduce max spots below number of occupied spots!", 'danger')
                return redirect(url_for('admin_dashboard'))

            if len(available_spots) < to_remove:
                flash("Not enough available spots to delete.", 'danger')
                return redirect(url_for('admin_dashboard'))

            # Remove available spots
            for spot in available_spots[:to_remove]:
                db.session.delete(spot)

        # Update max_spots in the lot
        lot.max_spots = new_max_spots
        db.session.commit()

        flash(f"{lot.location_name} updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_parking_lot.html', lot=lot)


@app.route('/delete_parking_lot/<int:lot_id>', methods=['GET','POST'])
def delete_parking_lot(lot_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('login'))

    lot = parking_lot.query.get_or_404(lot_id)

    if request.method == 'POST':
        db.session.delete(lot)
        db.session.commit()
        flash(f"{lot.location_name} deleted successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('delete_parking_lot.html', lot=lot)

@app.route('/admin_users')
def admin_users():
    user = User.query.all()
    return render_template('admin_users.html',User=user)

@app.route('/edit_profile_users')
def edit_profile_users():
    return render_template('edit_profile_users.html')

# @app.route('/details_spot/<int:spot_id>', methods=['GET'])
# def details_spot(spot_id):
# #     if 'username' not in session:
# #         flash('You need to login first!', 'warning')
# #         return redirect(url_for('login'))

# #     spot = parking_spot.query.get_or_404(spot_id)
# #     User=User.query.filter_by(username=session['username']).first()
#     render_template('details_spot.html')
            

@app.route('/user_dashboard',methods=['GET'])
def user_dashboard():
    return render_template('user_dashboard.html',lots=parking_lot.query.all())

@app.route('/book', methods=['GET', 'POST'])
def book():
    return render_template('book.html')


@app.route('/search_parking_lots', methods=['GET','POST'])
def search_parking_lots():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        if not search_query:
            flash('Search query cannot be empty!', 'error')
            return redirect(url_for('admin_dashboard'))

        # Search for parking lots by location name
        results = parking_lot.query.filter(parking_lot.address.ilike(f'%{search_query}%')).all()
        #here i am using the sql like(clause) -> as ilike
        if not results:
            flash('No parking lots found for the given location name.', 'info')
            return redirect(url_for('admin_dashboard'))

        return render_template('admin_search_results.html', results=results)

    return redirect(url_for('admin_dashboard'))

@app.route('/spot_details/<int:lot_id>/<int:spot_id>', methods=['GET'])
def spot_details(lot_id, spot_id):  
    lot = parking_lot.query.get_or_404(lot_id)
    spot = next((s for s in lot.spots if s.id == spot_id), None)
    if spot is None:
        flash('Spot not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    return render_template('spot_details.html', lot=lot, spot=spot)


@app.route('/delete_spot/<int:lot_id>/<int:spot_id>', methods=['POST'])
def delete_spot(lot_id, spot_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('login'))

    lot = parking_lot.query.get_or_404(lot_id)
    spot = next((s for s in lot.spots if s.id == spot_id), None)

    if spot is None:
        flash('Spot not found!', 'danger')
        return redirect(url_for('admin_dashboard'))

    if spot.status == 'occupied':
        flash('Cannot delete an occupied spot!', 'danger')
        return redirect(url_for('spot_details', lot_id=lot.id, spot_id=spot.id))

    db.session.delete(spot)
    lot.max_spots -= 1
    lot.available_spots -= 1
    db.session.commit()
    flash(f'Spot {spot.id} deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))