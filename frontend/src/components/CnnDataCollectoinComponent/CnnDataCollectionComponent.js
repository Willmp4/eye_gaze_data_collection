import React, { useEffect, useRef, useState } from "react";
import "./CnnDataCollectionComponent.css";
import useCamera from "../../hooks/useCamera";
import useCacheManager from "../../hooks/useCacheManager";
import useEventListeners from "../../hooks/useEventListeners";
import getCameraParameters from "../../utils/getCameraParameters";

function CnnDataCollectionComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const { cache, addToCache, processCache } = useCacheManager();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [isCapturing, setIsCapturing] = useState(false);
  const [isProcessingCache, setIsProcessingCache] = useState(false);

  const updateCursorPosition = (event) => {
    currentCursorPosition.current = { x: event.clientX, y: event.clientY };
  };

  const enqueueCapture = () => {
    console.log("enqueueCapture");
    if (!userId || isCapturing) return;

    setIsCapturing(true);

    captureImage()
      .then((blob) => {
        const { cameraMatrix, distCoeffs } = getCameraParameters(videoRef.current);

        addToCache({
          userId,
          cursorPosition: JSON.stringify(currentCursorPosition.current),
          cameraMatrix: JSON.stringify(cameraMatrix),
          distCoeffs: JSON.stringify(distCoeffs),
          blob,
        });

        setIsCapturing(false);
      })
      .catch((error) => {
        console.error("Error capturing image:", error);
        setIsCapturing(false);
      });
  };

  useEventListeners("mousemove", updateCursorPosition);
  useEventListeners("keydown", (event) => {
    if (event.keyCode === 32) {
      enqueueCapture();
    }
  });
  useEffect(() => {
    if (cache.length > 0 && !isProcessingCache) {
      setIsProcessingCache(true);
      processCache("https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image").finally(() => {
        setIsProcessingCache(false);
      });
    }
  }, [cache, processCache, isProcessingCache]);

  return (
    <div className={`camera-container ${isCapturing ? "processing" : ""}`}>
      <video ref={videoRef} className="video-feed" />
      {isCapturing && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CnnDataCollectionComponent;
