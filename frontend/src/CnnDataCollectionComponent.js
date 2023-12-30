import React, { useEffect, useRef, useState } from "react";
import "./CameraComponent.css";
import useCamera from "./useCamera"; // Assuming you have this hook
import sendImageToServer from "./sendImageToServer";

function CameraComponent({ userId }) {
  const { videoRef, captureImage } = useCamera(); // Using the custom hook
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [processing, setProcessing] = useState(null);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.keyCode === 32 && userId) {
        setProcessing("processing");
        console.log("space bar pressed");
        // space bar code
        captureImage()
          .then((blob) => {
            const additionalData = {
              userId,
              cursorPosition: currentCursorPosition.current,
            };
            sendImageToServer(blob, "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image", additionalData);
            setProcessing("success");
            setTimeout(() => setProcessing(null), 500);
          })
          .catch((error) => {
            console.log(error);
            setProcessing("error");
            setTimeout(() => setProcessing(null), 500);
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
    // eslint-disable-next-line
  }, [userId]);

  return (
    <div className={`camera-container ${processing}`}>
      <video ref={videoRef} className="video-feed" />
      {processing === "processing" && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CameraComponent;
