import { useState } from 'react';
import { motion } from 'framer-motion';
import { getHubUrl, getAuthHeaders } from '../store/hubClient';

/**
 * Upload links are signed and expire, and the old link is saved in the chat.
 * When an image fails to load, ask the hub for a fresh link once and retry.
 */
async function fetchFreshUrl(oldUrl: string): Promise<string | null> {
  try {
    const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
    const res = await fetch(`${getHubUrl()}/api/uploads/sign`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ url: oldUrl }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return typeof data.url === 'string' ? data.url : null;
  } catch {
    return null;
  }
}

export function AttachmentImage({ url }: { url: string }) {
  const [src, setSrc] = useState(url);
  const [retried, setRetried] = useState(false);
  const [failed, setFailed] = useState(false);

  const handleError = async () => {
    // Only uploads can be re-signed; data: URLs and other links are left alone.
    if (retried || !url.includes('/uploads/')) {
      setFailed(true);
      return;
    }
    setRetried(true);
    const fresh = await fetchFreshUrl(url);
    if (fresh) setSrc(fresh);
    else setFailed(true);
  };

  if (failed) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-[12px] text-slate-400">
        Image is no longer available
      </div>
    );
  }

  return (
    <motion.img
      whileHover={{ scale: 1.02 }}
      src={src}
      alt="Attachment"
      className="rounded-2xl border border-white/10 shadow-lg cursor-pointer max-h-48 object-cover"
      onClick={() => window.open(src, '_blank')}
      onError={handleError}
    />
  );
}
