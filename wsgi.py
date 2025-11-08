#Calling wsgi gateway service for Gunicorn. 
#App object is called from the __init__.py file in the app folder to create Flask connection per function and not per all together.
from app import create_app
app = create_app()
