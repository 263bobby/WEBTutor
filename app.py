from flask import Flask, redirect, url_for
from urllib.parse import quote_plus
from extensions import db, login_manager

# ── Cấu hình kết nối SQL Server ───────────────────────────
SERVER_NAME = r'ADMIN\SQLEXPRESS'
DB_NAME     = 'tutor_connect'
DB_USER     = 'flask_user'
DB_PASSWORD = '123456'

conn_str = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={SERVER_NAME};'
    f'DATABASE={DB_NAME};'
    f'UID={DB_USER};'
    f'PWD={DB_PASSWORD};'
)


def create_app():
    app = Flask(__name__)

    # ── Cấu hình ──────────────────────────────────────────
    app.config['SECRET_KEY'] = 'khoa-bi-mat-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mssql+pyodbc:///?odbc_connect=' + quote_plus(conn_str)
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Extensions ────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập.'
    login_manager.login_message_category = 'warning'

    # ── Đăng ký Blueprints ────────────────────────────────
    from auth.routes import auth_bp
    from student.routes import student_bp
    from tutor.routes import tutor_bp
    from admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(tutor_bp,   url_prefix='/tutor')
    app.register_blueprint(admin_bp,   url_prefix='/admin')

    # ── Khởi động ─────────────────────────────────────────
    with app.app_context():
        fix_passwords()

    return app


def fix_passwords():
    """Cập nhật password_hash thật cho tài khoản PLACEHOLDER."""
    from models import User
    from werkzeug.security import generate_password_hash
    try:
        placeholders = User.query.filter_by(password_hash='PLACEHOLDER').all()
        if not placeholders:
            print('✅ Kết nối SQL Server thành công!')
            return
        for u in placeholders:
            u.password_hash = generate_password_hash('123456')
        db.session.commit()
        print(f'✅ Đã cập nhật password cho {len(placeholders)} tài khoản.')
    except Exception as e:
        print(f'❌ Lỗi kết nối DB: {e}')


app = create_app()


# ── Route trang chủ: tự redirect theo role ────────────────
@app.route('/')
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        if current_user.is_admin():   return redirect(url_for('admin.dashboard'))
        if current_user.is_tutor():   return redirect(url_for('tutor.dashboard'))
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


# ── Route test kết nối DB ─────────────────────────────────
@app.route('/test-db')
def test_db():
    from models import User, Subject
    try:
        users    = User.query.count()
        subjects = Subject.query.count()
        return f'✅ SQL Server OK! {users} người dùng — {subjects} môn học.'
    except Exception as e:
        return f'❌ Lỗi: {str(e)}'


if __name__ == '__main__':
    app.run(debug=True)