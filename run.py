from newshound.app import app, manager
from newshound.config import ensure_dirs
import os

ensure_dirs()
manager.start()
app.run(host="0.0.0.0", port=int(os.environ.get("NEWSHOUND_PORT","8091")), threaded=True)
