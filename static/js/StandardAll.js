const header = document.querySelector("header");

window.addEventListener("scroll", function () {
  header.classList.toggle("sticky", window.scrollY > 0);
});

const dateInput = document.getElementById("date");
const today = new Date();
today.setDate(today.getDate() + 3); // 3 days after today
const yyyy = today.getFullYear();
const mm = String(today.getMonth() + 1).padStart(2, "0");
const dd = String(today.getDate()).padStart(2, "0");
const minDate = `${yyyy}-${mm}-${dd}`;
dateInput.min = minDate;
dateInput.value = minDate; // Optional: pre-fill with minimum date

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
