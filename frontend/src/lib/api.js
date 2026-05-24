export async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? ''

    if (contentType.includes('application/json')) {
      const payload = await response.json()
      throw new Error(payload.detail || `Request failed with status ${response.status}`)
    }

    const message = await response.text()
    throw new Error(message || `Request failed with status ${response.status}`)
  }

  return response.json()
}
