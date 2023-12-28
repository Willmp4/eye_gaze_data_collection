import { useEffect, useRef } from "react";

const useCamera = () => {
  const videoRef = useRef(null);

  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      });
    }
  }, []);

  const captureImage = (onCapture = (blob) => {}) => {
    return new Promise((resolve) => {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(onCapture);
    });
  };
  return { videoRef, captureImage };
};

export default useCamera;
