import React, { createContext, useContext, useState, useEffect } from "react";
import sendImageToServer from "./utils/sendImageToServer";

const QueueContext = createContext();

export const useQueue = () => useContext(QueueContext);

export const QueueProvider = ({ children }) => {
  const [taskQueue, setTaskQueue] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [startQueue, setStartQueue] = useState(false);

  const addToQueue = (item) => {
    setTaskQueue((prev) => [...prev, item]);
  };

  const processQueueItem = async (item) => {
    try {
      setIsProcessing(true);
      const endpoint =
        item.type === "calibration"
          ? "https://gaze-detection-c70f9bc17dbb.herokuapp.com/calibrate"
          : "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image";

      await sendImageToServer([item.data], endpoint);
      setIsProcessing(false);
    } catch (error) {
      console.error("Error processing queue item:", error);
    }
  };

  useEffect(() => {
    if (startQueue && taskQueue.length > 0 && !isProcessing) {
      const item = taskQueue[0];
      processQueueItem(item).then(() => {
        setTaskQueue((prev) => prev.slice(1));
      });
    }
  }, [taskQueue, isProcessing, startQueue]);

  return <QueueContext.Provider value={{ addToQueue, setStartQueue, taskQueue }}>{children}</QueueContext.Provider>;
};
