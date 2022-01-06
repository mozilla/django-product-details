DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
SECRET_KEY = "itsasekrit"
# quiets warnings
MIDDLEWARE_CLASSES = []
INSTALLED_APPS = ["product_details"]
