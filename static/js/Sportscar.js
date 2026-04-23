document.addEventListener("DOMContentLoaded", () => {
  // -------------------
  // Filter Buttons
  // -------------------
  const filterButtons = document.querySelectorAll(".filter-buttons button");
  const blogCards = document.querySelectorAll(".blog-card");
  const searchInput = document.getElementById("searchInput");

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      const category = button.getAttribute("data-category");

      blogCards.forEach((card) => {
        if (category === "all" || card.dataset.category === category) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });
    });
  });

  // -------------------
  // Search by Name + Type
  // -------------------
  if (searchInput) {
    searchInput.addEventListener("keyup", () => {
      const query = searchInput.value.toLowerCase();

      blogCards.forEach((card) => {
        const name = card.querySelector("h3 a").textContent.toLowerCase();
        const type = card.dataset.type.toLowerCase();

        if (name.includes(query) || type.includes(query)) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });
    });
  }

  // -------------------
  // Wishlist Hearts
  // -------------------
  const hearts = document.querySelectorAll(".heart-icon");

  hearts.forEach((heart) => {
    heart.addEventListener("click", () => {
      const card = heart.closest(".blog-card");
      const carName = card.querySelector("h3 a").textContent.trim();
      const carImage = card.querySelector("img").getAttribute("src");

      // Toggle UI
      heart.classList.toggle("liked");

      if (heart.classList.contains("liked")) {
        heart.innerHTML = "&#10084;";

        fetch("/add_to_wishlist", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            car_name: carName,
            car_image: carImage,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.status === "error") {
              alert(data.message);
              heart.classList.remove("liked");
              heart.innerHTML = "&#9825;";
            }
          })
          .catch((err) => console.error(err));
      } else {
        heart.innerHTML = "&#9825;";

        fetch("/remove_from_wishlist_by_name", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            car_name: carName,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.status !== "success") {
              alert("Failed to remove item");
            }
          })
          .catch((err) => console.error(err));
      }
    });
  });
});

// -------------------
// DELETE CAR
// -------------------
document.addEventListener("click", async (e) => {
  if (e.target.classList.contains("delete-btn")) {
    const carId = e.target.dataset.id;
    const card = e.target.closest(".blog-card");

    if (!confirm("Are you sure you want to delete this car?")) return;

    try {
      const res = await fetch(`/delete_car/${carId}`, {
        method: "POST",
      });

      const data = await res.json();

      if (data.status === "success") {
        // remove card smoothly
        card.style.transition = "opacity 0.3s";
        card.style.opacity = "0";

        setTimeout(() => {
          card.remove();
        }, 300);
      } else {
        alert(data.message);
      }
    } catch (err) {
      console.error(err);
      alert("Error deleting car");
    }
  }
});
