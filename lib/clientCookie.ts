export function getClientPolicy() {
  if (typeof document === 'undefined') return { role: '', permissions: [] };
  
  const match = document.cookie.match(new RegExp('(^| )client_policy=([^;]+)'));
  if (match) {
    try {
        // Decode URI component because cookies are often encoded
        const jsonStr = decodeURIComponent(match[2]);
        return JSON.parse(jsonStr);
    } catch (e) {
        return { role: '', permissions: [] };
    }
  }
  return { role: '', permissions: [] };
}