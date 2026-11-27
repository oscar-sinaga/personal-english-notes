export const apiUrl = import.meta.env.BASE_URL + 'api';
export const skills = ['Writing', 'Speaking', 'Reading', 'Listening', 'Credit Risk'];
export const contexts = ['Study', 'Work', 'Personal'];
export const statuses = { draft: 'Draft', completed: 'Completed' };
export const MIN_BOOK_EXCERPT = 10;
export const MAX_BOOK_EXCERPT = 4000;

export async function requestJson(path, options) {
  const response = await fetch(apiUrl + path, options);
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) {
    const detail = Array.isArray(data?.detail) ? data.detail[0]?.msg : data?.detail;
    throw new Error(detail || (response.status === 401
      ? 'Open the tracker again from ACC. Your current draft is still in this tab.'
      : 'Could not complete the request.'));
  }
  return data;
}

export function saveEntry(id, data) {
  return requestJson('/practice/' + id, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}
