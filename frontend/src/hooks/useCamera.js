import { useEffect, useRef } from "react";

const useCamera = () => {
  const videoRef = useRef(null);

  useEffect(() => {
    let currentVideoRef = videoRef.current; // Capture the current value of videoRef

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        if (currentVideoRef && currentVideoRef.srcObject) {
          const tracks = currentVideoRef.srcObject.getTracks();
          tracks.forEach((track) => track.stop());
        }
        if (currentVideoRef) {
          currentVideoRef.srcObject = stream;
          currentVideoRef.play().catch((e) => console.log("Error playing video: ", e));
        }
      });
    }

    // Cleanup function
    return () => {
      if (currentVideoRef && currentVideoRef.srcObject) {
        const tracks = currentVideoRef.srcObject.getTracks();
        tracks.forEach((track) => track.stop());
      }
    };
  }, []);

  const captureImage = (onCapture = (blob) => {}) => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      if (videoRef) {
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error("videoRef is null"));
          }
        });
      } else {
        reject(new Error("videoRef is null"));
      }
    });
  };
  return { videoRef, captureImage };
};

export default useCamera;
