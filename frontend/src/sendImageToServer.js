const sendImageToServer = async (cache, url, onCalibrationComplete, clearCache) => {
  for (const item of cache) {
    const formData = new FormData();

    // Dynamically append properties from the item to formData
    Object.keys(item).forEach((key) => {
      if (key === "blob") {
        formData.append("image", item[key]);
      } else if (typeof item[key] === "object") {
        formData.append(key, JSON.stringify(item[key]));
      } else {
        formData.append(key, item[key]);
      }
    });

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      console.log(data);
    } catch (err) {
      console.error("Error sending data:", err);
      // Handle error appropriately
    }
  }

  clearCache(); // Clear the cache after all submissions
  onCalibrationComplete(); // Call the completion handler
};

export default sendImageToServer;
