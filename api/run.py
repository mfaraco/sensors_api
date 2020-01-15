import os
import markdown
from datetime import datetime

# Import the framework
from flask import Flask, g, jsonify
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Create an instance of Flask
app = Flask(__name__)

# Create Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api.db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Create the API
api = Api(app)

# Create Models
class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, unique=False, nullable=False)
    longitude = db.Column(db.Float, unique=False, nullable=False)
    app_version = db.Column(db.String(10), nullable=False, default='0.01')
    readings = db.relationship('Reading', backref='station', lazy=True)

    def __init__(self, latitude, longitude, app_version):
        self.latitude = latitude
        self.longitude = longitude
        self.app_version = app_version

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reading = db.Column(db.String(20), unique=False, nullable=False)
    app_version = db.Column(db.String(10), unique=False, nullable=True)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)

    def __init__(self, timestamp, reading, app_version, station_id):
        self.timestamp = datetime.utcnow()
        self.reading = reading
        self.app_version = app_version
        self.station_id = station_id


# Schemas for JSON representation
class StationSchema(ma.Schema):
    class Meta:
        fields = ("id","latitude","longitude","app_version")
class ReadingSchema(ma.Schema):
    class Meta:
        fields = ("id","timestamp","reading","app_version","station_id")

# Init schema
station_schema = StationSchema()
stations_schema = StationSchema(many=True)
reading_schema = ReadingSchema()
readings_schema = ReadingSchema(many=True)

# Create Routes
@app.route("/")
def index():
    """Present barebones documentation"""

    # Open the README file
    with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:

        # Read the content of the file
        content = markdown_file.read()

        # Convert to HTML
        return markdown.markdown(content)

# Only for creatingthe database on first run
@app.route("/init/")
def init():
    """Initialize Database"""
    res = db.create_all()
    return "OK"

# Handler for all devices list
class handler_DeviceList(Resource):
    def get(self):
        all_stations = Station.query.all()

        return stations_schema.dump(all_stations), 200

# HAndler for CRUD operations on Stations
class handler_Device(Resource):
    def get(self, identifier):
        """ Returns a Station. """
        station = Station.query.get_or_404(identifier)

        return station_schema.dump(station), 200

    def post(self):
        """ creates a Station. """
        # Device params
        parser = reqparse.RequestParser()

        parser.add_argument('latitude', required=True)
        parser.add_argument('longitude', required=True)
        parser.add_argument('app_version', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()

        station = Station( args.latitude,
                           args.longitude,
                           args.app_version
                           )

        db.session.add(station)
        db.session.commit()

        return station_schema.dump(station), 201

    def delete(self, identifier):
        """ Deletes a Station. """
        station = Station.query.get_or_404(identifier)

        db.session.delete(station)
        db.session.commit()
        
        return '', 204

    def put(self, identifier):
        """ Modifies a Station. """
        station = Station.query.get_or_404(identifier)

        # Device params
        parser = reqparse.RequestParser()

        parser.add_argument('latitude', required=True)
        parser.add_argument('longitude', required=True)
        parser.add_argument('app_version', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()

        station.latitude = args.latitude
        station.longitude = args.longitude
        station.app_version = args.app_version

        db.session.commit()

        return station_schema.dump(station), 201

class handler_ReadingList(Resource):
    def get(self):
        """ Returns All readings. """
        all_readings = Reading.query.all()

        return readings_schema.dump(all_readings), 200

class handler_Reading(Resource):
    def post(self):
        """ Crates/Inserts a Reading. """
        # Reading params
        parser = reqparse.RequestParser()

        parser.add_argument('station_id', required=True)
        parser.add_argument('reading', required=True)
        parser.add_argument('timestamp', required=True)
        parser.add_argument('app_version', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()

        reading = Reading( station_id = args.station_id,
                           reading = args.reading,
                           timestamp = datetime.utcnow(),
                           app_version = args.app_version
                           )
        # If the stations doesn't exist fail
        station = Station.query.get_or_404(args.station_id)

        db.session.add(reading)
        db.session.commit()

        return reading_schema.dump(reading), 201

# Routes Definitions
api.add_resource(handler_DeviceList, '/devices')
api.add_resource(handler_Device, '/device/<int:identifier>', '/device')
api.add_resource(handler_ReadingList, '/readings')
api.add_resource(handler_Reading, '/reading')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
