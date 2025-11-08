
import os, secrets
from flask import Flask

#Flask Object Creation Function

#app.config will act as a dictionary !!!!!!!!!!!
def create_app():
    app = Flask(__name__)
#Create data directory with db, keu and flask key
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
#We try to get the key from Env variable.
    key_file = os.path.join(data_dir, "flask_secret.key")
    key = os.environ.get("FLASK_SECRET_KEY") 
#If we do not have in ENV, then read key for existing file. If empty then create one (secrets.token_hex)
    if not key:
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                key = f.read().strip()
        else:
            key = secrets.token_hex(32)
            with open(key_file, "w") as f:
                f.write(key)
    app.config["SECRET_KEY"] = key

###SQLAlchemy Configuration###

#Create the file -- maybe add condition if existent?
    db_path = os.path.join(data_dir, "app.db")
#Set the DB absolute path in the config
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
#Remove notifications. This was nice in logs but was returning warnings due to version missmatch. I removed it - Protera way
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#Set the data directory path in config
    app.config["DATA_DIR"] = data_dir
#Goes to current directory to models.py
    from .models import db
    db.init_app(app)
#There is no app context when we create the app, so we need to push one to create the DB. That is looking current_app
    with app.app_context():
#Crates the tables. It loads data from db.metadata. 
        db.create_all()

###Load Flask Routes####
#Goes to routes.py
    from .routes import bp as main_bp

    app.register_blueprint(main_bp)
    return app
