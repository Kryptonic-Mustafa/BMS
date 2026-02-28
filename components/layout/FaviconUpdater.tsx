'use client';
import { useEffect } from 'react';

export function FaviconUpdater() {
  useEffect(() => {
    const updateIdentity = async () => {
      try {
        const res = await fetch('/api/admin/settings');
        const data = await res.json();
        
        if (data.site_favicon) {
          let link: HTMLLinkElement | null = document.querySelector("link[rel~='icon']");
          if (!link) {
            link = document.createElement('link');
            link.rel = 'icon';
            document.getElementsByTagName('head')[0].appendChild(link);
          }
          link.href = data.site_favicon;
        }

        if (data.site_name) {
          document.title = data.site_name;
        }
      } catch (e) {
        console.error("Failed to load site identity", e);
      }
    };

    updateIdentity();
  }, []);

  return null;
}