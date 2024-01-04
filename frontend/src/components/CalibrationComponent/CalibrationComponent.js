import React, { useEffect, useState, useCallback } from "react";
import "./CalibrationComponent.css";
import useCamera from "../../hooks/useCamera";
import useCacheManager from "../../hooks/useCacheManager";
import getCameraParameters from "../../utils/getCameraParameters";
import useEventListeners from "../../hooks/useEventListeners";

function CalibrationComponent({ onCalibrationComplete, userId, setUserId }) {
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [currentPoint, setCurrentPoint] = useState(0);
  const { videoRef, captureImage } = useCamera();
  const { addToCache, processCache, clearCache } = useCacheManager();
  const [isUploading, setIsUploading] = useState(false);
  const [processing, setProcessing] = useState(null);

  const generateCalibrationPoints = useCallback(() => {
    const screenWidth = window.screen.width;
    const screenHeight = window.screen.height;
    const offset = 20; // Offset from the edges

    const points = [
      { x: offset, y: offset }, // Adjusted from 0,0 to be within the screen
      { x: offset, y: screenHeight - offset },
      { x: screenWidth - offset, y: offset },
      { x: screenWidth - offset, y: screenHeight - offset },
    ];

    const numCentralPoints = 46; // Number of points to be placed in the center
    const centralPointsPerSide = Math.ceil(Math.sqrt(numCentralPoints));

    const stepX = (screenWidth - 2 * offset) / (centralPointsPerSide + 1);
    const stepY = (screenHeight - 2 * offset) / (centralPointsPerSide + 1);

    for (let i = 1; i <= centralPointsPerSide; i++) {
      for (let j = 1; j <= centralPointsPerSide; j++) {
        const x = Math.round(offset + i * stepX);
        const y = Math.round(offset + j * stepY);
        points.push({ x, y });
      }
    }

    console.log(points.length);

    return points;
  }, []);

  useEffect(() => {
    setCalibrationPoints(generateCalibrationPoints());
  }, [generateCalibrationPoints]);

  const handleSubmitCache = useCallback(async () => {
    setIsUploading(true);
    await processCache("https://gaze-detection-c70f9bc17dbb.herokuapp.com/calibrate");
    clearCache();
    setIsUploading(false);
    onCalibrationComplete(false);
  }, [processCache, clearCache, onCalibrationComplete]);

  const handleSpaceBar = useCallback(async () => {
    if (currentPoint < calibrationPoints.length) {
      const point = calibrationPoints[currentPoint];
      try {
        const blob = await captureImage();
        const screenData = {
          screenWidth: window.screen.width,
          screenHeight: window.screen.height,
          devicePixelRatio: window.devicePixelRatio,
        };
        const { cameraMatrix, distCoeffs } = getCameraParameters(videoRef.current);
        const cacheItem = {
          userId: userId,
          screenData: JSON.stringify(screenData),
          calibrationPoints: JSON.stringify([point.x, point.y]),
          cameraMatrix: JSON.stringify(cameraMatrix),
          distCoeffs: JSON.stringify(distCoeffs),
          blob: blob,
        };

        addToCache(cacheItem);
        setProcessing("success");
        setTimeout(() => setProcessing(null), 500);
        if (currentPoint < calibrationPoints.length - 1) {
          setCurrentPoint(currentPoint + 1);
        } else {
          handleSubmitCache();
        }
      } catch (error) {
        setProcessing("error");
        setTimeout(() => setProcessing(null), 500);
        console.error("Error capturing or sending image:", error);
      }
    }
  }, [currentPoint, calibrationPoints, userId, captureImage, videoRef, addToCache, handleSubmitCache]);

  useEventListeners(
    "keydown",
    async (event) => {
      if (event.keyCode === 32 && userId && !isUploading) {
        await handleSpaceBar();
      }
    },
    window,
    [userId, handleSpaceBar, isUploading]
  );

  const handleUserIdChange = (e) => {
    setUserId(e.target.value);
  };

  if (isUploading) {
    return <div className="uploading-text">Uploading...</div>;
  }

  return (
    <div className={`calibration-container ${processing}`}>
      <video ref={videoRef} className="video-feed" />
      <input
        type="text"
        placeholder="Enter User ID"
        value={userId}
        onChange={handleUserIdChange}
        className="user-id-input"
        aria-label="User ID"
      />
      {calibrationPoints.length > 0 && (
        <div
          className="calibration-point"
          style={{
            top: calibrationPoints[currentPoint].y,
            left: calibrationPoints[currentPoint].x,
          }}
          aria-hidden="true"
        ></div>
      )}
    </div>
  );
}

export default CalibrationComponent;
