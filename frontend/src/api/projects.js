const BASE = 'http://localhost:8001'; // hardcoded for local dev

async function http(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const getProjects = () => http('/projects', { method: 'GET' });
export const createProject = (payload) =>
  http('/projects', { method: 'POST', body: JSON.stringify(payload) });