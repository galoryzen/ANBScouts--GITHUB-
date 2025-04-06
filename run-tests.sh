#!/bin/bash

# Set the environment to testing for Flask
export FLASK_ENV=testing

# Run pytest with specific flags
uv run flask db upgrade
uv run pytest --disable-warnings -v
