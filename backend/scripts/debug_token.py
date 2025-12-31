from app import create_app
from app.config import Config
from app.extensions import db

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_SECRET_KEY = 'test-secret-key'


def run():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # minimal init
        from app.models import User, MembershipConfig, ModelPricing, Task
        for lvl in range(1, 6):
            db.session.add(MembershipConfig(level=lvl, name=f'T{lvl}', concurrency_limit=lvl, queue_priority=0))
        db.session.add(ModelPricing(model_key='sora-v2', base_cost=100.00, is_active=1))
        db.session.commit()

        import bcrypt, uuid
        pw = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
        admin = User(email='admin@example.com', password_hash=pw, balance=10000.0, level=5, role='admin', status=1)
        db.session.add(admin)
        pw2 = bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
        user = User(email='test@example.com', password_hash=pw2, balance=1000.0, level=1, role='user', status=1)
        db.session.add(user)
        db.session.commit()

        t = Task(id=str(uuid.uuid4()), user_id=user.id, model_name='sora-v2', prompt='Test', params={'duration':5}, status='pending', cost_points=100.0)
        db.session.add(t)
        db.session.commit()

        client = app.test_client()
        r = client.post('/api/auth/login', json={'email':'admin@example.com','password':'admin123'})
        print('login status', r.status_code)
        print('login body', r.get_json())
        token = r.get_json()['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        r2 = client.get(f'/api/tasks/{t.id}', headers=headers)
        print('access status', r2.status_code)
        try:
            print('access body', r2.get_json())
        except Exception:
            print('raw', r2.data)

if __name__ == '__main__':
    run()


