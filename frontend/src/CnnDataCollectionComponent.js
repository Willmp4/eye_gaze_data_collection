import React, { useEffect, useRef, useState, useCallback } from "react";
import "./CameraComponent.css";
import useCamera from "./useCamera";
import sendImageToServer from "./sendImageToServer";
import getCameraParameters from "./getCameraParameters";
import { debounce } from "lodash";
import useCache from "./useCache";

function CameraComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [processing, setProcessing] = useState(null);
  const { cache, addToCache, clearCache } = useCache();
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);

  const processQueue = useCallback(async () => {
    if (isProcessingQueue || cache.length === 0) {
      return;
    }
    setIsProcessingQueue(true);
    const currentImage = cache[0];

    try {
      await sendImageToServer(
        [currentImage],
        "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image",
        clearCache
      );
    } catch (error) {
      console.error("Error processing image:", error);
    }

    setIsProcessingQueue(false);
  }, [cache, isProcessingQueue, clearCache]);

  useEffect(() => {
    processQueue();
  }, [cache, processQueue]);

  const captureAndProcessImage = async () => {
    if (processing || !userId) return;

    setProcessing("processing");
    try {
      const blob = await captureImage();
      const { cameraMatrix, distCoeffs } = getCameraParameters(videoRef.current);
      const imageData = {
        userId: userId,
        cursorPosition: JSON.stringify(currentCursorPosition.current),
        cameraMatrix: JSON.stringify(cameraMatrix),
        distCoeffs: JSON.stringify(distCoeffs),
        blob: blob,
      };

      addToCache(imageData);
      setProcessing("success");
    } catch (error) {
      console.log(error);
      setProcessing("error");
    } finally {
      setTimeout(() => setProcessing(null), 500);
    }
  };

  const debouncedCaptureAndProcessImage = debounce(captureAndProcessImage, 250);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.keyCode === 32) {
        debouncedCaptureAndProcessImage();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [debouncedCaptureAndProcessImage]);

  return (
    <div className={`camera-container ${processing}`}>
      <video ref={videoRef} className="video-feed" />
      {processing === "processing" && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CameraComponent;
