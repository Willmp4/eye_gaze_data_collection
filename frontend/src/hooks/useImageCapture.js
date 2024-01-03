import { useCallback } from "react";
import useCamera from "./useCamera";

function useImageCapture() {
  const { videoRef, captureImage } = useCamera();

  const capture = useCallback(async () => {
    try {
      const blob = await captureImage();
      return blob;
    } catch (error) {
      console.error("Error capturing or sending image:", error);
      throw error;
    }
  }, [captureImage]);
  return { videoRef, capture };
}

export default useImageCapture;
