# Danslist

A catalog of items. Each item belongs to one catagory.

## Installation
1. [Vagrant](https://www.vagrantup.com/)
2. `git clone https://github.com/d0coat01/catalog danslist`
3. `cd danslist`
4. `vagrant up`
5. `vagrant ssh`
6. `cd /vagrant`
7. `cd danslist`
8. `python db/setup.py testdata.py api.py`
9. [Open App](http://localhost:5000/)

## How permissions work
I added CRUD functionality for categories as well as items. Category write permissions, however, are locked behind a `is_admin` boolean flag. If you wish to be able to edit categories, the easiest way would be to edit `testdata.py`'s `User1` to your google login email and setting the `is_admin` flag to `True`.

Items can only be changed/removed if your user id matches the item's user_id. You must be logged in to create/edit/delete items.

## Input Validation
* You cannot have a blank item name.
* I used another field called label so that you can easily type the path and not worry about capitalization.
* An item's name can only be used once per category (I put a multi-column unique constraint on `Item.category_id` and `Item.name`.
* TODO: A more user-friendly error notification system.

## Code navigation

* `db/setup.py` - contains SQLAlchemy ORM for Category, Item, and User objects. I used sqlite.
* `api.py` - The main flask application. Contains all routes and route logic as well as helper functions.
* `testdata.py` - Example data to get you up and running right away.
* `static/*` - Mobile-first CSS files. `main.css` and `responsive.css` with `responsive.css` containing styling for larger screens.
* `templates/*` - HTML templates using Jinja
