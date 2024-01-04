import React, { useState } from "react";
import "../styles/App.css";
import CnnDataCollectionComponent from "../components/CnnDataCollectoinComponent/CnnDataCollectionComponent"; // Make sure the path is correct
import { Button } from "react-bootstrap";
import CalibrationComponent from "../components/CalibrationComponent/CalibrationComponent";
import UserGuideModal from "./userGuide";
import { QueueProvider } from "../QueueContext";
function App() {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [isCalibrationComplete, setIsCalibrationComplete] = useState(false);
  const [userId, setUserId] = useState(null);

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
    <QueueProvider>
      <div className={isFullScreen ? "App fullscreen" : "App"}>
        <h1>Welcome to the Gaze Capture App</h1>
        <UserGuideModal />
        {!isCalibrationComplete ? (
          <>
            <p>Enter your username in the box before anything.</p>
            <p>Look at the red dots and then press space bar to take the pictures for the calibration.</p>
            <CalibrationComponent
              onCalibrationComplete={handleCalibrationComplete}
              userId={userId}
              setUserId={setUserId}
            />
          </>
        ) : (
          <>
            <p>Look at the cursor and then press the space bar to take the pictures.</p>
            <CnnDataCollectionComponent userId={userId} />
          </>
        )}

        <Button onClick={handleFullScreen}>{isFullScreen ? "Exit Full Screen" : "Go Full Screen"}</Button>
      </div>
    </QueueProvider>
  );
}

export default App;
