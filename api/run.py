import os
import shelve
import markdown

# Import the framework
from flask import Flask, g
from flask_restful import Api, Resource, reqparse

# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

# Create Database
def get_devices_db():
    db = getattr(g, '_database_devices', None)
    if db is None:
        db = g._database = shelve.open("devices.db")
    return db

def get_readings_db():
    db = getattr(g, '_database_readings', None)
    if db is None:
        db = g._database = shelve.open("readings.db")
    return db

@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database_devices', None)
    if db is not None:
        db.close()

    db_readings = getattr(g, '_database_readings', None)
    if db_readings is not None:
        db_readings.close()

@app.route("/")
def index():
    """Present some documentation"""

    # Open the README file
    with open(os.path.dirname(app.root_path) + '/app/README.md', 'r') as markdown_file:

        # Read the content of the file
        content = markdown_file.read()

        # Convert to HTML
        return markdown.markdown(content)


class DeviceList(Resource):
    def get(self):
        shelf = get_devices_db()
        keys = list(shelf.keys())

        devices = []

        for key in keys:
            devices.append(shelf[key])

        return {'message': 'Success', 'data': devices}, 200

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('station_id', required=True)
        parser.add_argument('lat', required=True)
        parser.add_argument('long', required=True)
        parser.add_argument('app_version', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()

        shelf = get_devices_db()
        shelf[args['station_id']] = args
        return {'message': 'Device registered', 'data': args}, 201


class Device(Resource):
    def get(self, identifier):
        shelf = get_devices_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        return {'message': 'Device found', 'data': shelf[identifier]}, 200

    def delete(self, identifier):
        shelf = get_devices_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        del shelf[identifier]
        return '', 204

    def put(self, identifier):
        shelf = get_devices_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        # Device exists
        parser = reqparse.RequestParser()

        parser.add_argument('station_id', required=True)
        parser.add_argument('lat', required=True)
        parser.add_argument('long', required=True)
        parser.add_argument('app_version', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()

        if identifier != args['station_id']:
            return {'message': 'Device not found (args)', 'data': {}}, 404

        shelf[args['station_id']] = args

        return {'message': 'Device updated', 'data': args}, 201


api.add_resource(DeviceList, '/devices')
api.add_resource(Device, '/device/<string:identifier>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
