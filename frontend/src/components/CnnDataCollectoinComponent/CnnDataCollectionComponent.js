import React, { useRef, useState } from "react";
import "./CnnDataCollectionComponent.css";
import useCamera from "../../hooks/useCamera";
import useEventListeners from "../../hooks/useEventListeners";
import getCameraParameters from "../../utils/getCameraParameters";
import { useQueue } from "../../QueueContext";

function CnnDataCollectionComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [isCapturing, setIsCapturing] = useState(false);
  const { addToQueue } = useQueue();

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

        const cacheItem = {
          userId: userId,
          cursorPosition: currentCursorPosition.current,
          cameraMatrix: JSON.stringify(cameraMatrix),
          distCoeffs: JSON.stringify(distCoeffs),
          blob: blob,
        };
        const taskItem = {
          type: "image-processing",
          data: cacheItem,
        };
        addToQueue(taskItem);
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

  return (
    <div className={`camera-container ${isCapturing ? "processing" : ""}`}>
      <video ref={videoRef} className="video-feed" />
      {isCapturing && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CnnDataCollectionComponent;
