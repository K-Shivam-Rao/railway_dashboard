export async function apiFetch<T>(
  endpoint: string,
  init?: RequestInit
): Promise<T> {
  const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API Error: ${response.status}`);
  }

  return response.json();
}