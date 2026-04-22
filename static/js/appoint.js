// ---------------------------
// STICKY NAVBAR
// ---------------------------
const header = document.querySelector("header");

window.addEventListener("scroll", function () {
  header.classList.toggle("sticky", window.scrollY > 0);
});

// ---------------------------
// MINIMUM DATE (3 days ahead)
// ---------------------------
const dateInput = document.getElementById("date");
let today = new Date();
today.setDate(today.getDate() + 3);
dateInput.min = today.toISOString().split("T")[0];
dateInput.value = dateInput.min; // Optional: auto-fill minimum date

// ---------------------------
// BLOCK SUNDAYS
// ---------------------------
dateInput.addEventListener("change", function () {
  const selected = new Date(this.value);
  if (selected.getDay() === 0) {
    Swal.fire({
      icon: "error",
      title: "Sunday not available",
      text: "Please select another day.",
    });
    this.value = "";
  }
});

// ---------------------------
// TIME LIMIT: 10AM - 8PM
// ---------------------------
const timeInput = document.getElementById("time");
timeInput.min = "10:00";
timeInput.max = "20:00";

timeInput.addEventListener("change", function () {
  if (this.value < "10:00" || this.value > "20:00") {
    Swal.fire({
      icon: "error",
      title: "Invalid Time",
      text: "Please select a time between 10:00 AM and 8:00 PM.",
    });
    this.value = "";
  }
});

// ---------------------------
// TOGGLE LICENSE FIELD
// ---------------------------
function toggleLicenseNumber(show) {
  const field = document.getElementById("license-number-field");
  const input = document.getElementById("license_number");

  if (show) {
    field.style.display = "block";
    input.required = true;
  } else {
    field.style.display = "none";
    input.required = false;
    input.value = "";
  }
}

// ---------------------------
// FETCH BOOKED TIME SLOTS
// ---------------------------
dateInput.addEventListener("change", function () {
  let selectedDate = this.value;
  if (!selectedDate) return;

  fetch(`/get-booked-times?date=${selectedDate}`)
    .then((res) => res.json())
    .then((data) => {
      let bookedTimes = data.booked_times;

      timeInput.addEventListener("input", function () {
        if (bookedTimes.includes(this.value)) {
          Swal.fire({
            icon: "warning",
            title: "Slot Already Booked",
            text: "Please choose another time.",
          });
          this.value = "";
        }
      });
    });
});
