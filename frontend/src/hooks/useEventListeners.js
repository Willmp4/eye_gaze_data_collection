import { useEffect } from "react";

function useEventListeners(eventName, handler, element = window, dependencies) {
  useEffect(() => {
    const isSupported = element && element.addEventListener;
    if (!isSupported) return;

    element.addEventListener(eventName, handler);
    return () => {
      element.removeEventListener(eventName, handler);
    };
    // eslint-disable-next-line
  }, [eventName, handler, element]); // Add dependencies here
}

export default useEventListeners;
