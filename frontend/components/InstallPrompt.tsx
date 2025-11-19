'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstall, setShowInstall] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Check if iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    setIsIOS(iOS);

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return; // Already installed
    }

    // Check if dismissed recently
    const dismissed = localStorage.getItem('install-prompt-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed);
      const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) {
        return; // Don't show for 7 days after dismissal
      }
    }

    // Listen for beforeinstallprompt (Android/Desktop)
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Show iOS instructions after 3 seconds
    if (iOS) {
      setTimeout(() => setShowInstall(true), 3000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      setDeferredPrompt(null);
      setShowInstall(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('install-prompt-dismissed', Date.now().toString());
    setShowInstall(false);
  };

  if (!showInstall) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 bg-white rounded-lg shadow-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {isIOS ? (
            <div>
              <p className="font-semibold mb-1">Install VenturePulse</p>
              <p className="text-sm text-gray-600">
                Tap <span className="inline-block font-mono">⎙</span> then "Add to Home Screen"
              </p>
            </div>
          ) : (
            <div>
              <p className="font-semibold mb-1 flex items-center gap-2">
                Install VenturePulse
                <Badge variant="success">Free</Badge>
              </p>
              <p className="text-sm text-gray-600">
                Install for offline access and faster loading
              </p>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          {!isIOS && deferredPrompt && (
            <Button size="sm" onClick={handleInstallClick}>
              Install
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={handleDismiss}>
            ×
          </Button>
        </div>
      </div>
    </div>
  );
}
