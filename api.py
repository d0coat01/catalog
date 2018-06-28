from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import bleach
# append db directory to python path so we can import sqlalchemy classes.
sys.path.append('./db')
from setup import Base, User, Category, Item
from flask import session as login_session
import random
import string

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Copy your Google oauth2 credentials to client_secrets.json
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Danslist"
app = Flask(__name__)

# From root directory of this application, run python db/setup.py to create database.
engine = create_engine('sqlite:///catalog.db', pool_pre_ping=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
# initializing DBSession() variable at beginning of each function to avoid Flask error.

@app.route('/')
@app.route('/catalog')
def Catalog():
    session = DBSession()
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).filter(Item.category_id==Category.id).order_by(Item.id.desc()).all()
    username = login_session['username'] if 'username' in login_session.keys() else None
    return render_template('catalog.html', categories=categories, username=username, items=items)

@app.route('/catalog/<string:category_name>/items')
def CategoryItems(category_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=bleach.clean(category_name)).one()
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).filter_by(category_id=category.id).filter(Item.category_id==Category.id).order_by(Item.id.desc()).all()
    username = login_session['username'] if 'username' in login_session.keys() else None
    return render_template('catalog.html', items=items, categories=categories, username=username, category=category)
# Admin access only.
@app.route('/categories')
def Categories():
    session = DBSession()
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/JSON')
def CategoriesJSON():
    session = DBSession()
    categories = session.query(Category).order_by(Category.name).all()
    return jsonify(Categories=[r.serialize for r in categories])

@app.route('/categories/new', methods=['GET', 'POST'])
def newCategory():
    session = DBSession()
    if request.method == 'GET':
        return render_template('newcategory.html')
    if request.method == 'POST':
        new_category = Category(
            name=bleach.clean(request.form['name'])
        )
        session.add(new_category)
        session.commit()
        flash(new_category.label + " created.")
        return redirect(url_for('Categories'))

@app.route('/categories/<string:category_name>/edit', methods=['GET', 'POST'])
def editCategory(category_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=bleach.clean(category_name.lower())).one()
    if request.method == 'GET':
        return render_template('editcategory.html', category=category)
    if request.method == 'POST':
        category.label=bleach.clean(request.form['name'])
        category.name = category.label.lower()
        session.add(category)
        session.commit()
        flash(category.label + " updated.")
        return redirect(url_for('Categories'))

@app.route('/categories/<string:category_name>/delete', methods=['GET', 'POST'])
def deleteCategory(category_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=bleach.clean(category_name.lower())).one()
    if request.method == 'GET':
        return render_template('deletecategory.html', category=category)
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash(category.label + " deleted.")
        return redirect(url_for('Categories'))

@app.route('/catalog/items/new', methods=['GET','POST'])
@app.route('/catalog/<string:category_name>/items/new', methods=['GET','POST'])
def newItem(category_name=None):
    if 'user_id' not in login_session:
        return redirect(url_for('showLogin'))
    session = DBSession()
    categories = session.query(Category).order_by(Category.label).all()
    category = None
    if category_name:
        try:
            category = session.query(Category).filter_by(name=bleach.clean(category_name.lower())).one()
        except:
            return "That category wasn't found :("

    if request.method == 'GET':
        return render_template('newitem.html', category=category, categories=categories)
    if request.method == 'POST':
        new_item = Item(
            name=bleach.clean(request.form['name']),
            description=bleach.clean(request.form['description']),
            category_id=bleach.clean(request.form['category']),
            user_id=login_session['user_id']
        )
        session.add(new_item)
        session.commit()
        flash(new_item.label + " created.")
        if category:
            return redirect(url_for('CategoryItems', category_name=category.name))
        return redirect(url_for('Catalog'))

@app.route('/catalog/<string:category_name>/item/<string:item_name>')
def viewItem(category_name, item_name):
    session = DBSession()
    try:
        category = session.query(Category).filter_by(name=bleach.clean(category_name.lower())).one()
    except:
        return "That category wasn't found :("
    try:
        item = session.query(Item).filter_by(category_id=category.id, name=bleach.clean(item_name.lower())).one()
    except:
        return "That item wasn't found :("
    username = None
    if 'username' in login_session:
        username = login_session['username']
    return render_template('viewitem.html', item=item, category=category, username=username)

@app.route('/catalog/<string:category_name>/item/<string:item_name>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    if 'user_id' not in login_session:
        return redirect(url_for('showLogin'))
    session = DBSession()
    try:
        category = session.query(Category).filter_by(name=bleach.clean(category_name.lower())).one()
    except:
        return "That category wasn't found :("
    try:
        item = session.query(Item).filter_by(category_id=category.id, name=bleach.clean(item_name.lower())).one()
    except:
        return "That item wasn't found :("
    categories = session.query(Category).order_by(Category.name).all()
    if request.method == 'GET':
        return render_template('edititem.html', category=category, categories=categories, item=item)
    if request.method == 'POST':
        item.label = bleach.clean(request.form['name'])
        item.name = item.label.lower()
        item.description = bleach.clean(request.form['description'])
        item.category_id = bleach.clean(request.form['category'])
        session.add(item)
        session.commit()
        flash(item.label + " updated.")
        return redirect(url_for('CategoryItems', category_name=category.name))

@app.route('/catalog/<string:category_name>/item/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    session = DBSession()
    try:
        category = session.query(Category).filter_by(name=bleach.clean(category_name.lower())).one()
    except:
        return "That category wasn't found :("
    try:
        item = session.query(Item).filter_by(category_id=category.id, name=bleach.clean(item_name.lower())).one()
    except:
        return "That item wasn't found :("
    if request.method == 'GET':
        return render_template('deleteitem.html', category=category, item=item)
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash(item.label + " deleted.")
        return redirect(url_for('CategoryItems', category_name = category.name))
@app.route('/login')
def showLogin():
    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/connect', methods=['POST'])
def connect():
    # Check to see if valid user
    return "Logging in..."
    # Verify user.
    # Generate and assign auth token to login_session.
    # Return to previous page or go to home page.

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists.
    user_id = getUserId(login_session['email'])
    # If not, create User.
    if user_id is None:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    print(login_session)
    output = 'Done!'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('Catalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('Catalog'))

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

def createUser(login_session) :
    session = DBSession()
    newUser = User(email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    session = DBSession()
    try :
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None

def getUserId(email) :
    session = DBSession()
    try :
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except :
        return None


if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
    # Uncomment for https
    # app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')

