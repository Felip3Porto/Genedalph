from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flaskext.mysql import MySQL

mysql = MySQL()
app = Flask(__name__)
static_url_path='/Data'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cello1996'
app.config['MYSQL_DATABASE_DB'] = 'GenedalphFinal'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql.init_app(app)


# db = MySQL(app)
#why are we using name here? 
#this is because it can be equal to __main__

#for login information it is important to key secret keys

# app.config['SECRET_KEY'] = '9a8693e90da7fc1c20a6d96ee8f37764'
# specify relative path

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# ideally it should be random characters 
# import secrets 
# #secrets.token_hex(n) where n is the number of bytes 

# create instance of database


from gene_wizard import routes