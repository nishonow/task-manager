async function fetchTasks() {
    const taskList = document.getElementById('task-list');
    if (!taskList) return;
    try {
        const response = await fetch('/api/tasks/');
        if (!response.ok) {
            if (response.status === 401) window.location.href = '/login';
            throw new Error('Failed to fetch tasks');
        }
        const tasks = await response.json();
        taskList.innerHTML = '';
        tasks.forEach(task => {
            const li = document.createElement('li');
            li.className = `task-item bg-white p-3 rounded-md shadow-sm flex justify-between items-center ${task.completed ? 'completed' : ''}`;
            const title = document.createElement('h3');
            title.className = "text-base font-medium text-gray-800";
            title.textContent = task.title;
            if (task.completed) title.style.textDecoration = 'line-through';
            const desc = document.createElement('p');
            desc.className = "text-sm text-gray-600";
            desc.textContent = task.description || '';
            const div1 = document.createElement('div');
            div1.appendChild(title);
            div1.appendChild(desc);
            const btnComplete = document.createElement('button');
            btnComplete.className = "bg-green-500 text-white px-2 py-1 rounded-md hover:bg-green-600 transition text-sm";
            btnComplete.textContent = task.completed ? 'Restore' : 'Complete';
            btnComplete.onclick = () => toggleTask(task.id, !task.completed);
            const btnDelete = document.createElement('button');
            btnDelete.className = "bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600 transition text-sm";
            btnDelete.textContent = 'Delete';
            btnDelete.onclick = () => deleteTask(task.id);
            const div2 = document.createElement('div');
            div2.className = "space-x-2";
            div2.appendChild(btnComplete);
            div2.appendChild(btnDelete);
            li.appendChild(div1);
            li.appendChild(div2);
            taskList.appendChild(li);
        });
    } catch (error) {
        showToast('Failed to load tasks', 'error');
        console.error('Error fetching tasks:', error);
    }
}

async function addTask() {
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    if (!title) {
        showToast('Title is required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/tasks/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description })
        });
        if (!response.ok) throw new Error('Failed to add task');
        document.getElementById('title').value = '';
        document.getElementById('description').value = '';
        showToast('Task added successfully', 'success');
        fetchTasks();
    } catch (error) {
        showToast('Failed to add task', 'error');
        console.error('Error adding task:', error);
    }
}

async function toggleTask(id, completed) {
    try {
        const response = await fetch(`/api/tasks/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completed })
        });
        if (!response.ok) throw new Error('Failed to toggle task');
        showToast(`Task ${completed ? 'completed' : 'restored'}`, 'success');
        fetchTasks();
    } catch (error) {
        showToast('Failed to toggle task', 'error');
        console.error('Error toggling task:', error);
    }
}

async function deleteTask(id) {
    try {
        const response = await fetch(`/api/tasks/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete task');
        showToast('Task deleted successfully', 'success');
        fetchTasks();
    } catch (error) {
        showToast('Failed to delete task', 'error');
        console.error('Error deleting task:', error);
    }
}

function showToast(message, type) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `fixed bottom-4 right-4 p-3 rounded-md shadow-md text-white ${type}`;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

document.addEventListener('DOMContentLoaded', fetchTasks);