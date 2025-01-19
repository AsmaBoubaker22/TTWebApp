from flask import Flask
from configuration import create_application
from configuration.dbInitialization import db

app = create_application()
with app.app_context():
    db.create_all()
with app.app_context():
    print(app.url_map)


if __name__ == '__main__' :
    app.run(debug=True)

