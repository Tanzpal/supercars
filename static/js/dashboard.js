document.addEventListener("DOMContentLoaded", () => {
  const wishlistContainer = document.querySelector(".wishlist-container");

  // Function to show empty state
  function showEmptyMessage() {
    wishlistContainer.innerHTML = `
      <div class="empty-wishlist">
        <p>
          You have no cars in your wishlist.<br />
          Click the ❤️ icon on a car to add it here!
        </p>
      </div>
    `;
  }

  // Event delegation for remove buttons
  wishlistContainer.addEventListener("click", async (e) => {
    if (e.target.classList.contains("remove-car")) {
      const carId = e.target.dataset.id;
      const card = e.target.closest(".wishlist-card");

      if (!carId) {
        alert("Invalid car ID");
        return;
      }

      try {
        const response = await fetch("/remove_from_wishlist", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ car_id: carId }),
        });

        const result = await response.json();
        console.log("Server response:", result);

        if (result.status === "success") {
          // Fade out effect before removing the card
          card.style.transition = "opacity 0.4s ease";
          card.style.opacity = "0";
          setTimeout(() => {
            card.remove();

            // Check if wishlist is empty after removal
            if (
              wishlistContainer.querySelectorAll(".wishlist-card").length === 0
            ) {
              showEmptyMessage();
            }
          }, 400);

          showToast("✅ Car removed successfully!");
        } else {
          alert("❌ " + result.message);
        }
      } catch (error) {
        console.error("Error removing car:", error);
        alert("An unexpected error occurred. Try again.");
      }
    }
  });

  // Toast Notification
  function showToast(message) {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.position = "fixed";
    toast.style.bottom = "20px";
    toast.style.right = "20px";
    toast.style.background = "#333";
    toast.style.color = "#fff";
    toast.style.padding = "10px 20px";
    toast.style.borderRadius = "8px";
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";

    document.body.appendChild(toast);

    setTimeout(() => (toast.style.opacity = "1"), 100);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }
});

// Sidebar toggle logic
document.addEventListener("DOMContentLoaded", () => {
  const menuItems = document.querySelectorAll(".sidebar-menu li[data-target]");
  const sections = document.querySelectorAll(".section");

  menuItems.forEach((item) => {
    item.addEventListener("click", () => {
      // Remove active class from all menu items
      menuItems.forEach((i) => i.classList.remove("active"));
      // Add active to clicked item
      item.classList.add("active");

      // Hide all sections
      sections.forEach((sec) => (sec.style.display = "none"));

      // Show selected section
      const targetId = item.getAttribute("data-target");
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.style.display = "block";
      }
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const cancelButtons = document.querySelectorAll(".cancel-btn");

  cancelButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const apptId = btn.getAttribute("data-id");

      if (!confirm("Are you sure you want to cancel this appointment?")) return;

      try {
        const response = await fetch(`/cancel_appointment/${apptId}`, {
          method: "POST",
        });

        if (response.ok) {
          btn.closest(".appointment-card").remove();
          alert("Appointment cancelled successfully.");
        } else {
          alert("Error cancelling appointment. Try again later.");
        }
      } catch (err) {
        console.error(err);
        alert("Something went wrong. Please try again.");
      }
    });
  });
});
