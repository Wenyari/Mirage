#!/usr/bin/env python3
"""
Direct test of register_user function to isolate the error
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.services.auth_service import register_user

def test_register_direct():
    app = create_app()
    with app.app_context():
        try:
            print("Testing register_user function directly...")
            user_id = register_user("2536331283@qq.com", "494023", "wanglei123.")
            print(f"Success! User ID: {user_id}")
        except Exception as e:
            print(f"Error in register_user: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_register_direct()
