#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.services import register_user
        try:
            user_id = register_user("test-runner@example.com", "000000", "password123")
            print("Created user id:", user_id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("Exception:", type(e).__name__, e)
except Exception as e:
    print("Failed to import app or create app:", type(e).__name__, e)
    sys.exit(1)


