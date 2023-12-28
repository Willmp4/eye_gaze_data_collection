import React, { useState } from "react";
import "./App.css";
import CameraComponent from "./CnnDataCollectionComponent"; // Make sure the path is correct
import { Button } from "react-bootstrap";
import CalibrationComponent from "./CalibrationComponent";

function App() {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [isCalibrationComplete, setIsCalibrationComplete] = useState(false);

  const handleCalibrationComplete = () => {
    setIsCalibrationComplete(true);
  };

  const handleFullScreen = () => {
    if (!isFullScreen) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullScreen(!isFullScreen);
  };

  return (
    <div className={isFullScreen ? "App fullscreen" : "App"}>
      <h1>Welcome to the Gaze Capture App</h1>
      <p>Enter your usename in the box before anything.</p>
      <p>Please go fullscreen and look at the cursor before pressing the space bar.</p>
      <Button onClick={handleFullScreen}>{isFullScreen ? "Exit Full Screen" : "Go Full Screen"}</Button>
      {!isCalibrationComplete ? <CalibrationComponent onCalibrationComplete={handleCalibrationComplete} /> : <CameraComponent />}
    </div>
  );
}

export default App;
