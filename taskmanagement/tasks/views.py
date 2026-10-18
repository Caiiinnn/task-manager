from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
import json

from .models import Task, Category, TaskChecklistItem
from .forms import TaskForm, CategoryForm, TaskChecklistItemForm


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)

    # Filtering
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if category_filter:
        tasks = tasks.filter(category__id=category_filter)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    categories = Category.objects.filter(user=request.user)

    context = {
        'tasks': tasks,
        'categories': categories,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'total_tasks': tasks.count(),
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = TaskForm(user=request.user)

    categories = Category.objects.filter(user=request.user)
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'categories': categories,
        'action': 'Create',
        'category_form': CategoryForm()
    })


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = TaskForm(user=request.user, instance=task)

    categories = Category.objects.filter(user=request.user)
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'categories': categories,
        'action': 'Update',
        'category_form': CategoryForm()
    })


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    checklist_items = task.checklist_items.all()
    checklist_form = TaskChecklistItemForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_checklist':
            checklist_form = TaskChecklistItemForm(request.POST)
            if checklist_form.is_valid():
                item = checklist_form.save(commit=False)
                item.task = task
                item.save()
                messages.success(request, 'Checklist item added.')
                return redirect('task_detail', pk=pk)

        elif action == 'toggle_checklist':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(TaskChecklistItem, id=item_id, task=task)
            item.is_done = not item.is_done
            item.save()
            return redirect('task_detail', pk=pk)

        elif action == 'delete_checklist':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(TaskChecklistItem, id=item_id, task=task)
            item.delete()
            return redirect('task_detail', pk=pk)

    completed_items = checklist_items.filter(is_done=True).count()
    total_items = checklist_items.count()

    context = {
        'task': task,
        'checklist_items': checklist_items,
        'checklist_form': checklist_form,
        'completed_items': completed_items,
        'total_items': total_items,
        'checklist_progress': int((completed_items / total_items * 100) if total_items > 0 else 0),
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': category.id,
                    'name': category.name,
                    'color': category.color
                })
            messages.success(request, f'Category "{category.name}" created!')
            return redirect('task_create')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
    return redirect('task_create')


@login_required
def progress_tracking(request):
    tasks = Task.objects.filter(user=request.user)
    now = timezone.now()

    # Categorize tasks
    overdue_tasks = [t for t in tasks if t.is_overdue]
    due_soon_tasks = [t for t in tasks if not t.is_overdue and t.due_date and (t.due_date - now).days <= 3 and t.status != 'completed']
    in_progress_tasks = tasks.filter(status='in_progress')
    completed_tasks = tasks.filter(status='completed')

    # Progress buckets
    progress_buckets = {
        'not_started': tasks.filter(status='todo').count(),
        'early': 0,
        'midway': 0,
        'almost_done': 0,
        'completed': completed_tasks.count(),
    }

    for task in tasks.exclude(status__in=['todo', 'completed']):
        p = task.progress
        if p < 30:
            progress_buckets['early'] += 1
        elif p < 70:
            progress_buckets['midway'] += 1
        else:
            progress_buckets['almost_done'] += 1

    context = {
        'tasks': tasks,
        'overdue_tasks': overdue_tasks,
        'due_soon_tasks': due_soon_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'progress_buckets': progress_buckets,
        'now': now,
        'total_tasks': tasks.count(),
        'overdue_count': len(overdue_tasks),
        'completion_rate': int((completed_tasks.count() / tasks.count() * 100) if tasks.count() > 0 else 0),
    }
    return render(request, 'tasks/progress_tracking.html', context)


@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user)
    now = timezone.now()

    total = tasks.count()
    completed = tasks.filter(status='completed').count()
    in_progress = tasks.filter(status='in_progress').count()
    todo = tasks.filter(status='todo').count()
    review = tasks.filter(status='review').count()
    overdue = sum(1 for t in tasks if t.is_overdue)

    completion_rate = int((completed / total * 100) if total > 0 else 0)

    # Priority breakdown
    priority_data = {
        'critical': tasks.filter(priority='critical').count(),
        'high': tasks.filter(priority='high').count(),
        'medium': tasks.filter(priority='medium').count(),
        'low': tasks.filter(priority='low').count(),
    }

    # Recent tasks
    recent_tasks = tasks.order_by('-created_at')[:5]

    # Upcoming deadlines
    upcoming = tasks.filter(
        due_date__gte=now,
        status__in=['todo', 'in_progress', 'review']
    ).order_by('due_date')[:5]

    # Category stats
    categories = Category.objects.filter(user=request.user).annotate(
        task_count=Count('tasks')
    )

    # Average progress of active tasks
    active_tasks = [t for t in tasks if t.status not in ['todo', 'completed']]
    avg_progress = int(sum(t.progress for t in active_tasks) / len(active_tasks)) if active_tasks else 0

    context = {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'todo': todo,
        'review': review,
        'overdue': overdue,
        'completion_rate': completion_rate,
        'priority_data': priority_data,
        'recent_tasks': recent_tasks,
        'upcoming': upcoming,
        'categories': categories,
        'avg_progress': avg_progress,
        'now': now,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def update_task_status(request, pk):
    """AJAX endpoint to update task status quickly."""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, user=request.user)
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            return JsonResponse({
                'success': True,
                'progress': task.progress,
                'status': task.status,
                'is_overdue': task.is_overdue
            })
    return JsonResponse({'success': False}, status=400)