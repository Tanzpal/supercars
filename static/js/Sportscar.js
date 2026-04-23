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
  // Search Cars
  // -------------------
  if (searchInput) {
    searchInput.addEventListener("keyup", () => {
      const query = searchInput.value.toLowerCase();
      blogCards.forEach((card) => {
        const textContent = card.textContent.toLowerCase();
        if (textContent.includes(query)) {
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

        // ADD
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

        // REMOVE
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
