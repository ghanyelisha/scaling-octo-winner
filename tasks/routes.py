from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Task
from tasks import tasks_bp


def _parse_deadline(value):
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


@tasks_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    sort = request.args.get('sort', 'deadline')

    query = Task.query.filter_by(user_id=current_user.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)

    if sort == 'deadline':
        query = query.order_by(Task.deadline.asc())
    elif sort == 'priority':
        priority_order = db.case(
            (Task.priority == 'high', 1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low', 3),
            else_=4
        )
        query = query.order_by(priority_order)
    elif sort == 'created':
        query = query.order_by(Task.created_at.desc())

    tasks = query.all()

    now = datetime.now(timezone.utc)
    for task in tasks:
        if task.status != Task.STATUS_COMPLETED and task.deadline_utc < now:
            task.status = Task.STATUS_OVERDUE
    db.session.commit()

    return render_template('tasks/index.html', tasks=tasks,
                           status_filter=status_filter, priority_filter=priority_filter,
                           sort=sort)


@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        deadline_str = request.form.get('deadline', '')
        priority = request.form.get('priority', Task.PRIORITY_MEDIUM)
        status = request.form.get('status', Task.STATUS_PENDING)

        error = None
        if not title:
            error = 'Title is required.'
        elif not deadline_str:
            error = 'Deadline is required.'

        deadline = _parse_deadline(deadline_str) if deadline_str else None
        if not error and deadline is None:
            error = 'Invalid deadline format.'

        if error:
            flash(error, 'danger')
        else:
            task = Task(
                user_id=current_user.id,
                title=title,
                description=description,
                deadline=deadline,
                priority=priority,
                status=status,
            )
            db.session.add(task)
            db.session.commit()
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks.detail', task_id=task.id))

    return render_template('tasks/create.html')


@tasks_bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    return render_template('tasks/detail.html', task=task)


@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        deadline_str = request.form.get('deadline', '')
        priority = request.form.get('priority', task.priority)
        status = request.form.get('status', task.status)

        error = None
        if not title:
            error = 'Title is required.'
        elif not deadline_str:
            error = 'Deadline is required.'

        deadline = _parse_deadline(deadline_str) if deadline_str else None
        if not error and deadline is None:
            error = 'Invalid deadline format.'

        if error:
            flash(error, 'danger')
        else:
            task.title = title
            task.description = description
            task.deadline = deadline
            task.priority = priority
            task.status = status
            task.updated_at = datetime.now(timezone.utc)
            # Reset reminder flags if deadline changed
            task.reminder_24h_sent = False
            task.reminder_1h_sent = False
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('tasks.detail', task_id=task.id))

    deadline_fmt = task.deadline.strftime('%Y-%m-%dT%H:%M') if task.deadline else ''
    return render_template('tasks/edit.html', task=task, deadline_fmt=deadline_fmt)


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'info')
    return redirect(url_for('tasks.index'))


@tasks_bp.route('/<int:task_id>/status', methods=['POST'])
@login_required
def update_status(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    new_status = request.form.get('status')
    if new_status in (Task.STATUS_PENDING, Task.STATUS_IN_PROGRESS,
                      Task.STATUS_COMPLETED, Task.STATUS_OVERDUE):
        task.status = new_status
        db.session.commit()
    return redirect(request.referrer or url_for('tasks.index'))


@tasks_bp.route('/<int:task_id>/countdown')
@login_required
def countdown_data(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'seconds': task.seconds_until_deadline,
        'title': task.title,
        'deadline': task.deadline.isoformat(),
        'is_overdue': task.is_overdue,
    })
