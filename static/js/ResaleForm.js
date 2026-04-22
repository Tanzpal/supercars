document.getElementById("imageInput").addEventListener("change", function () {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function () {
      document.getElementById("previewImage").src = reader.result;
    };
    reader.readAsDataURL(file);
  }
});
