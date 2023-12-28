import React, { useEffect, useRef, useState } from "react";
import "./CalibrationComponent.css";
import useCamera from "./useCamera";

function CalibrationComponent({ onCalibrationComplete }) {
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [currentPoint, setCurrentPoint] = useState(0);
  const { videoRef, captureImage } = useCamera();

  useEffect(() => {
    const updatedCalibrationPoints = generateCalibrationPoints();
    setCalibrationPoints(updatedCalibrationPoints);
    console.log("Calibration Points: ", updatedCalibrationPoints);
  }, []);

  const generateCalibrationPoints = () => {
    return [
      { x: 0, y: 0 },
      { x: 200, y: 200 },
    ];
  };

  const handleSpaceBar = async () => {
    if (currentPoint < calibrationPoints.length - 1) {
      console.log("Current Point: ", currentPoint);
      const point = calibrationPoints[currentPoint];
      await captureImage();
      setCurrentPoint(currentPoint + 1);
    } else {
      onCalibrationComplete();
    }
  };

  useEffect(() => {
    const keyDownHandler = (event) => {
      if (event.keyCode === 32) {
        handleSpaceBar();
      }
    };

    window.addEventListener("keydown", keyDownHandler);
    return () => {
      window.removeEventListener("keydown", keyDownHandler);
    };
  }, [currentPoint, calibrationPoints]);

  return (
    <div className="calibration-containter">
      <video ref={videoRef} className="video-feed" />
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
