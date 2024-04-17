exports = async function(changeEvent) {
  const newData = changeEvent.updateDescription.updatedFields;

  const body = JSON.stringify({
    action: "update",
    config: {
      bandwidth: newData.bandwidth,
      priority: newData.priority
    }
  });

  const url = "https://sdwan-controller.example.com/api/configure";

  const options = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body
  };

  // Using the Realm's context.http.post to send the HTTP request
  const response = await context.http.post({ url, options });

  if (response.status === 200) {
    console.log("SD-WAN configuration updated successfully!");
  } else {
    console.error("Failed to update SD-WAN configuration:", response.status);
  }
};
