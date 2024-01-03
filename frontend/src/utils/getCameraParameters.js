function getCameraParameters(videoElement) {
  const width = videoElement.videoWidth;
  const height = videoElement.videoHeight;

  const focalLength = (width + height) / 2; // Simplified approximation
  const opticalCenterX = width / 2;
  const opticalCenterY = height / 2;

  const cameraMatrix = [
    [focalLength, 0, opticalCenterX],
    [0, focalLength, opticalCenterY],
    [0, 0, 1],
  ];

  const distCoeffs = [0, 0, 0, 0, 0]; // Assuming minimal distortion

  return { cameraMatrix, distCoeffs };
}

export default getCameraParameters;
