// Dummy alert data
const alerts = [
    {
      id: 1,
      message: "Budget limit exceeded for groceries!",
      type: "warning",
    },
    {
      id: 2,
      message: "New expense added successfully.",
      type: "success",
    },
    {
      id: 3,
      message: "Upcoming recurring payment due for rent.",
      type: "info",
    },
    {
      id: 4,
      message: "Savings goal achieved!",
      type: "success",
    },
    {
      id: 5,
      message: "Warning: Unexpected expense detected.",
      type: "warning",
    },
    {
      id: 6,
      message: "Expense tracking updated.",
      type: "info",
    },
  ];
  
  // Function to get the current time as a formatted string
  const getCurrentTime = () => {
    const now = new Date();
    return now.toLocaleString();
  };
  
  // Display alerts in the table
  const displayAlertsInTable = async() => {
    const tableBody = document.querySelector("#alertTable tbody");
    const alert=await fetch('http://localhost:5000/Alerts',{
        method:"GET",
        mode:"cors"
    })
    alerts.forEach((alert) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${alert.type}</td>
        <td>${alert.message}</td>
        <td>${getCurrentTime()}</td>
        <td>
          <button class="view-button" onclick="viewAlertDetails(${alert.id})">View</button>
          <button class="view-button" onclick="sendAlertEmail(${alert.id})">Send Email</button>
        </td>
      `;
      tableBody.appendChild(row);
    });
  };
  
  
  // Show alert details in the modal
  const viewAlertDetails = (alertId) => {
    const alert = alerts.find(a => a.id === alertId);
    const modal = document.getElementById("alertModal");
    const details = document.getElementById("alertDetails");
  
    details.innerHTML = `
      <strong>Type:</strong> ${alert.type} <br>
      <strong>Message:</strong> ${alert.message} <br>
      <strong>Timestamp:</strong> ${getCurrentTime()}
    `;
  
    modal.style.visibility = "visible";
  };
  
  // Close the modal
  const closeModal = () => {
    const modal = document.getElementById("alertModal");
    modal.style.visibility = "hidden";
  };
  
  displayAlertsInTable();
  