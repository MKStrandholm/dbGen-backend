import flask
from flask_cors import CORS

from fetch import fetch_endpoint
from create import create_endpoint
from update import update_endpoint
from delete import delete_endpoint

app = flask.Flask(__name__)
cors = CORS(app)
app.config["DEBUG"] = True

app.register_blueprint(fetch_endpoint)
app.register_blueprint(create_endpoint)
app.register_blueprint(update_endpoint)
app.register_blueprint(delete_endpoint)

app.run()