import os
import click
from flask import Flask, jsonify
from flask.cli import with_appcontext
from src.scripts.generate_mock_data import generate_mock_data 
from flask_jwt_extended import JWTManager
from src.tasks import long_task_worker
from src.models.main import db
from dotenv import load_dotenv
from src import video
from src import public
from flask_migrate import Migrate, upgrade
from src.auth import auth_bp
from datetime import timedelta



load_dotenv()

app = Flask(__name__)

db_password = os.getenv("POSTGRES_PASSWORD")
db_user = os.getenv("POSTGRES_USER")
db_name = os.getenv("POSTGRES_DB")

is_testing_mode = os.getenv("FLASK_ENV") == "testing"

connection = (
    "sqlite:///:memory:"
    if is_testing_mode
    else f"postgresql://{db_user}:{db_password}@postgres/{db_name}?sslmode=disable"
)

app.config['SQLALCHEMY_DATABASE_URI'] = connection
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'lamejorfrase')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_VERIFY_SUB'] = False

app_context = app.app_context()
app_context.push()

db.init_app(app)

migrate = Migrate(app, db)

if is_testing_mode:
    with app.app_context():
        upgrade()

jwt = JWTManager(app)


# Video routes
video.register_blueprints(app)
public.register_blueprints(app)
app.register_blueprint(auth_bp)

@click.command("create-mock-data")
@with_appcontext
def create_mock_data():
    generate_mock_data()
    click.echo("Mock data generated successfully!")

app.cli.add_command(create_mock_data)

@app.route("/")
def hello_world():
    return {"message": "Hello, World!"}, 200


@app.route("/long-task")
def long_task():
    task = long_task_worker.delay()
    return {"message": "Task started", "task_id": task.id}, 202