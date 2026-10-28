export class ApiError extends Error {
  constructor(status, message, details) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export class NetworkError extends Error {
  constructor(message = 'No se pudo conectar con el servidor') {
    super(message);
    this.name = 'NetworkError';
  }
}

export function friendlyMessage(err) {
  if (err instanceof NetworkError) return err.message;
  if (err instanceof ApiError) {
    if (err.status === 404) return 'No se encontró el registro.';
    if (err.status === 422) return err.message || 'Datos inválidos.';
    if (err.status === 503) return err.message || 'El servicio no está disponible.';
    return err.message || `Error ${err.status}`;
  }
  return 'Ocurrió un error inesperado.';
}
