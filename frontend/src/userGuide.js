import React, { useState } from "react";
import { Modal, Button } from "react-bootstrap";

function UserGuideModal() {
  const [show, setShow] = useState(false);

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  // Styles for the full-screen modal and the close button
  const modalStyle = {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    overflow: "auto",
    backgroundColor: "white",
  };
  // Additional styles for the close button to make it more obvious
  const closeButtonStyle = {
    position: "absolute",
    top: "1rem",
    right: "1rem",
    fontSize: "2em", // even larger font size
    color: "#fff", // white color for the icon
    backgroundColor: "#dc3545", // red background for high contrast
    borderRadius: "50%", // circular shape
    padding: "0.3em", // padding around the icon
    lineHeight: "1", // tight line height for the icon
    border: "none", // no border
    cursor: "pointer", // cursor indicates it's clickable
    zIndex: "1051", // Bootstrap's default z-index for modal is 1050
  };

  // Ensure the style is applied only to the close button by targeting the class
  return (
    <>
      <Button variant="primary" onClick={handleShow}>
        User Guide
      </Button>

      <Modal show={show} onHide={handleClose} style={modalStyle} size="lg">
        <Modal.Header>
          <Modal.Title>User Guide</Modal.Title>
          <button type="button" className="close" style={closeButtonStyle} onClick={handleClose} aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </Modal.Header>
        <Modal.Body>
          <h2>Welcome to the Gaze Capture App!</h2>
          <p>
            This tool is designed to help us collect data on eye movements and gaze patterns. Your participation is invaluable, and we
            appreciate your time and effort in helping us with this study.
          </p>

          <h3>Before You Begin</h3>
          <p>
            <strong>Lighting:</strong> For best results, please try to participate in a variety of lighting conditions (natural light,
            artificial light, etc.).
          </p>

          <h3>Getting Started</h3>
          <p>
            <strong>Entering User ID:</strong> Upon launching the app, you will be prompted to enter your User ID. Avoid pressing the space
            bar in the User ID box, as it triggers the image capture process.
          </p>
          <p>
            <strong>Full Screen Mode:</strong> go into full screen mode. Click anywhere on the screen outside of the User ID box after going
            full screen to ensure the app registers your key presses correctly.
          </p>

          <h3>The Process</h3>
          <p>The app operates in two phases: the Calibration Phase and the Regular Phase.</p>
          <ul>
            <li>
              <strong>Calibration Phase:</strong> Look at red dots that appear on the screen and press the space bar to capture the image.
            </li>
            <li>
              <strong>Regular Phase:</strong> Focus on the cursor on the screen and use the space bar to capture each image. Move the cursor
              around and refocus on it before each capture.
            </li>
          </ul>

          <h3>Additional Tips</h3>
          <p>
            Keep your head still during capture for accurate results. If interrupted, just continue with the next dot or cursor position.
          </p>

          <h3>Doing Multiple Sessions</h3>
          <p>Repeating the process under different conditions enhances data quality significantly.</p>

          <h3>Feedback and Support</h3>
          <p>If you encounter any issues or have feedback, please contact us at [support email/contact form].</p>

          <p>
            <em>Thank you for participating in our Gaze Capture study. Your contribution is greatly appreciated!</em>
          </p>
        </Modal.Body>
      </Modal>
    </>
  );
}

export default UserGuideModal;
