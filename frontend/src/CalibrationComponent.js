import React, { useEffect, useState } from "react";
import "./CalibrationComponent.css";
import useCamera from "./useCamera";
import sendImageToServer from "./sendImageToServer";

function CalibrationComponent({ onCalibrationComplete, userId, setUserId }) {
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [currentPoint, setCurrentPoint] = useState(0);
  const { videoRef, captureImage } = useCamera();
  const [processing, setProcessing] = useState(null);

  const screenData = {
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    devicePixelRatio: window.devicePixelRatio,
  };

  useEffect(() => {
    const updatedCalibrationPoints = generateCalibrationPoints();
    setCalibrationPoints(updatedCalibrationPoints);
    console.log("Calibration Points: ", updatedCalibrationPoints);
  }, []);

  useEffect(() => {
    const keyDownHandler = async (event) => {
      if (event.keyCode === 32 && userId) {
        await handleSpaceBar();
      }
    };

    window.addEventListener("keydown", keyDownHandler);
    return () => {
      window.removeEventListener("keydown", keyDownHandler);
    };
    // Make sure to include all the dependencies required for the effect to work correctly
    // eslint-disable-next-line
  }, [currentPoint, calibrationPoints, userId]);

  const generateCalibrationPoints = () => {
    // Your logic to generate calibration points
    return [
      { x: 0, y: 0 },
      { x: 200, y: 200 },
    ];
  };

  const handleSpaceBar = async () => {
    if (currentPoint < calibrationPoints.length) {
      const point = calibrationPoints[currentPoint];
      console.log("Point: ", point);
      try {
        const blob = await captureImage();
        const additionalData = {
          calibrationPoints: [point.x, point.y],
          userId: userId,
          screenData: screenData,
        };
        await sendImageToServer(blob, "https://gaze-detection-c70f9bc17dbb.herokuapp.com/calibrate", additionalData);
        // Move to the next point or complete the calibration
        setProcessing("success");
        setTimeout(() => setProcessing(null), 500);
        if (currentPoint < calibrationPoints.length - 1) {
          setCurrentPoint(currentPoint + 1);
        } else {
          onCalibrationComplete();
        }
      } catch (error) {
        setProcessing("error");
        setTimeout(() => setProcessing(null), 500);
        console.error("Error capturing or sending image:", error);
      }
    }
  };

  return (
    <div className={`calibration-container ${processing}`}>
      <video ref={videoRef} className="video-feed" />
      <input type="text" placeholder="Enter User ID" value={userId} onChange={(e) => setUserId(e.target.value)} className="user-id-input" />
      {calibrationPoints.length > 0 && (
        <div
          className="calibration-point"
          style={{
            top: calibrationPoints[currentPoint].y,
            left: calibrationPoints[currentPoint].x,
          }}
        ></div>
      )}
    </div>
  );
}

export default CalibrationComponent;
