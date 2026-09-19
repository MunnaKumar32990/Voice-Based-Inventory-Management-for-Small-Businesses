function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined') return undefined;
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'];
  for (const c of candidates) {
    try {
      if (MediaRecorder.isTypeSupported(c)) return c;
    } catch {
      /* ignore */
    }
  }
  return undefined;
}

export const startRecording = async (): Promise<{ stop: () => Promise<Blob> }> => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = pickMimeType();
    const mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
    const audioChunks: Blob[] = [];
    let settled = false;

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    const cleanup = () => {
      stream.getTracks().forEach((track) => track.stop());
    };

    const buildBlob = () => new Blob(audioChunks, { type: mediaRecorder.mimeType || mimeType || 'audio/webm' });

    // Auto-stop after 12 seconds as a safeguard — resolve through the same path
    let autoStop: number | undefined;
    const stopPromise = new Promise<Blob>((resolve) => {
      mediaRecorder.onstop = () => {
        if (settled) return;
        settled = true;
        if (autoStop !== undefined) window.clearTimeout(autoStop);
        cleanup();
        resolve(buildBlob());
      };
      autoStop = window.setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          try {
            mediaRecorder.stop();
          } catch {
            if (!settled) {
              settled = true;
              cleanup();
              resolve(buildBlob());
            }
          }
        }
      }, 12000);
    });
    // Attach handler early so auto-stop resolves; manual stop() awaits same promise
    void stopPromise.catch(() => undefined);

    mediaRecorder.start();

    return {
      stop: () => {
        if (mediaRecorder.state === 'recording') {
          try {
            mediaRecorder.stop();
          } catch {
            if (!settled) {
              settled = true;
              if (autoStop !== undefined) window.clearTimeout(autoStop);
              cleanup();
              return Promise.resolve(buildBlob());
            }
          }
        } else if (!settled) {
          settled = true;
          if (autoStop !== undefined) window.clearTimeout(autoStop);
          cleanup();
          return Promise.resolve(buildBlob());
        }
        return stopPromise;
      },
    };
  } catch (error) {
    console.error('Error starting recording:', error);
    throw error;
  }
};
