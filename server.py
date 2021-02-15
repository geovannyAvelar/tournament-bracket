import config

connex_app = config.connexion_app
connex_app.add_api("swagger.yml")

config.db.create_all()

if __name__ == "__main__":
    connex_app.run(debug = True)