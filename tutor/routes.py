from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import Booking, Availability
from datetime import date

tutor_bp = Blueprint('tutor', __name__)


def tutor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_tutor():
            flash('Trang này chỉ dành cho gia sư.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard: xem tất cả đơn ─────────────────────────────
@tutor_bp.route('/dashboard')
@login_required
@tutor_required
def dashboard():
    pending   = Booking.query.filter_by(tutor_id=current_user.id, status='pending')\
                             .order_by(Booking.created_at.desc()).all()
    confirmed = Booking.query.filter_by(tutor_id=current_user.id, status='confirmed')\
                             .order_by(Booking.created_at.desc()).all()
    completed = Booking.query.filter_by(tutor_id=current_user.id, status='completed')\
                             .order_by(Booking.created_at.desc()).limit(10).all()
    return render_template('tutor/dashboard.html',
                           pending=pending,
                           confirmed=confirmed,
                           completed=completed)


# ── Chấp nhận đơn ─────────────────────────────────────────
@tutor_bp.route('/accept/<int:booking_id>', methods=['POST'])
@login_required
@tutor_required
def accept(booking_id):
    booking = Booking.query.filter_by(id=booking_id, tutor_id=current_user.id,
                                      status='pending').first_or_404()
    booking.status = 'confirmed'
    db.session.commit()
    flash(f'Đã xác nhận lịch học với {booking.student.full_name}.', 'success')
    return redirect(url_for('tutor.dashboard'))


# ── Từ chối đơn ───────────────────────────────────────────
@tutor_bp.route('/reject/<int:booking_id>', methods=['POST'])
@login_required
@tutor_required
def reject(booking_id):
    booking = Booking.query.filter_by(id=booking_id, tutor_id=current_user.id,
                                      status='pending').first_or_404()
    booking.status = 'cancelled'
    booking.availability.is_booked = False   # mở lại slot
    db.session.commit()
    flash('Đã từ chối đơn đặt lịch.', 'info')
    return redirect(url_for('tutor.dashboard'))


# ── Hoàn thành buổi dạy ───────────────────────────────────
@tutor_bp.route('/complete/<int:booking_id>', methods=['POST'])
@login_required
@tutor_required
def complete(booking_id):
    booking = Booking.query.filter_by(id=booking_id, tutor_id=current_user.id,
                                      status='confirmed').first_or_404()
    booking.status = 'completed'
    db.session.commit()
    flash('Buổi dạy đã hoàn thành!', 'success')
    return redirect(url_for('tutor.dashboard'))


# ── Quản lý lịch rảnh ─────────────────────────────────────
@tutor_bp.route('/schedule')
@login_required
@tutor_required
def schedule():
    slots = Availability.query.filter(
        Availability.tutor_id == current_user.id,
        Availability.avail_date >= date.today()
    ).order_by(Availability.avail_date, Availability.start_time).all()
    return render_template('tutor/schedule.html', slots=slots)


# ── Thêm slot rảnh ────────────────────────────────────────
@tutor_bp.route('/schedule/add', methods=['POST'])
@login_required
@tutor_required
def add_slot():
    avail_date = request.form.get('avail_date')
    start_time = request.form.get('start_time')
    end_time   = request.form.get('end_time')

    if not avail_date or not start_time or not end_time:
        flash('Vui lòng điền đầy đủ thông tin slot.', 'danger')
        return redirect(url_for('tutor.schedule'))

    # Kiểm tra trùng slot
    existing = Availability.query.filter_by(
        tutor_id=current_user.id,
        avail_date=avail_date,
        start_time=start_time
    ).first()
    if existing:
        flash('Bạn đã có slot vào thời gian này rồi.', 'warning')
        return redirect(url_for('tutor.schedule'))

    slot = Availability(
        tutor_id=current_user.id,
        avail_date=avail_date,
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(slot)
    db.session.commit()
    flash('Đã thêm slot lịch rảnh.', 'success')
    return redirect(url_for('tutor.schedule'))


# ── Xóa slot rảnh ─────────────────────────────────────────
@tutor_bp.route('/schedule/delete/<int:slot_id>', methods=['POST'])
@login_required
@tutor_required
def delete_slot(slot_id):
    slot = Availability.query.filter_by(id=slot_id, tutor_id=current_user.id).first_or_404()
    if slot.is_booked:
        flash('Không thể xóa slot đã có người đặt.', 'danger')
    else:
        db.session.delete(slot)
        db.session.commit()
        flash('Đã xóa slot.', 'info')
    return redirect(url_for('tutor.schedule'))