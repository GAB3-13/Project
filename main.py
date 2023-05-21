from flask import Flask, session, render_template, request, redirect, url_for
import mysql.connector
import time
from datetime import datetime

from flask import jsonify

app = Flask(__name__)
app.secret_key = 'MATOS'


mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="l21iu3y34hjjkuhj34kjbihjk",
  database="softwareproject"
)

@app.route('/')
def home():
    cursor = mydb.cursor()
    query = ("SELECT id, title,image, price FROM products")
    cursor.execute(query)
    items = []
    for (id, title, image, price) in cursor:
        items.append({'id': id, 'title': title,'image': image,'price': price})
    return render_template('home.html', items=items)
@app.route('/login', methods =['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('email-input'):
            email = request.form['email-input']
            if 'username' in session:
                session.pop('username')
            else:
                mycursor = mydb.cursor()
                sql = "SELECT * FROM users WHERE email = (%s)"
                val = (email,)
                mycursor.execute(sql, val)
                result = mycursor.fetchone()
                if result:
                    session['email'] = email
                    return redirect(url_for('emaillog', email=email))
                else:
                    return render_template('signup.html', error_message='No account with this email please sign up')
        elif request.form.get('username-input'):
            username = request.form['username-input']
            if 'email' in session:
                session.pop('email')
            else:
                mycursor = mydb.cursor()
                sql = "SELECT * FROM users WHERE username = %s"
                val = (username,)
                mycursor.execute(sql, val)
                result = mycursor.fetchone()
                if result:
                    session['username'] = username
                    return render_template('email-login.html', username=username)
                else:
                    return render_template('signup.html', error_message='No account with this username please sign up')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')
    return render_template('login.html')
@app.route('/futurehome')
def home1():
    cursor = mydb.cursor()
    query = ("SELECT * FROM products ORDER BY id DESC LIMIT 3")
    cursor.execute(query)
    # cursor.execute("SELECT * FROM products ORDER BY id DESC LIMIT 3")
    products = cursor.fetchall()
    print(products)
    cursor.close()
    # mydb.close()
    return render_template('index.html', products=products)
@app.route('/login/email-login', methods=['GET', 'POST'])
def emaillog():
    if 'email' in session:
        email = session.get('email')
    else:
        email = ''
    if 'username' in session:
        username = session.get('username')
    else:
        username = ''

    if request.method == 'POST':
        password = request.form['password']
        mycursor = mydb.cursor()
        if email:
            sql = "SELECT * FROM users WHERE email = %s"
            val = (email,)
        else:
            sql = "SELECT * FROM users WHERE username = %s"
            val = (username,)
        mycursor.execute(sql, val)
        result = mycursor.fetchone()
        if result:
            if result[5] == 'Admin':
                if result[4] == password:  # Check if the password is correct
                    session['logged_in'] = True
                    session['id'] = result[0]
                    session['username'] = result[1]
                    return redirect(url_for('adminlog'))
            elif result[5] == 'Vendor':
                if result[4] == password:  # Check if the password is correct for the vendor
                    session['logged_in'] = True
                    session['id'] = result[0]
                    session['username'] = result[1]
                    return redirect(url_for('vendor'))
            else:
                if result[4] == password:
                    session['logged_in'] = True
                    session['id'] = result[0]
                    # return redirect(url_for('home'))
        return render_template('email-login.html', email=email, username=username)

    return render_template('email-login.html', email=email, username=username)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['firstname']
        email = request.form['email']
        password = request.form['password']
        account_type = request.form['account_type']

        cursor = mydb.cursor()
        query = "INSERT INTO users (username, first_name, email, password, account_type) VALUES (%s, %s, %s, %s, %s)"
        values = (username, first_name, email, password, account_type)
        cursor.execute(query, values)
        mydb.commit()

        return render_template('signup-success.html')

    return render_template('signup.html')

@app.route('/vendor', methods=['GET', 'POST'])
def vendor():
    cursor = mydb.cursor()
    username = session.get('username')
    id = session.get('id')
    # print(id)
    # print(username)

    account_query = "SELECT account_type FROM users WHERE id = %s AND username = %s"
    cursor.execute(account_query, (id, username))
    account_type = cursor.fetchone()

    if account_type is None or account_type[0] != 'Vendor':
        return "You are not a vendor."

    items_query = "SELECT id, title, description, image, category, inventory, price FROM products WHERE vendor = %s"
    cursor.execute(items_query, (username,))
    items = []
    for (item_id, title, description, image, category, inventory, price) in cursor:
        items.append({
            'id': item_id,
            'title': title,
            'description': description,
            'image': image,
            'category': category,
            'inventory': inventory,
            'price': price
        })

    orders_query = """
    SELECT oc.order_id, oc.user_id, oc.order_number, oc.total_price, oc.status
    FROM orders AS oc
    JOIN orders_items AS oi ON oc.order_id = oi.order_id
    JOIN products AS p ON oi.product_id = p.id
    WHERE p.vendor = %s AND oc.status = 'Pending'
    """
    cursor.execute(orders_query, (username,))
    orders = []
    for (order_id, user_id, order_number, total_price, status) in cursor:
        orders.append({
            'order_id': order_id,
            'user_id': user_id,
            'order_number': order_number,
            'total_price': total_price,
            'status': status
        })

    return render_template('vendor-login.html', items=items, orders=orders)



@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        new_status = request.form.get('new_status')

        cursor = mydb.cursor()

        update_query = "UPDATE orders SET status = %s WHERE order_id = %s"
        cursor.execute(update_query, (new_status, order_id))
        mydb.commit()

        return redirect('/vendor')

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlog():
    cursor = mydb.cursor()
    username = session.get('username')
    id = session.get('id')

    account_query = "SELECT account_type FROM users WHERE id = %s AND username = %s"
    cursor.execute(account_query, (id, username))
    account_type = cursor.fetchone()

    if account_type is None or account_type[0] != 'Admin':
        return "You are not an admin."

    cursor = mydb.cursor()
    query = "SELECT id, title, description, image, category, inventory, price FROM products"
    cursor.execute(query)
    items = []
    for (item_id, title, description, image, category, inventory, price) in cursor:
        items.append({
            'id': item_id,
            'title': title,
            'description': description,
            'image': image,
            'category': category,
            'inventory': inventory,
            'price': price
        })

    query = "SELECT return_id, order_id, user_id, product_id, return_type, title, description, demand, status FROM returns_refunds"
    cursor.execute(query)
    returns = []
    for (return_id, order_id, user_id, product_id, return_type, title, description, demand, status) in cursor:
        returns.append({
            'return_id': return_id,
            'order_id': order_id,
            'user_id': user_id,
            'product_id': product_id,
            'return_type': return_type,
            'title': title,
            'description': description,
            'demand': demand,
            'status': status
        })

    return render_template('admin-login.html', items=items, returns=returns)

@app.route('/update_status', methods=['POST'])
def update_status():
    return_id = request.form.get('return_id')
    status = request.form.get('status')

    cursor = mydb.cursor()
    query = "UPDATE returns_refunds SET status = %s WHERE return_id = %s"
    values = (status, return_id)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()
    return redirect('/adminlogin')

@app.route('/Womenswear')
def Women():
    cursor = mydb.cursor()
    query = ("SELECT id, title,image, price FROM products where category = 'womenswear'")
    cursor.execute(query)
    items = []
    for (id, title, image, price) in cursor:
        items.append({'id': id, 'title': title,'image': image,'price': price})
    return render_template('Womenswear.html', items=items)

@app.route('/Menswear')
def Mens():
    cursor = mydb.cursor()
    query = ("select id,title,image,price from products where category = 'menswear'")
    cursor.execute(query)
    items = []
    for (id, title, image, price) in cursor:
        items.append({'id': id, 'title': title,'image': image,'price': price})
    return render_template('menswear.html', items=items)
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_text = request.form['search_text']
        cursor = mydb.cursor()
        query = f"SELECT id,title,image,price FROM products WHERE description like \'%{search_text}%\' or title like \'%{search_text}%\'"
        cursor.execute(query)
        items = []
        for (id, title, image, price) in cursor:
            items.append({'id': id, 'title': title, 'image': image, 'price': price})
        return render_template('home.html', items=items)
    else:
        return render_template('home.html')

@app.route('/info', methods=['GET', 'POST'])
def info():
    if request.method == 'POST':
        if 'username' in session or 'email' in session:
            # print('wurk')
            return render_template('item.html')
        else:
            # print('no')
            return render_template('item.html')
    else:
        id = request.args.get('id')
        # print(id)
        cursor = mydb.cursor()
        query = """
            SELECT p.id, p.title, p.description, p.image, p.category, p.inventory, p.price, ps.size, ps.quantity
            FROM products AS p
            JOIN product_size AS ps ON p.id = ps.mainid
            WHERE p.id = %s
        """
        values = (id,)
        cursor.execute(query, values)
        items = cursor.fetchall()
        # print(items)
        # print(items)
        query2 = """
            SELECT p.id, p.title, p.description, p.image, p.category, p.inventory, p.price
            FROM products AS p
            WHERE p.id = %s
        """
        values = (id,)
        cursor.execute(query2, values)
        items2 = cursor.fetchall()
        # print(items2)

        reviews_query = "SELECT c.rating,c.comment,p.username,l.description FROM reviews as c join users as p on c.user_id = p.id join products AS l on c.item_id = l.id WHERE item_id = %s;"

        reviews = []
        for item in items2:
            item_id = item[0]
            cursor.execute(reviews_query, (id,))
            for (rating, comment,username,description) in cursor:
                # print(rating, comment,username,description)
                reviews.append({'rating': rating, 'comment': comment,'username': username,'description': description})

        return render_template('item.html', item=items, reviews=reviews)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'username' in session or 'email' in session:
        user_id = session.get('id')

        cursor = mydb.cursor()
        query = "SELECT  c.product_id, c.cart_id, c.size, p.title, p.description, p.image, p.price, c.quantity FROM cart AS c JOIN products AS p ON c.product_id = p.id where c.user_id = %s"

        values = (user_id,)
        cursor.execute(query, values)
        # print(values)
        items = []
        for (product_id, cart_id, size, title, description, image, price, quantity) in cursor:
            items.append({'product_id': product_id, 'cart_id': cart_id, 'size': size, 'title': title, 'description': description, 'image': image, 'price': price, 'quantity': quantity})

        if request.method == 'POST':
            for item in items:
                cart_id = item['cart_id']
                quantity = int(request.form.get(f'quantity-{cart_id}'))
                cursor.execute("UPDATE cart SET quantity = %s WHERE cart_id = %s", (quantity, cart_id))
                mydb.commit()

        return render_template('cart.html', items=items)
    else:
        return redirect('/login')



@app.route('/wish', methods=['GET', 'POST'])
def wish():
    if 'username' in session or 'email' in session:
        user_id = session.get('id')
        cursor = mydb.cursor()
        query = "SELECT c.product_id,c.cart_id,p.title, p.description, p.image, p.price, ps.size FROM wish AS c JOIN products AS p ON c.product_id = p.id JOIN product_size AS ps ON c.product_id = ps.sizeid WHERE c.user_id = %s"
        values = (user_id,)
        cursor.execute(query, values)

        items = []
        for (product_id,cart_id, title, description, image, price, size) in cursor:
            items.append({'product_id': product_id,'cart_id': cart_id, 'title': title, 'description': description, 'image': image, 'price':price, 'size': size})

        return render_template('wish.html', items=items)
    else:
        return redirect('/login')
@app.route('/addcart', methods=['GET', 'POST'])
def addcart():
    if 'username' in session or 'email' in session:
        user_id = session.get('id')
        product_id = request.args.get('id')
        selected_size = request.args.get('size')
        # print(user_id, product_id, selected_size)

        cursor = mydb.cursor()
        query = "INSERT INTO cart (user_id, product_id, size,quantity) VALUES (%s, %s, %s,1)"
        values = (user_id, product_id, selected_size)
        cursor.execute(query, values)
        mydb.commit()

        return redirect('/cart')
    else:
        return redirect('/login')



@app.route('/addwish', methods=['GET', 'POST'])
def addwish():
    if 'username' in session or 'email' in session:
        user_id = session.get('id')
        product_id = request.args.get('id')
        selected_size = request.form.get('product-size')
        # print(user_id, product_id, selected_size)

        cursor = mydb.cursor()
        query = "INSERT INTO wish (user_id, product_id, size) VALUES (%s, %s, %s)"
        values = (user_id, product_id, selected_size)
        cursor.execute(query, values)
        mydb.commit()

        return redirect('/wish')
    else:
        return redirect('/login')

@app.route('/removeitem', methods=['POST'])
def remove_item():
    if 'username' in session or 'email' in session:
        user_id = session.get('id')
        cart_id = request.form.get('cart_id')
        # print(user_id,cart_id)
        cursor = mydb.cursor()
        query = "DELETE FROM cart WHERE user_id = %s AND cart_id = %s"
        values = (user_id, cart_id)
        cursor.execute(query, values)
        mydb.commit()

        return redirect('/cart')
    else:
        return redirect('/login')


@app.route('/Items')
def items():
    cursor = mydb.cursor()
    query = "SELECT id, title, image, price FROM products WHERE category = 'items'"
    cursor.execute(query)

    items = []
    for (id, title, image, price) in cursor:
        items.append({'id': id, 'title': title, 'image': image, 'price': price})

    return render_template('Items.html', items=items)



@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        id = request.form.get('id')
        # print(id)
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.form.get('image')
        category = request.form.get('category')
        inventory = request.form.get('inventory')
        price = request.form.get('price')
        print(id, title, description, image, category, inventory, price)
        cursor = mydb.cursor()
        query = "UPDATE products SET title = %s,description = %s,image =%s,category =%s,inventory =%s,price =%s WHERE id = %s;"
        values = (title,description,image,category,inventory,price,id)
        cursor.execute(query, values)
        mydb.commit()
        item = cursor.fetchone()

        print(item)
        return redirect('/futurehome')
    else:
        id = request.args.get('id')
        # print(id)
        cursor = mydb.cursor()
        query = "SELECT title, description, image, category, inventory, price FROM products WHERE id = %s"
        values = (id,)
        cursor.execute(query, values)
        item = cursor.fetchone()
        # print(item)
        return render_template('edit.html', item=item,id=id)

@app.route('/delete', methods=['POST'])
def deleteitem():
    item_id = request.form.get('id')
    # print(item_id)
    cursor = mydb.cursor()
    cart_delete_query = "DELETE FROM cart WHERE product_id = %s"
    cursor.execute(cart_delete_query, (item_id,))
    product_size_delete_query = "DELETE FROM product_size WHERE mainid = %s"
    cursor.execute(product_size_delete_query, (item_id,))
    products_delete_query = "DELETE FROM products WHERE id = %s"
    cursor.execute(products_delete_query, (item_id,))
    mydb.commit()
    return redirect('/vendor')



@app.route('/additem', methods=['GET', 'POST'])
def add_item():

    if request.method == 'POST':
        print('runnign additem')
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.form.get('image')
        category = request.form.get('category')
        price = request.form.get('price')
        user_id = session.get('id')

        cursor = mydb.cursor()
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            username = result[0]
        else:
            username = None

        query = "INSERT INTO products (title, description, image, category, price, vendor) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (title, description, image, category, price, username)
        cursor.execute(query, values)
        mydb.commit()
        product_id = cursor.lastrowid
        cursor.close()
        session['product_id'] = product_id
        print(product_id)
        return redirect(url_for('add_size', product_id=product_id))

    return render_template('additem.html')


@app.route('/addsize', methods=['GET', 'POST'])
def add_size():
    product_id = session.get('product_id')
    print(product_id)
    if request.method == 'POST':
        sizes = request.form.getlist('size[]')
        inventories = request.form.getlist('inventory[]')

        if len(sizes) != len(inventories):
            return "Invalid size and inventory data"

        cursor = mydb.cursor()
        print(sizes, inventories)

        for size, inventory in zip(sizes, inventories):
            query = "INSERT INTO product_size (mainid, size, quantity) VALUES (%s, %s, %s)"
            values = (product_id, size, inventory)
            cursor.execute(query, values)

        mydb.commit()
        cursor.close()

        return redirect('/')

    return render_template('addsize.html', product_id=product_id)

import time

def generate_order_number(user_id):
    timestamp = int(time.time())
    order_number = f"{user_id}_{timestamp}"
    return order_number

def calculate_total_price(items):
    total_price = 0
    cursor = mydb.cursor()
    for item in items:
        query = "SELECT price FROM products WHERE id = %s"
        values = (item['product_id'],)
        cursor.execute(query, values)
        result = cursor.fetchone()
        if result:
            price = result[0]
            total_price += price
    return total_price
def get_cart_items(user_id):
    cursor = mydb.cursor()
    query = """
    SELECT c.cart_id, c.user_id, c.product_id, c.size, p.price, p.description, p.image, p.vendor
    FROM cart c
    JOIN products p ON c.product_id = p.id
    WHERE c.user_id = %s
    """
    values = (user_id,)
    cursor.execute(query, values)
    cart_items = cursor.fetchall()
    items = []
    for item in cart_items:
        item_data = {
            'cart_id': item[0],
            'user_id': item[1],
            'product_id': item[2],
            'size': item[3],
            'price': item[4],
            'description': item[5],
            'image': item[6],
            'vendor': item[7]
        }
        items.append(item_data)
    return items

@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if 'id' in session:
        user_id = session['id']
        cursor = mydb.cursor()
        query = """
        SELECT c.cart_id, c.user_id, c.product_id, c.size, p.price, p.description, p.image, p.vendor
        FROM cart AS c
        JOIN products AS p ON c.product_id = p.id
        WHERE c.user_id = %s
        """
        values = (user_id,)
        cursor.execute(query, values)
        cart_items = cursor.fetchall()
        items = []
        total_price = 0
        for item in cart_items:
            item_data = {
                'cart_id': item[0],
                'user_id': item[1],
                'product_id': item[2],
                'size': item[3],
                'price': item[4],
                'description': item[5],
                'image': item[6],
                'vendor': item[7]
            }
            items.append(item_data)
            total_price += item[4]

        return render_template('checkout.html', items=items, total=total_price)
    else:
        return redirect('/login')


@app.route('/order_complete', methods=['POST'])
def order_complete():
    if 'id' in session:
        user_id = session['id']
        cursor = mydb.cursor()
        query = """
        SELECT c.cart_id, c.user_id, c.product_id, c.size, p.price, p.description, p.image, p.vendor
        FROM cart AS c
        JOIN products AS p ON c.product_id = p.id
        WHERE c.user_id = %s
        """
        values = (user_id,)
        cursor.execute(query, values)
        cart_items = cursor.fetchall()
        items = []
        total_price = 0
        for item in cart_items:
            item_data = {
                'cart_id': item[0],
                'user_id': item[1],
                'product_id': item[2],
                'size': item[3],
                'price': item[4],
                'description': item[5],
                'image': item[6],
                'vendor': item[7]
            }
            items.append(item_data)
            total_price += item[4]

        order_number = generate_order_number(user_id)
        status = 'Pending'

        cursor.execute("INSERT INTO orders (order_number, user_id, total_price, status) VALUES (%s, %s, %s, %s)",
                       (order_number, user_id, total_price, status))
        order_id = cursor.lastrowid

        for item in items:
            cursor.execute("INSERT INTO orders_items (order_id, user_id, product_id, size, price, description, image, vendor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (order_id, item['user_id'], item['product_id'], item['size'], item['price'], item['description'], item['image'], item['vendor']))

        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        mydb.commit()

        return render_template('paid.html')
    else:
        return redirect('/login')

def clear_cart(user_id):
    cursor = mydb.cursor()
    query = "DELETE FROM cart WHERE user_id = %s"
    values = (user_id,)
    cursor.execute(query, values)
    mydb.commit()

@app.route('/userorders', methods=['GET'])
def userorder():
    if 'id' in session:
        user_id = session['id']
        cursor = mydb.cursor()
        query = """
        SELECT oi.*, o.status
        FROM orders_items AS oi
        JOIN orders AS o ON oi.order_id = o.order_id
        WHERE oi.user_id = %s;
        """
        cursor.execute(query, (user_id,))
        orders = []
        for (
            order_item_id,
            order_id,
            user_id,
            product_id,
            size,
            price,
            description,
            image,
            vendor,
            status,
        ) in cursor:
            orders.append(
                {
                    'order_item_id': order_item_id,
                    'order_id': order_id,
                    'user_id': user_id,
                    'product_id': product_id,
                    'size': size,
                    'price': price,
                    'description': description,
                    'image': image,
                    'vendor': vendor,
                    'status': status,
                }
            )
        return render_template('userorder.html', orders=orders)
    else:
        return "Please log in to view your orders."


@app.route('/returns', methods=['POST', 'GET'])
def returns():
    if request.method == 'GET':
        product_id = request.args.get('product_id')
        order_id = request.args.get('order_id')
        print(product_id,order_id)

        cursor = mydb.cursor()
        query = "SELECT * FROM products WHERE id = %s"
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        print(product)
        cursor.close()
        item = {
            'image': product[3],
            'title': product[1],
            'description': product[2]
        }
        return render_template('return.html', item=item, order_id=order_id,product_id=product_id)

    elif request.method == 'POST':
        product_id = request.form.get('product_id')
        order_id = request.form.get('order_id')
        print(product_id,order_id)
        complaint_type = request.form.get('complaint_type')
        complaint_comment = request.form.get('complaint_comment')
        title = request.form.get('title')
        user_id = session.get('id')
        cursor = mydb.cursor()
        query = "INSERT INTO returns_refunds (order_id, user_id, product_id, return_type, title, description, demand) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (order_id, user_id, product_id, complaint_type, title, complaint_comment, complaint_type)
        cursor.execute(query, values)
        mydb.commit()

        cursor.close()

        return redirect('/userorders')


@app.route('/review', methods=['POST', 'GET'])
def review():
    if request.method == 'GET':
        item_id = request.args.get('product_id')
        cursor = mydb.cursor()
        query = "SELECT id,title, description, image, price, vendor FROM products WHERE id = %s"
        cursor.execute(query, (item_id,))
        item = cursor.fetchone()
        if item is None:
            return "Item not found."
        id,title, description, image, price, vendor = item
        item_dict = {
            'id' : id,
            'title': title,
            'description': description,
            'image': image,
            'price': price,
            'vendor': vendor,
        }
        if item is None:
            return "Item not found."
        return render_template('review.html', item=item_dict)

    elif request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        item_id = request.form.get('item_id')
        cursor = mydb.cursor()
        query = "INSERT INTO items_review (item_id, rating, comment) VALUES (%s, %s, %s)"
        cursor.execute(query, (item_id, rating, comment))
        mydb.commit()

        return "Review submitted successfully."

@app.route('/submit_review', methods=['POST'])
def submit_review():
    item_id = request.form.get('item_id')
    vendor = request.form.get('vendor')
    user_id = session.get('id')
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    cursor = mydb.cursor()
    query = "INSERT INTO reviews (item_id, vendor, user_id, rating, comment) VALUES (%s, %s, %s, %s, %s);"
    values = (item_id, vendor, user_id, rating, comment)
    cursor.execute(query, values)
    mydb.commit()
    return redirect('/userorders')


@app.route('/logout', methods=['GET'])
def logout():
    if 'username' in session:
        session.pop('username')
    if 'email' in session:
        session.pop('email')
    return redirect(url_for('login'))


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        sender_id = session['id']
        message = request.form['message']
        receiver_id = int(request.form.get('receiver_id', 0))
        send_chat_message(sender_id, receiver_id, message)
        print(sender_id, receiver_id, message)
    sender_id = session['id']
    vendors = get_vendors()
    admins = get_admins()
    receiver_id = int(request.args.get('receiver_id', 0))
    chat_messages = get_chat_messages(sender_id, receiver_id)
    print(chat_messages)
    return render_template('chat.html', chat_messages=chat_messages, receiver_id=receiver_id, vendors=vendors, admins=admins)



@app.route('/receiver', methods=['POST'])
def select_receiver():
    receiver_id = int(request.form['receiver_id'])
    return redirect(url_for('chat', receiver_id=receiver_id))



def send_chat_message(sender_id, receiver_id, message):
    cursor = mydb.cursor()
    query = "INSERT INTO chat (sender_id, receiver_id, message, timestamp) VALUES (%s, %s, %s, %s)"
    timestamp = datetime.now()
    values = (sender_id, receiver_id, message, timestamp)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()

def get_chat_messages(sender_id, receiver_id):
    cursor = mydb.cursor()
    query = "SELECT * FROM chat WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) ORDER BY timestamp"
    values = (sender_id, receiver_id, receiver_id, sender_id)
    cursor.execute(query, values)
    chat_messages = cursor.fetchall()
    print(chat_messages)
    cursor.close()

    return chat_messages

def get_vendors():
    cursor = mydb.cursor()
    query = "SELECT id, username FROM users WHERE account_type = 'vendor'"
    cursor.execute(query)
    vendors = cursor.fetchall()
    print(vendors)
    cursor.close()

    return vendors

def get_admins():
    cursor = mydb.cursor()
    query = "SELECT id, username FROM users WHERE account_type = 'admin'"
    cursor.execute(query)
    admins = cursor.fetchall()
    cursor.close()
    return admins
@app.route('/process_payment', methods=['POST'])
def paid():
    return render_template('paid.html')


if __name__ == '__main__':
    app.run(debug=True)
