from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

def get_db_connection():
    conn = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    return conn

# Home page
@app.route('/')
def index():
    return render_template('base.html')

# Product routes
@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Product ORDER BY product_id')
    products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        product_name = request.form['product_name']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO Product (product_id, product_name) VALUES (%s, %s)', 
                          (product_id, product_name))
            conn.commit()
            flash('Product added successfully!', 'success')
        except mysql.connector.IntegrityError:
            flash('Product ID already exists!', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('products'))
    
    return render_template('add_edit_forms/product_form.html', form_type='Add')

@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        product_name = request.form['product_name']
        
        cursor.execute('UPDATE Product SET product_name = %s WHERE product_id = %s', 
                      (product_name, product_id))
        conn.commit()
        conn.close()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
    product = cursor.fetchone()
    conn.close()
    return render_template('add_edit_forms/product_form.html', form_type='Edit', product=product)

@app.route('/delete_product/<product_id>')
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if product is referenced in movements
    cursor.execute('SELECT COUNT(*) FROM ProductMovement WHERE product_id = %s', (product_id,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        flash('Cannot delete product. It is referenced in product movements.', 'danger')
    else:
        cursor.execute('DELETE FROM Product WHERE product_id = %s', (product_id,))
        conn.commit()
        flash('Product deleted successfully!', 'success')
    
    conn.close()
    return redirect(url_for('products'))

# Location routes (similar to product routes)
@app.route('/locations')
def locations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Location ORDER BY location_id')
    locations = cursor.fetchall()
    conn.close()
    return render_template('locations.html', locations=locations)

@app.route('/add_location', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        location_id = request.form['location_id']
        location_name = request.form['location_name']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO Location (location_id, location_name) VALUES (%s, %s)', 
                          (location_id, location_name))
            conn.commit()
            flash('Location added successfully!', 'success')
        except mysql.connector.IntegrityError:
            flash('Location ID already exists!', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('locations'))
    
    # For GET request, render the form with empty values
    return render_template('add_edit_forms/location_form.html', form_type='Add', 
                         location={'location_id': '', 'location_name': ''})

@app.route('/edit_location/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        location_name = request.form['location_name']
        
        cursor.execute('UPDATE Location SET location_name = %s WHERE location_id = %s', 
                      (location_name, location_id))
        conn.commit()
        conn.close()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('locations'))
    
    cursor.execute('SELECT * FROM Location WHERE location_id = %s', (location_id,))
    location = cursor.fetchone()
    conn.close()
    return render_template('add_edit_forms/location_form.html', form_type='Edit', location=location)

@app.route('/delete_location/<location_id>')
def delete_location(location_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if location is referenced in movements
    cursor.execute('SELECT COUNT(*) FROM ProductMovement WHERE from_location = %s OR to_location = %s', 
                  (location_id, location_id))
    count = cursor.fetchone()[0]
    
    if count > 0:
        flash('Cannot delete location. It is referenced in product movements.', 'danger')
    else:
        cursor.execute('DELETE FROM Location WHERE location_id = %s', (location_id,))
        conn.commit()
        flash('Location deleted successfully!', 'success')
    
    conn.close()
    return redirect(url_for('locations'))

# Product Movement routes
@app.route('/movements')
def movements():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = '''
    SELECT pm.movement_id, pm.timestamp, 
           p.product_id, p.product_name,
           fl.location_id as from_location_id, fl.location_name as from_location_name,
           tl.location_id as to_location_id, tl.location_name as to_location_name,
           pm.qty
    FROM ProductMovement pm
    JOIN Product p ON pm.product_id = p.product_id
    LEFT JOIN Location fl ON pm.from_location = fl.location_id
    LEFT JOIN Location tl ON pm.to_location = tl.location_id
    ORDER BY pm.timestamp DESC
    '''
    
    cursor.execute(query)
    movements = cursor.fetchall()
    conn.close()
    return render_template('movements.html', movements=movements)

@app.route('/add_movement', methods=['GET', 'POST'])
def add_movement():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        from_location = request.form['from_location'] if request.form['from_location'] != '' else None
        to_location = request.form['to_location'] if request.form['to_location'] != '' else None
        product_id = request.form['product_id']
        qty = int(request.form['qty'])
        
        # Validate that both from and to locations are not the same
        if from_location and to_location and from_location == to_location:
            flash('From and To locations cannot be the same!', 'danger')
            return redirect(url_for('add_movement'))
        
        # Check if there's enough quantity in the from_location
        if from_location:
            available_qty = get_available_quantity(product_id, from_location)
            if available_qty < qty:
                flash(f'Not enough quantity available in {from_location}. Only {available_qty} available.', 'danger')
                return redirect(url_for('add_movement'))
        
        cursor.execute('''
            INSERT INTO ProductMovement (from_location, to_location, product_id, qty)
            VALUES (%s, %s, %s, %s)
        ''', (from_location, to_location, product_id, qty))
        
        conn.commit()
        conn.close()
        flash('Product movement added successfully!', 'success')
        return redirect(url_for('movements'))
    
    # Get products and locations for dropdowns
    cursor.execute('SELECT * FROM Product ORDER BY product_id')
    products = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Location ORDER BY location_id')
    locations = cursor.fetchall()
    
    conn.close()
    return render_template('add_edit_forms/movement_form.html', form_type='Add', 
                          products=products, locations=locations)

@app.route('/edit_movement/<int:movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        from_location = request.form['from_location'] if request.form['from_location'] != '' else None
        to_location = request.form['to_location'] if request.form['to_location'] != '' else None
        product_id = request.form['product_id']
        qty = int(request.form['qty'])
        
        # Validate that both from and to locations are not the same
        if from_location and to_location and from_location == to_location:
            flash('From and To locations cannot be the same!', 'danger')
            return redirect(url_for('edit_movement', movement_id=movement_id))
        
        # Get the original movement to check if we need to revert quantities
        cursor.execute('SELECT * FROM ProductMovement WHERE movement_id = %s', (movement_id,))
        original_movement = cursor.fetchone()
        
        # If from_location changed, we need to check availability
        if from_location and from_location != original_movement['from_location']:
            available_qty = get_available_quantity(product_id, from_location)
            if available_qty < qty:
                flash(f'Not enough quantity available in {from_location}. Only {available_qty} available.', 'danger')
                return redirect(url_for('edit_movement', movement_id=movement_id))
        
        cursor.execute('''
            UPDATE ProductMovement 
            SET from_location = %s, to_location = %s, product_id = %s, qty = %s
            WHERE movement_id = %s
        ''', (from_location, to_location, product_id, qty, movement_id))
        
        conn.commit()
        conn.close()
        flash('Product movement updated successfully!', 'success')
        return redirect(url_for('movements'))
    
    # Get the movement to edit
    cursor.execute('''
        SELECT pm.*, p.product_name
        FROM ProductMovement pm
        JOIN Product p ON pm.product_id = p.product_id
        WHERE pm.movement_id = %s
    ''', (movement_id,))
    movement = cursor.fetchone()
    
    # Get products and locations for dropdowns
    cursor.execute('SELECT * FROM Product ORDER BY product_id')
    products = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Location ORDER BY location_id')
    locations = cursor.fetchall()
    
    conn.close()
    return render_template('add_edit_forms/movement_form.html', form_type='Edit', 
                          movement=movement, products=products, locations=locations)

@app.route('/delete_movement/<int:movement_id>')
def delete_movement(movement_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM ProductMovement WHERE movement_id = %s', (movement_id,))
    conn.commit()
    conn.close()
    
    flash('Product movement deleted successfully!', 'success')
    return redirect(url_for('movements'))

# Report route
@app.route('/report')
def report():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all products and locations
    cursor.execute('SELECT * FROM Product ORDER BY product_id')
    products = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Location ORDER BY location_id')
    locations = cursor.fetchall()
    
    # Calculate balance for each product in each location
    balance_data = []
    for product in products:
        for location in locations:
            quantity = get_available_quantity(product['product_id'], location['location_id'])
            if quantity > 0:
                balance_data.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'location_id': location['location_id'],
                    'location_name': location['location_name'],
                    'quantity': quantity
                })
    
    conn.close()
    return render_template('report.html', balance_data=balance_data)

# Helper function to get available quantity of a product in a location
def get_available_quantity(product_id, location_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate total incoming quantity
    cursor.execute('''
        SELECT COALESCE(SUM(qty), 0) 
        FROM ProductMovement 
        WHERE product_id = %s AND to_location = %s
    ''', (product_id, location_id))
    incoming = cursor.fetchone()[0]
    
    # Calculate total outgoing quantity
    cursor.execute('''
        SELECT COALESCE(SUM(qty), 0) 
        FROM ProductMovement 
        WHERE product_id = %s AND from_location = %s
    ''', (product_id, location_id))
    outgoing = cursor.fetchone()[0]
    
    conn.close()
    return incoming - outgoing

if __name__ == '__main__':
    app.run(debug=True)