const BASE = 'http://localhost:5002';

async function http(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const listTasks = async () => {
  const data = await http('/tasks', { method: 'GET' });
  return data.tasks || [];
};

export const createTask = (payload) =>
  http('/tasks', { method: 'POST', body: JSON.stringify(payload) });

export const updateTaskProject = (taskId, projectId, owner) =>
  http(`/task/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify({ project_id: projectId, owner }),
  });


