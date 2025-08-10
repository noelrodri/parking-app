function deleteUser(userId) {
    if (confirm("Are you sure you want to delete this user?")) {
        fetch(`/user/${userId}/delete`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        }).then(response => response.json())
        .then(data => {
            alert(data.message);
            window.location.href = "/users"; // Redirect back to users list
        });
    }
}


function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleButton = event.target;

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleButton.textContent = 'Hide'; 
    } else {
        passwordInput.type = 'password';
        toggleButton.textContent = 'Show'; 
    }
}


const usrdashlot = document.getElementById('lotsearchBtn');

if (usrdashlot) {
  usrdashlot.addEventListener("click", async () => {
    const query = document.getElementById('searchQuery').value; 
    const tbody = document.getElementById('lotResults');
    tbody.innerHTML = "";
    try {
      const response = await fetch('/user/api/parking-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })  
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Request failed.");
      }

      const result = await response.json();
      console.log("Search results:", result);

       if (result.parking_lots.length === 0) {
            tbody.innerHTML = `<tr>
              <td colspan="4" class="text-muted">No parking lots found at this location.</td>
            </tr>`;
        } 
        else {
            result.parking_lots.forEach(lot => {
              const row = document.createElement('tr');
              row.innerHTML = `
                <td>${lot.id}</td>
                <td>${lot.address}</td>
                <td>${lot.availability}</td>
              `;

              const bookCell = document.createElement('td');
              if (lot.availability > 0)
              { 
                bookCell.innerHTML = `<a href="/user/spot/book${lot.id}" class="btn btn-primary btn-sm">Book</a>`;
                row.appendChild(bookCell);
              }
              else {
                row.appendChild(bookCell);
              }

              tbody.appendChild(row);
            });
        }
      
    } 
    catch (error) {
      console.error("Error:", error.message);
    }
  });
}



const usageCtx = document.getElementById('usageChart')?.getContext('2d');

if (usageCtx ) {
    const labels = window.chartData.labels || [];
    const values = window.chartData.values || [];
    const max_value = (window.chartData.maxvalue || 10)  + 1;
    new Chart(usageCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Times Parked',
                data: values,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(0, 0, 0, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    suggestedMax: max_value,
                    ticks: { stepSize: 1 },
                    beginAtZero: true
                }
            }
        }
    });
}


const revenueCtx = document.getElementById('revenueChart')?.getContext('2d');

if (revenueCtx) {   
    const revenue_labels = window.chartData.revenue_labels || [];
    const revenue_values = window.chartData.revenue_values || [];

    new Chart(revenueCtx, {
        type: 'pie',
        data: {
            labels: revenue_labels,      
            datasets: [{
                label: 'Revenue (₹)',
                data: revenue_values,     
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                ],
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}


const occupancyCtx = document.getElementById('occupancyChart')?.getContext('2d');

if (occupancyCtx) {
    const lot_labels = window.chartData.lot_labels || [];
    const available_counts = window.chartData.available_counts || [];
    const occupied_counts = window.chartData.occupied_counts || [];


    new Chart(occupancyCtx, {
        type: 'bar',
        data: {
            labels:  lot_labels, 
            datasets: [
                {
                    label: 'Available',
                    data: available_counts,  
                    backgroundColor: '#4BC0C0'
                },
                {
                    label: 'Occupied',
                    data:  occupied_counts,  
                    backgroundColor: '#FF6384'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    }); 
}