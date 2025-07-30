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
         password = (request.form.get('password'))
         if not username or not password:
            flash('All fields are required!','error')
            return redirect(url_for('login'))
         user = User.query.filter_by(username=username).first()
        
         if not user:
              flash('User not found!','danger')
              return redirect(url_for('register'))
         
         if not check_password_hash(user.passhash, password):
              flash('Incorrect password!','danger')
              return redirect(url_for('login'))
         
         
         session['username'] = user.username
         session['is_admin'] = user.is_admin
         session['user_id'] = user.id  # Store user ID in session

         if user.is_admin == True:
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
        if password!= confirm_password:
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
        
        hashed_password = generate_password_hash(password)
        if username != 'admin':
            new_user = User(username=username, email = email,passhash=hashed_password, name=name, address=address, pincode=pincode)
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
        if not check_password_hash(user.passhash, old_password):
            flash('Incorrect password!','danger')
            return redirect(url_for('edit_profile'))
        #this is updating the profile
        user.username = request.form.get('new_username')
        user.passhash = generate_password_hash(request.form.get('new_password'))  # Note: hash this in production!
        session['username'] = user.username  # Update session
        session['password'] = user.passhash
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
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
        parking_spot.query.filter_by(parking_lot_id=lot.id).delete()  # first we have to delete all the spots in the lot
        db.session.delete(lot)
        db.session.commit()
        flash(f"{lot.location_name} deleted successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('delete_parking_lot.html', lot=lot)

@app.route('/admin_users')
def admin_users():
    user = User.query.all()
    return render_template('admin_users.html',User=user)


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

@app.route('/book/<int:lot_id>', methods=['GET', 'POST'])
def book(lot_id):
    if request.method == 'POST':
        spot_id = request.form.get('spot_id')
        # start_time = request.form.get('start_time')
        if not lot_id or not spot_id:
            flash('Lot ID and Spot ID are required!', 'error')
            return redirect(url_for('user_dashboard'))
        lot = parking_lot.query.get_or_404(lot_id)
        spot = next((s for s in lot.spots if s.id == int(spot_id)), None)

        if not spot:
            flash('Spot not found!', 'danger')
            return redirect(url_for('user_dashboard'))

        if spot.status != 'available':
            flash('Spot is not available for booking!', 'warning')
            return redirect(url_for('user_dashboard'))
        

        from datetime import datetime
        start_time_str = request.form['start_time']
        start_time = datetime.fromisoformat(start_time_str)

        # Create a reservation
        reservation = reserve_parking_spot(
            user_id=session['user_id'],  # Assuming username is unique and used as user ID
            parking_spot_id=spot.id,
            start_time=start_time,
            vehicle_number=request.form.get('vehicle_number')
        )
        
        db.session.add(reservation)
        spot.status = 'occupied'
        lot.available_spots -= 1
        db.session.commit()

        flash(f'Spot {spot.id} booked successfully!', 'success')
        
        return redirect(url_for('user_dashboard'))
    #get kosam
    lot = parking_lot.query.get_or_404(lot_id)
    if not lot.spots:
        flash('No spots available for booking!', 'warning')
        return redirect(url_for('user_dashboard'))
    return render_template('book.html',lot=lot)

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
    return render_template('spot_details.html', lot=lot, spot=spot,user=User.name)


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

@app.route('/search_parking_lots_by_location', methods=['GET','POST'])
def search_parking_lots_by_location():

    if request.method == 'POST':
        location_name = request.form.get('location_name')
        if not location_name:
            flash('Search query cannot be empty!', 'error')
            return redirect(url_for('user_dashboard'))

        # Search for parking lots by location name
        results = parking_lot.query.filter(parking_lot.location_name.ilike(f'%{location_name}%')).all()
        #here i am using the sql like(clause) -> as ilike
        if not results:
            flash('No parking lots found for the given location name.', 'info')
            return redirect(url_for('user_dashboard'))

        return render_template('user_search_results.html', results=results)

    return redirect(url_for('user_dashboard'))


@app.route('/search_parking_lots_by_pincode',methods=['GET','POST'])
def search_parking_lots_by_pincode():

    if request.method == 'POST':
        pincode = request.form.get('pincode')
        if not pincode:
            flash('Search query cannot be empty!', 'error')
            return redirect(url_for('user_dashboard'))

        # Search for parking lots by location name
        results = parking_lot.query.filter(parking_lot.pincode.ilike(f'%{pincode}%')).all()
        #here i am using the sql like(clause) -> as ilike
        if not results:
            flash('No parking lots found for the given pincode.', 'info')
            return redirect(url_for('user_dashboard'))

        return render_template('user_search_results.html', results=results)

    return redirect(url_for('user_dashboard'))


@app.route('/search_parking_lots_by_address',methods=['GET','POST'])
def search_parking_lots_by_address():
    if request.method == 'POST':
        address = request.form.get('address')
        if not address:
            flash('Search query cannot be empty!', 'error')
            return redirect(url_for('user_dashboard'))

        # Search for parking lots by location name
        results = parking_lot.query.filter(parking_lot.address.ilike(f'%{address}%')).all()
        #here i am using the sql like(clause) -> as ilike
        if not results:
            flash('No parking lots found for the given address .', 'info')
            return redirect(url_for('user_dashboard'))
        return render_template('user_search_results.html', results=results)

    return redirect(url_for('user_dashboard'))


@app.route('/bookings', methods=['GET'])
def bookings():
    if 'username' not in session:
        flash('You need to login first!', 'warning')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash('User ID not found in session!', 'danger')
        return redirect(url_for('login'))

    bookings = reserve_parking_spot.query.filter_by(user_id=user_id).all()
    return render_template('bookings.html', bookings=bookings)

from datetime import datetime
@app.route('/release/<int:booking_id>/<int:lot_id>', methods=['GET', 'POST'])
def release(booking_id, lot_id):
    booking = reserve_parking_spot.query.get_or_404(booking_id)
    spot = parking_spot.query.get_or_404(booking.parking_spot_id)
    
    if request.method == 'POST':
        releasing_time = datetime.now()
        booking.end_time = releasing_time
        
        # Duration and cost calculation
        duration = (releasing_time - booking.start_time).total_seconds() / 3600
        rate_per_hour = booking.parking_spot.lot.price # adjust as needed
        cost = round(duration * rate_per_hour, 2)
        
        # Update spot status
        spot.status = 'available'
        spot.lot.available_spots += 1
        # Save everything
        db.session.commit()

        flash(f'Parking spot released. Total cost: ₹{cost}', 'info')
        return redirect(url_for('bookings'))
    
    return render_template('release.html', booking=booking, spot=spot,datetime=datetime)


@app.route('/parked_out/<int:booking_id>/<int:lot_id>')
def parked_out(booking_id, lot_id):
    booking = reserve_parking_spot.query.get_or_404(booking_id)
    spot = parking_spot.query.get_or_404(booking.parking_spot_id)
    
    # Update spot status to available
    spot.status = 'available'
    
    # Commit to database
    db.session.commit()
    
    flash('Parking marked as Parked Out', 'success')
    return redirect(url_for('bookings'))


from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/edit_profile_users', methods=['GET', 'POST'])
def edit_profile_users():
    if 'username' not in session:
        flash('You need to login first!', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_username = request.form.get('username')
        old_password = request.form.get('password')
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')

        user = User.query.filter_by(username=old_username).first()

        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('edit_profile_users'))

        if not check_password_hash(user.passhash, old_password):#ikkada we need to use check_password_hash
            flash('Incorrect password!', 'danger')
            return redirect(url_for('edit_profile_users'))

        # here we would update the user profile
        user.username = new_username
        user.passhash = generate_password_hash(new_password)#we would the hash password for security    
        session['username'] = new_username
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('edit_profile_users.html')


import matplotlib
matplotlib.use('Agg')  #for using as non-interactive backend and non GUI based one
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
@app.route('/user_summary')
def user_summary():
    if 'username' not in session:
        flash("Please log in to view your booking summary.", "warning")
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    # Fetch all bookings made by the user
    user_history = reserve_parking_spot.query.filter_by(user_id=user_id).all()

    # Count how many times each parking spot (by location) was booked
    location_counts = Counter()
    for record in user_history:
        try:
            loc = record.parking_spot.lot.location_name
            location_counts[loc] += 1
        except AttributeError:
            continue  # Skip if any data is missing

    if not location_counts:
        flash("No bookings found to summarize.", "info")
        return redirect(url_for('user_dashboard'))

    # Plotting the data using matplotlib
    fig, ax = plt.subplots(figsize=(8, 5))
    locations = list(location_counts.keys())
    bookings = list(location_counts.values())

    ax.bar(locations, bookings, color='mediumseagreen')
    ax.set_title("Your Booking Summary", fontsize=14)
    ax.set_xlabel("Parking Location")
    ax.set_ylabel("Number of Times Booked")
    ax.tick_params(axis='x', rotation=45)

    # Save the plot to a buffer and encode to base64
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return render_template('user_summary_plot.html', chart_data=chart_data)


@app.route('/admin_summary')
def admin_summary():
    if 'username' not in session or not session.get('is_admin'):
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    # Revenue summary: Count bookings per parking lot
    bookings = reserve_parking_spot.query.all()
    revenue_summary = Counter()

    for entry in bookings:
        try:
            lot = entry.parking_spot.lot
            revenue_summary[lot.location_name] += 1
        except AttributeError:
            continue  # Ignore incomplete records

    # Occupancy summary: Count available vs. occupied per lot
    all_lots = parking_lot.query.all()
    occupancy_data = {}

    for lot in all_lots:
        available = sum(1 for spot in lot.spots if spot.status == 'available')
        occupied = sum(1 for spot in lot.spots if spot.status == 'occupied')
        occupancy_data[lot.location_name] = (available, occupied)

    # Plot 1: Revenue by Parking Lot (Bar Chart)
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(revenue_summary.keys(), revenue_summary.values(), color='royalblue')
    ax1.set_title('Total (Bookings) per Parking Lot')
    ax1.set_xlabel('Location')
    ax1.set_ylabel('Bookings')
    ax1.tick_params(axis='x', rotation=45)
    buf1 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    revenue_chart = base64.b64encode(buf1.read()).decode('utf-8')
    buf1.close()
    plt.close(fig1)

    # Plot 2: Availability vs. Occupancy per Lot (Grouped Bar Chart)
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    labels = list(occupancy_data.keys())
    available_counts = [val[0] for val in occupancy_data.values()]
    occupied_counts = [val[1] for val in occupancy_data.values()]

    x = range(len(labels))
    ax2.bar(x, available_counts, width=0.4, label='Available', align='center', color='mediumseagreen')
    ax2.bar([i + 0.4 for i in x], occupied_counts, width=0.4, label='Occupied', align='center', color='salmon')

    ax2.set_xticks([i + 0.2 for i in x])
    ax2.set_xticklabels(labels, rotation=45)
    ax2.set_title('Availability vs. Occupancy per Lot')
    ax2.set_ylabel('Number of Spots')
    ax2.legend()
    plt.tight_layout()
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    occupancy_chart = base64.b64encode(buf2.read()).decode('utf-8')
    buf2.close()
    plt.close(fig2)

    return render_template('admin_summary_plot.html', 
                           revenue_chart=revenue_chart, 
                           occupancy_chart=occupancy_chart)

