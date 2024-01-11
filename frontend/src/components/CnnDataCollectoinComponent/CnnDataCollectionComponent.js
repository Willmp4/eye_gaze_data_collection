import React, { useRef, useState, useEffect } from "react";
import "./CnnDataCollectionComponent.css";
import useCamera from "../../hooks/useCamera";
import useEventListeners from "../../hooks/useEventListeners";
import { useQueue } from "../../QueueContext";

function CnnDataCollectionComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [isCapturing, setIsCapturing] = useState(false);
  const { addToQueue, taskQueue } = useQueue();
  const [showNotification, setShowNotification] = useState(false);
  const [counter, setCounter] = useState(0);

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (taskQueue.length > 0) {
        e.preventDefault();
        e.returnValue = "Images are still being processed. Are you sure you want to leave?";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [taskQueue.length]);

  const updateCursorPosition = (event) => {
    currentCursorPosition.current = { x: event.clientX, y: event.clientY };
  };

  const enqueueCapture = () => {
    if (!userId || isCapturing) return;
    setIsCapturing(true);
    captureImage()
      .then((blob) => {
        const cacheItem = {
          userId: userId,
          cursorPosition: currentCursorPosition.current,
          blob: blob,
        };
        const taskItem = {
          type: "image-processing",
          data: cacheItem,
        };
        addToQueue(taskItem);
        setIsCapturing(false);
        setShowNotification(true);
        setTimeout(() => setShowNotification(false), 2000);
      })
      .catch((error) => {
        console.error("Error capturing image:", error);
        setIsCapturing(false);
      });
  };

  useEventListeners("mousemove", updateCursorPosition);
  useEventListeners("keydown", (event) => {
    if (event.keyCode === 32) {
      setCounter(counter + 1);
      enqueueCapture();
    }
  });

  return (
    <div className={`camera-container ${isCapturing ? "processing" : ""}`}>
      <video ref={videoRef} className="video-feed" />
      <div className="counter">{counter}</div>
      {isCapturing && <div className="processing-indicator">Processing...</div>}
      {showNotification && <div className="captrue-notification">Image captured!</div>}
    </div>
  );
}

export default CnnDataCollectionComponent;
