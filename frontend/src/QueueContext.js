import React, { createContext, useContext, useState, useEffect } from "react";
import sendImageToServer from "./utils/sendImageToServer";

const QueueContext = createContext();

export const useQueue = () => useContext(QueueContext);

export const QueueProvider = ({ children }) => {
  const [taskQueue, setTaskQueue] = useState([]);

  const addToQueue = (item) => {
    setTaskQueue((prev) => [...prev, item]);
  };

  const processQueueItem = async (item) => {
    try {
      const endpoint =
        item.type === "calibration"
          ? "https://gaze-detection-c70f9bc17dbb.herokuapp.com/calibrate"
          : "https://gaze-detection-c70f9bc17dbb.herokuapp.com/process-image";

      await sendImageToServer([item.data], endpoint);
    } catch (error) {
      console.error("Error processing queue item:", error);
    }
  };

  useEffect(() => {
    if (taskQueue.length > 0) {
      const item = taskQueue[0];
      processQueueItem(item).then(() => {
        setTaskQueue((prev) => prev.slice(1));
      });
    }
  }, [taskQueue]);

  return <QueueContext.Provider value={{ addToQueue }}>{children}</QueueContext.Provider>;
};
