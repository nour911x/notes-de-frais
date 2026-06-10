const fileInput = document.getElementById("file-input");
const preview = document.getElementById("preview");
const dropzoneContent = document.getElementById("dropzone-content");
const analyzeBtn = document.getElementById("analyze-btn");
const resetBtn = document.getElementById("reset-btn");
const formContainer = document.getElementById("form-container");
const confirmationContainer = document.getElementById("confirmation-container");

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    preview.src = event.target.result;
    preview.hidden = false;
    dropzoneContent.hidden = true;
  };
  reader.readAsDataURL(file);

  analyzeBtn.disabled = false;
  formContainer.innerHTML = "";
  confirmationContainer.innerHTML = "";
});

resetBtn.addEventListener("click", () => {
  fileInput.value = "";
  preview.src = "";
  preview.hidden = true;
  dropzoneContent.hidden = false;
  analyzeBtn.disabled = true;
  formContainer.innerHTML = "";
  confirmationContainer.innerHTML = "";
});

document.body.addEventListener("htmx:responseError", (event) => {
  const target = event.detail.target;
  if (target) target.innerHTML = event.detail.xhr.responseText;
});

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail.target.id === "form-container") {
    confirmationContainer.innerHTML = "";
    event.detail.target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});
