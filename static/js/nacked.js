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
  searchInput.addEventListener("keyup", () => {
    const query = searchInput.value.toLowerCase();
    blogCards.forEach((card) => {
      const title = card.querySelector("h3").innerText.toLowerCase();
      const text = card.querySelector("p").innerText.toLowerCase();
      if (title.includes(query) || text.includes(query)) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  });

  // -------------------
  // Like Count
  // -------------------
  document.querySelectorAll(".like-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const countSpan = btn.querySelector(".like-count");
      if (countSpan) {
        let count = parseInt(countSpan.textContent);
        count++;
        countSpan.textContent = count;
      }
    });
  });

  // -------------------
  // Comment Modal
  // -------------------
  const modal = document.getElementById("commentModal");
  const closeModal = document.querySelector(".close");
  const commentList = document.getElementById("commentList");
  const commentInput = document.getElementById("commentInput");
  const postCommentBtn = document.getElementById("postComment");
  const modalBlogTitle = document.getElementById("modalBlogTitle");

  document.querySelectorAll(".comment-btn").forEach((btn, index) => {
    btn.addEventListener("click", () => {
      modal.style.display = "block";
      modalBlogTitle.textContent =
        document.querySelectorAll(".blog-card h3")[index].textContent;
      commentList.innerHTML = ""; // reset comments
    });
  });

  closeModal.addEventListener("click", () => {
    modal.style.display = "none";
  });

  postCommentBtn.addEventListener("click", () => {
    const comment = commentInput.value.trim();
    if (comment !== "") {
      const li = document.createElement("li");
      li.textContent = comment;
      commentList.appendChild(li);
      commentInput.value = "";
    }
  });

  // -------------------
  // Wishlist Hearts
  // -------------------
  const hearts = document.querySelectorAll(".heart-icon");

  hearts.forEach((heart) => {
    heart.addEventListener("click", () => {
      const card = heart.closest(".blog-card");
      const carName = card.querySelector("h3 a").textContent.trim();
      const carImage = card.querySelector("img").getAttribute("src");

      // Toggle visual heart
      heart.classList.toggle("liked");
      heart.innerHTML = heart.classList.contains("liked")
        ? "&#10084;"
        : "&#9825;";

      // Send AJAX request to add to wishlist
      if (heart.classList.contains("liked")) {
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
            if (data.status === "success") {
              console.log(`${carName} added to wishlist`);
            } else if (data.status === "exists") {
              alert(`${carName} is already in your wishlist`);
            } else if (data.status === "error") {
              alert(data.message);
            }
          })
          .catch((err) => console.error("Error:", err));
      }
    });
  });
});
