const API_URL = "";

const form = document.querySelector("#debate-form");
const question = document.querySelector("#question");
const rounds = document.querySelector("#rounds");
const submitButton = document.querySelector("#submit-button");
const charCount = document.querySelector("#char-count");
const section = document.querySelector("#transcript-section");
const transcript = document.querySelector("#transcript");
const loading = document.querySelector("#loading");
const loadingTitle = document.querySelector("#loading-title");
const loadingDetail = document.querySelector("#loading-detail");
const error = document.querySelector("#error");
const count = document.querySelector("#transcript-count");
const apiStatus = document.querySelector("#api-status");

question.addEventListener("input", () => {
  charCount.textContent = `${question.value.length} / 1000`;
});

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.querySelector("span").textContent = isLoading ? "Debate in progress" : "Begin debate";
  loading.classList.toggle("is-hidden", !isLoading);
}

function addResponse(entry, index) {
  const message = typeof entry.message === "string" ? entry.message.trim() : "";
  if (!message) return;

  const card = document.createElement("article");
  card.className = "response";
  card.dataset.philosopher = entry.philosopher;
  card.style.animationDelay = `${index * 70}ms`;
  card.innerHTML = `
    <div class="response-meta"><span>Round ${entry.round}</span><span>${entry.philosopher}</span></div>
    <h3>${entry.philosopher}</h3>
    <p></p>
  `;
  card.querySelector("p").textContent = message;
  transcript.appendChild(card);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = question.value.trim();
  if (!prompt) return;

  section.classList.remove("is-hidden");
  transcript.innerHTML = "";
  error.classList.add("is-hidden");
  count.textContent = "0 responses";
  loadingTitle.textContent = "The philosophers are preparing...";
  loadingDetail.textContent = "Hobbes will speak first.";
  setLoading(true);
  section.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const response = await fetch(`${API_URL}/debate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: prompt, rounds: Number(rounds.value) }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The debate could not be started.");

    data.debate.forEach((entry, index) => {
      addResponse(entry, index);
      loadingTitle.textContent = `${entry.philosopher} has answered.`;
      loadingDetail.textContent = index + 1 < data.debate.length ? "The next voice is considering the argument..." : "The exchange is complete.";
    });
    count.textContent = `${data.debate.length} responses`;
    apiStatus.textContent = "Debate complete";
    setLoading(false);
  } catch (requestError) {
    error.textContent = requestError.message.includes("fetch")
      ? "Could not reach the API. Start Uvicorn with: uvicorn main:app --reload"
      : requestError.message;
    error.classList.remove("is-hidden");
    apiStatus.textContent = "API unavailable";
    setLoading(false);
  }
});
