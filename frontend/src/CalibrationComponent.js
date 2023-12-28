import React, { useEffect, useRef, useState } from "react";
import "./CalibrationComponent.css";

function CalibrationComponent({ onCalibrationComplete }) {
  const videoRef = useRef(null);
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [currentPoint, setCurrentPoint] = useState(0);

  useEffect(() => {
    const updatedCalibrationPoints = generateCalibrationPoints();
    setCalibrationPoints(updatedCalibrationPoints);
    console.log("Calibration Points: ", updatedCalibrationPoints);
  }, []);

  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      });
    }
  }, []);

  const generateCalibrationPoints = () => {
    return [
      { x: 100, y: 100 },
      { x: 200, y: 200 },
    ];
  };

  const handleSpaceBar = async () => {
    if (currentPoint < calibrationPoints.length - 1) {
      console.log("Current Point: ", currentPoint);
      const point = calibrationPoints[currentPoint];
      //   await caputreAndSendImage(point);
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
