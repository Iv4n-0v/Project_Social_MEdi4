import { useState } from 'react';
import { friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { PLATFORM_LABELS, SOURCE_LABELS, formatFollowers } from './venture';

export const PLACEHOLDERS = {
  instagram: 'https://instagram.com/tu_usuario',
  facebook: 'https://facebook.com/tu_pagina',
  tiktok: 'https://tiktok.com/@tu_usuario',
  whatsapp: 'https://wa.me/573001234567',
  youtube: 'https://youtube.com/@tu_canal',
};

export default function SocialRow({ platform, current, onSaved, onError }) {
  const [url, setUrl] = useState(current ? current.url : '');
  const [followers, setFollowers] = useState('');
  const [busy, setBusy] = useState(false);

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    onError('');
    try {
      const body = { url: url.trim() };
      if (followers !== '') body.followers = Number(followers);
      onSaved(await venturesApi.setSocial(platform, body), `${PLATFORM_LABELS[platform]} guardado`);
      setFollowers('');
    } catch (err) {
      onError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function unlink() {
    setBusy(true);
    onError('');
    try {
      const v = await venturesApi.removeSocial(platform);
      setUrl('');
      onSaved(v, `${PLATFORM_LABELS[platform]} desvinculado`);
    } catch (err) {
      onError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="social-row" onSubmit={save}>
      <strong>{PLATFORM_LABELS[platform]}</strong>
      <input
        type="url"
        aria-label={`Enlace de ${PLATFORM_LABELS[platform]}`}
        placeholder={PLACEHOLDERS[platform]}
        required
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      {platform !== 'whatsapp' && (
        <input
          type="number"
          min="0"
          aria-label={`Seguidores de ${PLATFORM_LABELS[platform]} (opcional)`}
          placeholder="Seguidores (opcional)"
          value={followers}
          onChange={(e) => setFollowers(e.target.value)}
        />
      )}
      <div className="row">
        <button className="btn small primary" disabled={busy}>{current ? 'Actualizar' : 'Vincular'}</button>
        {current && <button type="button" className="btn small danger" disabled={busy} onClick={unlink}>Desvincular</button>}
      </div>
      {current && current.followers != null && (
        <small className="muted">
          Último dato: {formatFollowers(current.followers)} seguidores ({SOURCE_LABELS[current.followers_source] || current.followers_source}
          {current.followers_updated_at ? `, ${new Date(current.followers_updated_at).toLocaleDateString('es-CO')}` : ''})
        </small>
      )}
    </form>
  );
}
