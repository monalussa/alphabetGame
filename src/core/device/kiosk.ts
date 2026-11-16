interface KeyboardLock {
  lock?: () => Promise<void>;
  unlock?: () => void;
}

function keyboardApi(): KeyboardLock | undefined {
  return (navigator as Navigator & { keyboard?: KeyboardLock }).keyboard;
}

/** Fullscreen + keyboard lock (Chromium) so small hands cannot leave the game by accident. */
export async function enterKioskMode(): Promise<void> {
  try {
    if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
    await keyboardApi()?.lock?.();
  } catch (error) {
    console.warn('Kiosk mode not available', error);
  }
}

export async function exitKioskMode(): Promise<void> {
  keyboardApi()?.unlock?.();
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
  } catch (error) {
    console.warn('Could not leave fullscreen', error);
  }
}
