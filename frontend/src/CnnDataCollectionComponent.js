import React, { useEffect, useState } from "react";
import "./CameraComponent.css";
import useCamera from "./useCamera"; // Assuming you have this hook
import sendImageToServer from "./sendImageToServer";

function CameraComponent() {
  const [userId, setUserId] = useState(null);
  const { videoRef, captureImage } = useCamera(); // Using the custom hook
  const currentCursorPosition = useRef({ x: 0, y: 0 });

  const screenData = {
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    devicePixelRatio: window.devicePixelRatio,
  };

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.keyCode === 32 && userId) {
        // space bar code
        captureImage().then((blob) => {
          const additionalData = {
            userId,
            cursorPosition: currentCursorPosition.current,
            screenData,
          };
          sendImageToServer(blob, "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image", additionalData);
        });
      }
    };

    const updateCursorPosition = (event) => {
      currentCursorPosition.current = { x: event.screenX, y: event.screenY };
    };

    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousemove", updateCursorPosition);

    return () => {
      document.removeEventListener("mousemove", updateCursorPosition);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [userId]);

  return (
    <div className="camera-container">
      <input type="text" placeholder="Enter User ID" value={userId} onChange={(e) => setUserId(e.target.value)} className="user-id-input" />
      <video ref={videoRef} className="video-feed" />
    </div>
  );
}

export default CameraComponent;
