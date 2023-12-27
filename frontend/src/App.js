import React, { useState } from "react";
import "./App.css";
import CameraComponent from "./useCamera"; // Make sure the path is correct
import { Button } from "react-bootstrap";
import useCalibration from "./useCalibration";

function App() {
  const [isFullScreen, setIsFullScreen] = useState(false);

  const handleFullScreen = () => {
    // Implement full-screen toggle logic
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
      <useCalibration />
      <CameraComponent />
    </div>
  );
}

export default App;
