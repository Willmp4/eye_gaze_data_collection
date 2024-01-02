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
            This tool is designed to assist in the collection of eye movement and gaze pattern data. Your participation
            is invaluable, and I appreciate your time and effort in aiding this study.
          </p>

          <h3>Before You Begin</h3>
          <p>
            <strong>Lighting:</strong> For the best results, please participate in a variety of lighting conditions
            (natural light, artificial light, etc.).
          </p>

          <h3>Getting Started</h3>
          <p>
            <strong>Entering User ID:</strong> When launching the app, you will be prompted to enter your User ID.
            Please be careful not to press the space bar in the User ID box, as it triggers the image capture process.
          </p>
          <p>
            <strong>Full Screen Mode:</strong> For optimal experience, go into full screen mode. Click anywhere on the
            screen outside of the User ID box after entering full screen to ensure the app registers your key presses
            correctly.
          </p>

          <h3>The Process</h3>
          <p>The app operates in two phases: the Calibration Phase and the Regular Phase.</p>
          <ul>
            <li>
              <strong>Calibration Phase:</strong> Look at the red dots that appear on the screen and press the space bar
              to capture the image.
            </li>
            <li>
              <strong>Regular Phase:</strong> Focus on the cursor on the screen and use the space bar to capture each
              image. Move the cursor around and refocus on it before each capture.
            </li>
          </ul>

          <h3>Important Note</h3>
          <p>
            Please avoid spamming the space bar, as it may disrupt the image capturing process and result in inaccurate
            data collection. The app might appear simple in design, but rest assured, it's fully functional and designed
            for efficiency.
          </p>

          <h3>Additional Tips</h3>
          <p>
            Keep your head still during the capture for more accurate results. If you are interrupted, just continue
            with the next dot or cursor position.
          </p>

          <h3>Doing Multiple Sessions</h3>
          <p>
            Repeating the process under different conditions can significantly enhance the quality of the data
            collected.
          </p>

          <h3>Feedback and Support</h3>
          <p>
            If you encounter any issues or have feedback, please don't hesitate to reach out to me at [support
            email/contact form].
          </p>

          <p>
            <em>Thank you for participating in the Gaze Capture study. Your contribution is greatly appreciated!</em>
          </p>
        </Modal.Body>
      </Modal>
    </>
  );
}

export default UserGuideModal;
