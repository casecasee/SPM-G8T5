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
  // Backend can return either { tasks: [...] } or { my_tasks: [...], team_tasks: {...} }
  if (Array.isArray(data.tasks)) return data.tasks;

  const mine = Array.isArray(data.my_tasks) ? data.my_tasks : [];
  const teamGroups = data.team_tasks ? Object.values(data.team_tasks) : [];
  const team = Array.isArray(teamGroups) ? teamGroups.flat() : [];
  return [...mine, ...team];
};

export const createTask = (payload) =>
  http('/tasks', { method: 'POST', body: JSON.stringify(payload) });

export const updateTaskProject = (taskId, projectId, owner) =>
  http(`/task/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify({ project_id: projectId, owner }),
  });


