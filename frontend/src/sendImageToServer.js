const sendImageToServer = async (blob, url, additionalData) => {
  const formData = new FormData();
  formData.append("image", blob);
  Object.keys(additionalData).forEach((key) => {
    if (typeof additionalData[key] === "object") {
      formData.append(key, JSON.stringify(additionalData[key]));
    } else {
      formData.append(key, additionalData[key]);
    }
  });

  try {
    const respone = await fetch(url, {
      method: "POST",
      body: formData,
    });
    const data = await respone.json();
    console.log(data);
    return data;
  } catch (err) {
    console.log(err);
  }
};

export default sendImageToServer;
