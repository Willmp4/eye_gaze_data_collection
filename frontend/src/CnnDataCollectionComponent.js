import React, { useEffect, useRef, useState } from "react";
import "./CameraComponent.css";

function CameraComponent() {
  const videoRef = useRef(null);
  const [userId, setUserId] = useState(null);
  const currentCursorPosition = useRef({ x: 0, y: 0 }); // useRef to persist values
  const screenData = {
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    devicePixelRatio: window.devicePixelRatio,
  };

  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      });
    }
  }, []);

  useEffect(() => {
    const captureImage = () => {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        sendImageToServer(blob, currentCursorPosition.current); // Use .current to access the latest ref value
      });
    };

    const sendImageToServer = async (blob, cursorPosition) => {
      const formData = new FormData();
      formData.append("image", blob);
      formData.append("userId", userId);
      formData.append("cursorPosition", JSON.stringify(cursorPosition));
      formData.append("screenData", JSON.stringify(screenData));

      try {
        const response = await fetch("https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image", {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        console.log(data);
      } catch (err) {
        console.log(err);
      }
    };
    const handleKeyDown = (event) => {
      if (event.keyCode === 32 && userId) {
        // space bar code
        captureImage();
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]); // userId as dependency if it affects the event listeners

  return (
    <div className="camera-container">
      <input type="text" placeholder="Enter User ID" value={userId} onChange={(e) => setUserId(e.target.value)} className="user-id-input" />
      <video ref={videoRef} className="video-feed" />
    </div>
  );
}

export default CameraComponent;
