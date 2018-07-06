"""
All endpoints were built using Flask for routing functionality,
Jinja2 for templating, and SQLAlchemy for database interaction.
"""
from functools import wraps
from flask import (Flask, render_template, redirect, url_for,
                   request, jsonify, flash, make_response)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import bleach
from flask import session as login_session
import random
import string
from oauth2client.client import (flow_from_clientsecrets,
                                 FlowExchangeError)
import httplib2
import json
import requests
from setup import Base, User, Category, Item
from queryhelpers import (getCategories, getCategory,
                          getItems, getCategoryItems,
                          getItem)

# Copy your Google oauth2 credentials to client_secrets.json
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Danslist"
app = Flask(__name__)

# From root directory of this application,
# run python db/setup.py to create database.
engine = create_engine('sqlite:///catalog.db', pool_pre_ping=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
# Initializing DBSession() at beginning of each function to avoid Flask error.


def loginRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You must login first.")
            return redirect(url_for('showLogin'))
    return decorated_function


def adminRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' in login_session and login_session['is_admin']:
            return f(*args, **kwargs)
        else:
            flash("You don't have access to that.")
            return redirect(url_for('Catalog'))
    return decorated_function


@app.route('/')
@app.route('/catalog')
def Catalog():
    """
    Retrieves all items from newest to oldest.
    Retrieves all categories.
    Returns Home page.
    """
    session = DBSession()
    categories = getCategories(session)
    items = getItems(session)
    username = (login_session['username']
                if 'username' in login_session.keys()
                else None)
    return render_template('catalog.html', categories=categories,
                           username=username, items=items)


@app.route('/catalog/JSON')
def CatalogJSON():
    """
      Retrieve all categories and their associated items.
      :return:
      JSON-formatted list of categories with each
      category containing a list of items.
      """
    session = DBSession()
    categories = getCategories(session)
    return jsonify(categories=[r.serialize_items for r in categories])


@app.route('/catalog/items/JSON')
def CatalogItemsJSON():
    """
      Retrieve all items in alphabetic order.
      :return:
      JSON-formatted list of items.
      """
    session = DBSession()
    items = getItems(session)
    return jsonify(items=[r.serialize for r in items])


@app.route('/catalog/<string:category_name>/items')
def CategoryItems(category_name):
    """
    View the items for a particular category.
    :param category_name: string
    :return:
    HTML page of a particular category's items.
    """
    session = DBSession()
    category = getCategory(category_name, session)
    categories = getCategories(session)
    items = getCategoryItems(category.id, session)
    username = (login_session['username']
                if 'username' in login_session.keys()
                else None)
    return render_template('catalog.html',
                           items=items,
                           categories=categories,
                           username=username,
                           category=category)


@app.route('/catalog/<string:category_name>/items/JSON')
def CategoryItemsJSON(category_name):
    """
    View the items for a particular category in JSON
    :param category_name: string
    :return:
    JSON-formatted category and its items.
    """
    session = DBSession()
    category = (session.query(Category)
                .filter(Item.category_id == Category.id)
                .filter_by(name=bleach.clean(category_name))
                .one())
    return jsonify(category=category.serialize_items)


# Admin access only.
@app.route('/categories')
def Categories():
    """
    View all categories and potentional actions for them.
    :return:
    HTML page of categories.
    """
    session = DBSession()
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)


@app.route('/categories/JSON')
def CategoriesJSON():
    """
    View all categories in JSON
    :return:
    JSON-formatted list of categories.
    """
    session = DBSession()
    categories = getCategories(session)
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/categories/new', methods=['GET', 'POST'])
@adminRequired
def newCategory():
    """
    Create a new category.
    :return:
    HTML page or redirect
    """
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
@adminRequired
def editCategory(category_name):
    """
    Edit an existing category.
    :param category_name: (string)
    :return:
    HTML page or redirect
    """
    if 'is_admin' not in login_session or not login_session['is_admin']:
        flash("You don't have access to that.")
        return redirect(url_for('Catalog'))
    session = DBSession()
    category = getCategory(category_name, session)
    if request.method == 'GET':
        return render_template('editcategory.html', category=category)
    if request.method == 'POST':
        category.label = bleach.clean(request.form['name'])
        category.name = category.label.lower()
        session.add(category)
        session.commit()
        flash(category.label + " updated.")
        return redirect(url_for('Categories'))


@app.route('/categories/<string:category_name>/delete',
           methods=['GET', 'POST'])
@adminRequired
def deleteCategory(category_name):
    """
    Delete an existing category.
    :param category_name: (string)
    :return:
    Redirect
    """
    if 'is_admin' not in login_session or not login_session['is_admin']:
        flash("You don't have access to that.")
        return redirect(url_for('Catalog'))
    session = DBSession()
    category = getCategory(category_name, session)
    if request.method == 'GET':
        return render_template('deletecategory.html', category=category)
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash(category.label + " deleted.")
        return redirect(url_for('Categories'))


@app.route('/catalog/items/new', methods=['GET', 'POST'])
@app.route('/catalog/<string:category_name>/items/new',
           methods=['GET', 'POST'])
@loginRequired
def newItem(category_name=None):
    """
    Create a new item for category.
    :param category_name: (string)
    :return:
    HTML page
    """
    session = DBSession()
    categories = getCategories(session)
    category = None
    if category_name:
        category = getCategory(category_name, session)

    if request.method == 'GET':
        return render_template('newitem.html',
                               category=category, categories=categories)
    if request.method == 'POST':
        new_item = Item(
            label=bleach.clean(request.form['name']),
            description=bleach.clean(request.form['description']),
            category_id=bleach.clean(request.form['category']),
            user_id=login_session['user_id']
        )
        new_item = addItem(new_item, session)
        flash(new_item.label + " created.")
        if category:
            return redirect(url_for('CategoryItems',
                                    category_name=category.name))
        return redirect(url_for('Catalog'))


def addItem(new_item, session):
    """
    Add item to database.
    :param new_item: (dictionary) new_item dictionary of all item variables.
    :param session: (DBSession) the current session created by DBSession()
    :return:
    new_item dictionary after post-processing.
    """
    new_item.name = new_item.label.lower()
    if len(new_item.name) < 1:
        raise ValueError('Name cannot be empty.')
    session.add(new_item)
    session.commit()
    return new_item


@app.route('/catalog/<string:category_name>/item/<string:item_name>')
def viewItem(category_name, item_name):
    """
    View a particular item from a category.
    :param category_name: (string)
    :param item_name: (string)
    :return:
    HTML page
    """
    session = DBSession()
    category = getCategory(category_name, session)
    item = getItem(category.id, item_name, session)
    username = None
    user_id = None
    if 'username' in login_session:
        username = login_session['username']
        user_id = login_session['user_id']
    return render_template('viewitem.html',
                           item=item, category=category,
                           username=username, user_id=user_id)


@app.route('/catalog/<string:category_name>/item/<string:item_name>/JSON')
def viewItemJSON(category_name, item_name):
    """
    View a particular item from a category in JSON
    :param category_name: (string)
    :param item_name: (string)
    :return:
    JSON-formatted http response
    """
    session = DBSession()
    category = getCategory(category_name, session)
    item = getItem(category.id, item_name, session)
    return jsonify(item=item.serialize)


@app.route('/catalog/<string:category_name>/item/<string:item_name>/edit',
           methods=['GET', 'POST'])
@loginRequired
def editItem(category_name, item_name):
    """
    Edit an existing item.
    :param category_name: (string)
    :param item_name: (string)
    :return:
    HTML page or redirect
    """
    if 'user_id' not in login_session:
        return redirect(url_for('showLogin'))
    session = DBSession()
    category = getCategory(category_name, session)
    item = getItem(category.id, item_name, session)
    if login_session['user_id'] != item.user_id:
        return "You don't have access to this item."
    categories = session.query(Category).order_by(Category.name).all()
    if request.method == 'GET':
        return render_template('edititem.html', category=category,
                               categories=categories, item=item)
    if request.method == 'POST':
        item.label = bleach.clean(request.form['name'])
        item.description = bleach.clean(request.form['description'])
        item.category_id = bleach.clean(request.form['category'])
        item = addItem(item, session)
        flash(item.label + " updated.")
        return redirect(url_for('CategoryItems', category_name=category.name))


@app.route('/catalog/<string:category_name>/item/<string:item_name>/delete',
           methods=['GET', 'POST'])
@loginRequired
def deleteItem(category_name, item_name):
    """
    Delete an existing item
    :param category_name: (string)
    :param item_name: (string)
    :return:
    HTML page or redirect
    """
    session = DBSession()
    category = getCategory(category_name, session)
    item = getItem(category.id, item_name, session)
    if login_session['user_id'] != item.user_id:
        return "You don't have access to this item."
    if request.method == 'GET':
        return render_template('deleteitem.html',
                               category=category, item=item)
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash(item.label + " deleted.")
        return redirect(url_for('CategoryItems',
                                ategory_name=category.name))


@app.route('/login')
def showLogin():
    """
    Generate an state token and display the login page.
    """
    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Using Google's OAUTH2 service, validate and initiate a session.
    The session data is saved in Flask session.
    :return:
    "Done!"
    """
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
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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
    login_session['email'] = data['email']

    # Check if user exists.
    user_id = getUserId(login_session['email'])
    # If not, create User.
    if user_id is None:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    userinfo = getUserInfo(user_id)
    login_session['is_admin'] = userinfo.is_admin
    output = 'Done!'
    flash("you are now logged in as %s" % login_session['username'])
    return output


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    """
    Revoke the current auth session token.
    Delete existing login_session data.
    :return:
    redirect
    """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('Catalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('Catalog'))


@app.route('/gdisconnect')
def gdisconnect():
    """
    Revoke the current user's google auth token.
    :return:
    JSON 200 "Successfully disconnected" response
    """
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
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400)
        )
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(login_session):
    """
    Create a new user in database table 'user'
    :param login_session: (DBSession) login_session
    :return:
    User.id integer from newly created user row.
    """
    session = DBSession()
    newUser = User(email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserId(email):
    """
    Retrieve an existing user id using an email address
    :param email: (string)
    :return:
    User.id integer
    """
    session = DBSession()
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        return None


def getUserInfo(id):
    """
    Retrieve an existing user's data.
    :param id: (integer) User.id
    :return:
    'user' row data
    """
    session = DBSession()
    try:
        user = session.query(User).filter_by(id=id).one()
        return user
    except SQLAlchemyError:
        return None


if __name__ == '__main__':
    app.secret_key = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
    # Uncomment for https
    # app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
