// Logos esquemáticos de cada red, en el color de la marca. Decorativos: el nombre va en el texto.
const BRAND = {
  instagram: '#e1306c',
  facebook: '#1877f2',
  tiktok: '#111111',
  whatsapp: '#25d366',
  youtube: '#ff0000',
};

function Glyph({ platform }) {
  switch (platform) {
    case 'instagram':
      return (
        <>
          <rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" strokeWidth="2" />
          <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="2" />
          <circle cx="17.2" cy="6.8" r="1.2" fill="currentColor" />
        </>
      );
    case 'facebook':
      return (
        <>
          <circle cx="12" cy="12" r="10" fill="currentColor" />
          <path d="M13.2 21v-7h2.4l.4-2.8h-2.8V9.5c0-.8.3-1.3 1.4-1.3H16V5.7c-.3 0-1.1-.1-2.1-.1-2.1 0-3.5 1.3-3.5 3.6v2H8v2.8h2.4V21z" fill="#fff" />
        </>
      );
    case 'tiktok':
      return (
        <path
          d="M14 3v11.2a3.2 3.2 0 1 1-3.2-3.2M14 3c.3 2.4 1.9 4 4.5 4.2"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      );
    case 'whatsapp':
      return (
        <>
          <path d="M3 21l1.4-4.6A9 9 0 1 1 8 20z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
          <path d="M9 8.5c0 3.6 2.9 6.5 6.5 6.5l1-1.5-2.2-1-1 .8c-1-.4-1.8-1.2-2.2-2.2l.8-1-1-2.2z" fill="currentColor" />
        </>
      );
    case 'youtube':
      return (
        <>
          <rect x="2" y="5" width="20" height="14" rx="4" fill="currentColor" />
          <path d="M10 9l5 3-5 3z" fill="#fff" />
        </>
      );
    default:
      return <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="2" />;
  }
}

export default function SocialIcon({ platform, size = 20 }) {
  return (
    <svg
      className="social-icon"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      style={{ color: BRAND[platform] || 'var(--color-muted)' }}
      aria-hidden="true"
      focusable="false"
    >
      <Glyph platform={platform} />
    </svg>
  );
}