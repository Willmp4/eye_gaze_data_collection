import React, { useEffect, useRef, useState, useCallback } from "react";
import "./CameraComponent.css";
import useCamera from "./useCamera";
import sendImageToServer from "./sendImageToServer";
import getCameraParameters from "./getCameraParameters";
import useCache from "./useCache";
import { debounce } from "lodash";

function CameraComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [processing, setProcessing] = useState(null);
  const { cache, addToCache, clearCache } = useCache();
  const [isCapturing, setIsCapturing] = useState(false);
  const maxCacheSize = 10;

  const handleSubmitCache = useCallback(async () => {
    await sendImageToServer(cache, "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image", clearCache);
  }, [cache, clearCache]);

  const captureAndProcessImage = async () => {
    if (isCapturing || !userId) return;

    setIsCapturing(true);
    setProcessing("processing");

    try {
      const blob = await captureImage();
      const { cameraMatrix, distCoeffs } = getCameraParameters(videoRef.current);
      const cacheItem = {
        userId: userId,
        cursorPosition: JSON.stringify(currentCursorPosition.current),
        cameraMatrix: JSON.stringify(cameraMatrix),
        distCoeffs: JSON.stringify(distCoeffs),
        blob: blob,
      };

      addToCache(cacheItem);
      setProcessing("success");
    } catch (error) {
      console.log(error);
      setProcessing("error");
    } finally {
      setIsCapturing(false);
      setTimeout(() => setProcessing(null), 500);
      console.log(cache.length);
    }
  };

  // Debounced function
  const debouncedCaptureAndProcessImage = debounce(captureAndProcessImage, 500);

  const handleKeyDown = async (event) => {
    if (event.keyCode === 32) {
      debouncedCaptureAndProcessImage();
    }
  };

  useEffect(() => {
    const handleBeforeUnload = async (e) => {
      if (cache.length > 0) {
        e.preventDefault();
        await handleSubmitCache();
      }
    };

    const updateCursorPosition = (event) => {
      currentCursorPosition.current = { x: event.screenX, y: event.screenY };
    };

    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousemove", updateCursorPosition);
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      document.removeEventListener("mousemove", updateCursorPosition);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [handleKeyDown, handleSubmitCache, cache.length]);

  useEffect(() => {
    if (cache.length >= maxCacheSize) {
      handleSubmitCache();
    }
  }, [cache.length, handleSubmitCache]);

  return (
    <div className={`camera-container ${processing}`}>
      <video ref={videoRef} className="video-feed" />
      {processing === "processing" && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CameraComponent;
