document.addEventListener("DOMContentLoaded", () => {
	const getFlashContainer = () => {
		let container = document.querySelector("#flash-messages");

		if (!container) {
			container = document.createElement("div");
			container.className = "flash-messages";
			container.id = "flash-messages";
			container.setAttribute("aria-live", "polite");
			document.body.prepend(container);
		}

		return container;
	};

	const showToast = (message, category = "error") => {
		const toast = document.createElement("div");
		toast.className = `flash-message message-${category}`;
		toast.setAttribute("role", category === "error" ? "alert" : "status");
		toast.innerHTML = `<span></span><button class="flash-close" type="button" aria-label="Dismiss message">&times;</button>`;
		toast.querySelector("span").textContent = message;
		getFlashContainer().append(toast);

		const dismiss = () => {
			toast.classList.remove("is-visible");
			setTimeout(() => toast.remove(), 220);
		};

		toast.querySelector(".flash-close").addEventListener("click", dismiss);
		requestAnimationFrame(() => toast.classList.add("is-visible"));
		setTimeout(dismiss, 4500);
	};

	const flashMessages = document.querySelectorAll(".flash-message");

	flashMessages.forEach((message) => {
		const closeButton = message.querySelector(".flash-close");
		let removeTimer;

		const dismiss = () => {
			clearTimeout(removeTimer);
			message.classList.remove("is-visible");
			removeTimer = setTimeout(() => message.remove(), 220);
		};

		closeButton.addEventListener("click", dismiss);
		requestAnimationFrame(() => message.classList.add("is-visible"));
		removeTimer = setTimeout(dismiss, 4500);
	});

	const uploadForm = document.querySelector("#upload-form");
	const fileInput = uploadForm?.querySelector('input[type="file"]');

	fileInput?.addEventListener("invalid", (event) => {
		event.preventDefault();
		showToast("Please choose a file to upload.");
	}, true);
});
