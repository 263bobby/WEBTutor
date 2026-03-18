from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import User, TutorProfile, Availability, Booking, Subject

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            flash('Trang này chỉ dành cho học viên.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Tìm kiếm gia sư ───────────────────────────────────────
@student_bp.route('/search')
@login_required
@student_required
def search():
    subject_id = request.args.get('subject_id', type=int)
    subjects   = Subject.query.filter_by(is_active=True).all()

    query = TutorProfile.query.join(User).filter(User.is_active == True)
    if subject_id:
        query = query.filter(TutorProfile.subject_id == subject_id)

    tutors = query.all()
    return render_template('student/search.html',
                           tutors=tutors,
                           subjects=subjects,
                           selected_subject=subject_id)


# ── Hồ sơ gia sư & lịch rảnh ─────────────────────────────
@student_bp.route('/tutor/<int:tutor_id>')
@login_required
@student_required
def tutor_detail(tutor_id):
    from datetime import date
    tutor_user = User.query.filter_by(id=tutor_id, role='tutor', is_active=True).first_or_404()
    slots = Availability.query.filter(
        Availability.tutor_id == tutor_id,
        Availability.avail_date >= date.today(),
        Availability.is_booked == False
    ).order_by(Availability.avail_date, Availability.start_time).all()
    return render_template('student/tutor_detail.html', tutor=tutor_user, slots=slots)


# ── Đặt lịch ──────────────────────────────────────────────
@student_bp.route('/book/<int:avail_id>', methods=['POST'])
@login_required
@student_required
def book(avail_id):
    slot = Availability.query.get_or_404(avail_id)

    if slot.is_booked:
        flash('Slot này đã được đặt rồi, vui lòng chọn slot khác.', 'danger')
        return redirect(url_for('student.tutor_detail', tutor_id=slot.tutor_id))

    # Kiểm tra học viên chưa đặt slot này
    existing = Booking.query.filter_by(
        student_id=current_user.id, avail_id=avail_id
    ).filter(Booking.status.in_(['pending', 'confirmed'])).first()
    if existing:
        flash('Bạn đã đặt slot này rồi.', 'warning')
        return redirect(url_for('student.tutor_detail', tutor_id=slot.tutor_id))

    note = request.form.get('note', '').strip()

    # Tạo booking
    booking = Booking(
        student_id=current_user.id,
        tutor_id=slot.tutor_id,
        avail_id=avail_id,
        note=note,
        status='pending'
    )
    slot.is_booked = True
    db.session.add(booking)
    db.session.commit()

    flash('Đặt lịch thành công! Vui lòng chờ gia sư xác nhận.', 'success')
    return redirect(url_for('student.my_bookings'))


# ── Lịch sử đặt lịch ──────────────────────────────────────
@student_bp.route('/my-bookings')
@login_required
@student_required
def my_bookings():
    bookings = Booking.query.filter_by(student_id=current_user.id)\
                            .order_by(Booking.created_at.desc()).all()
    return render_template('student/my_bookings.html', bookings=bookings)


# ── Hủy lịch ──────────────────────────────────────────────
@student_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
@student_required
def cancel(booking_id):
    booking = Booking.query.filter_by(id=booking_id, student_id=current_user.id).first_or_404()

    if booking.status not in ('pending',):
        flash('Chỉ có thể hủy đơn đang chờ xác nhận.', 'danger')
        return redirect(url_for('student.my_bookings'))

    booking.status = 'cancelled'
    booking.availability.is_booked = False
    db.session.commit()
    flash('Đã hủy lịch thành công.', 'info')
    return redirect(url_for('student.my_bookings'))

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    pending_count   = Booking.query.filter_by(student_id=current_user.id, status='pending').count()
    confirmed_count = Booking.query.filter_by(student_id=current_user.id, status='confirmed').count()
    completed_count = Booking.query.filter_by(student_id=current_user.id, status='completed').count()
    upcoming = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.status.in_(['pending', 'confirmed'])
    ).order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('student/dashboard.html',
                           active_tab='overview',
                           pending_count=pending_count,
                           confirmed_count=confirmed_count,
                           completed_count=completed_count,
                           upcoming_bookings=upcoming)