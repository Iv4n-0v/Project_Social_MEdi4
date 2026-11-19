const MAX_SIDE = 1024; // la foto se muestra a 96 px; 1024 sobra incluso en pantallas retina
const SKIP_BELOW = 200 * 1024; // si ya es pequeña, no se toca

export function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function toBlob(canvas, type, quality) {
  return new Promise((resolve) => canvas.toBlob(resolve, type, quality));
}

// Reduce la imagen a MAX_SIDE y la recomprime. Devuelve un File listo para subir.
export async function compressImage(file) {
  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch {
    throw new Error('No se pudo leer la imagen. Prueba con otra.');
  }
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  if (scale === 1 && file.size <= SKIP_BELOW) {
    bitmap.close();
    return file;
  }
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();

  // WEBP conserva la transparencia de los PNG; si el navegador no lo soporta, JPEG con fondo blanco
  let blob = await toBlob(canvas, 'image/webp', 0.82);
  let name = 'foto.webp';
  if (!blob || blob.type !== 'image/webp') {
    ctx.globalCompositeOperation = 'destination-over';
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    blob = await toBlob(canvas, 'image/jpeg', 0.85);
    name = 'foto.jpg';
  }
  if (!blob) throw new Error('No se pudo optimizar la imagen.');
  // Si por alguna razón quedó más pesada que la original, se sube la original
  if (blob.size >= file.size) return file;
  return new File([blob], name, { type: blob.type });
}