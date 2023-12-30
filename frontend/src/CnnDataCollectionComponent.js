import React, { useEffect, useRef, useState } from "react";
import "./CameraComponent.css";
import useCamera from "./useCamera";
import sendImageToServer from "./sendImageToServer";
import debounce from "lodash/debounce"; // Assuming lodash is installed

function CameraComponent({ userId }) {
  const { videoRef, captureImage } = useCamera();
  const currentCursorPosition = useRef({ x: 0, y: 0 });
  const [processing, setProcessing] = useState("idle");

  const updateCursorPosition = debounce((event) => {
    currentCursorPosition.current = { x: event.screenX, y: event.screenY };
  }, 250); // Debounce the function

  useEffect(() => {
    const handleKeyDown = async (event) => {
      if (event.code === "Space" && userId) {
        setProcessing("processing");
        console.log("space bar pressed");
        try {
          const blob = await captureImage();
          const additionalData = {
            userId,
            cursorPosition: currentCursorPosition.current,
          };
          await sendImageToServer(blob, "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image", additionalData);
          setProcessing("success");
        } catch (error) {
          console.error("Error: ", error);
          setProcessing("error");
        } finally {
          setTimeout(() => setProcessing("idle"), 500);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousemove", updateCursorPosition);

    return () => {
      document.removeEventListener("mousemove", updateCursorPosition);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [userId, captureImage, updateCursorPosition]);

  return (
    <div className={`camera-container ${processing}`}>
      <video ref={videoRef} className="video-feed" />
      {processing === "processing" && <div className="processing-indicator">Processing...</div>}
    </div>
  );
}

export default CameraComponent;
