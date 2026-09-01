"""PythonAnywhere Web → WSGI file. Loads /home/saadmasoodd22/wsgi.py."""

import os
import sys
import traceback

project = "/home/saadmasoodd22/voice-ai-patient-agent"
os.chdir(project)
sys.path.insert(0, project)
sys.path.insert(0, "/home/saadmasoodd22")

os.environ["APP_ENV"] = "pythonanywhere"
os.environ["SKIP_LIFESPAN"] = "1"
os.environ["DATABASE_URL"] = "sqlite:////home/saadmasoodd22/voice-ai-patient-agent/voice_ai.db"
os.environ["PUBLIC_BASE_URL"] = "https://saadmasoodd22.pythonanywhere.com"


def _fail(message):
    def application(environ, start_response):
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [message.encode("utf-8")]

    return application


try:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "cloudcare_wsgi",
        "/home/saadmasoodd22/wsgi.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    application = mod.application
except Exception:
    application = _fail(traceback.format_exc())
