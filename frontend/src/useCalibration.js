import React, { useEffect, useRef, useState } from "react";

function useCalibration({ onCalibrationComplete }) {
  const videoRef = useRef(null);
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [currentPoint, setCurrentPoint] = useState(0);

  useEffect(() => {
    setCalibrationPoints(generateCalibrationPoints());
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
    if (currentPoint < calibrationPoints.length) {
      const point = calibrationPoints[currentPoint];
      //   await caputreAndSendImage(point);
      setCurrentPoint(currentPoint + 1);
    } else {
      onCalibrationComplete();
    }
  };

  useEffect(() => {
    window.addEventListener("keydown", (event) => {
      if (event.keyCode === 32) {
        handleSpaceBar();
      }
    });
    return () => {
      window.removeEventListener("keydown", () => {});
    };
  }, [currentPoint, calibrationPoints]);

  return (
    <div className=";claibration-containter">
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

export default useCalibration;
