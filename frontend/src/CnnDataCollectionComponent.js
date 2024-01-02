import React, { useEffect, useRef, useState, useCallback } from "react";
import "./CameraComponent.css";
import useCamera from "./useCamera";
import sendImageToServer from "./sendImageToServer";
import getCameraParameters from "./getCameraParameters";
import useCache from "./useCache";

function CameraComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [isCapturing, setIsCapturing] = useState(false);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);
  const { cache, addToCache, removeFromCache } = useCache();

  const updateCursorPosition = useCallback((event) => {
    currentCursorPosition.current = { x: event.clientX, y: event.clientY };
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", updateCursorPosition);
    return () => {
      window.removeEventListener("mousemove", updateCursorPosition);
    };
  }, [updateCursorPosition]);

  const captureImageRequest = useCallback(async () => {
    if (isCapturing || !userId) return;

    setIsCapturing(true);
    try {
      const blob = await captureImage();
      const { cameraMatrix, distCoeffs } = getCameraParameters(videoRef.current);
      const currentCursorPos = currentCursorPosition.current;

      const imageData = {
        userId,
        cursorPosition: JSON.stringify(currentCursorPos),
        cameraMatrix: JSON.stringify(cameraMatrix),
        distCoeffs: JSON.stringify(distCoeffs),
        blob,
      };

      addToCache(imageData);
    } catch (error) {
      console.log(error);
    } finally {
      setIsCapturing(false);
    }
  }, [isCapturing, userId, captureImage, videoRef, addToCache]);

  const processQueue = useCallback(async () => {
    if (isProcessingQueue || cache.length === 0) return;
    setIsProcessingQueue(true);

    // Clone the current cache for processing
    const currentCache = [...cache];

    for (let i = 0; i < currentCache.length; i++) {
      try {
        await sendImageToServer([currentCache[i]], "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image");
        removeFromCache(currentCache[i]);
      } catch (error) {
        console.error("Error processing image:", error);
      }
    }

    setIsProcessingQueue(false);
  }, [cache, isProcessingQueue, removeFromCache]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.keyCode === 32) {
        captureImageRequest();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [captureImageRequest]);

  useEffect(() => {
    processQueue();
  }, [processQueue, cache]);

  return (
    <div className={`camera-container ${isCapturing ? "processing" : ""}`}>
      <video ref={videoRef} className="video-feed" />
      {isCapturing && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CameraComponent;
