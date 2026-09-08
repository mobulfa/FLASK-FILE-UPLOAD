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

	const confirmationModal = document.createElement("div");
	confirmationModal.className = "confirmation-modal";
	confirmationModal.setAttribute("aria-hidden", "true");
	confirmationModal.innerHTML = `
		<div class="confirmation-backdrop"></div>
		<section class="confirmation-dialog" role="dialog" aria-modal="true" aria-labelledby="confirmation-title">
			<h2 id="confirmation-title">Delete file?</h2>
			<p class="confirmation-message"></p>
			<div class="confirmation-actions">
				<button class="confirmation-cancel" type="button">Cancel</button>
				<button class="confirmation-delete" type="button">Delete</button>
			</div>
		</section>`;
	document.body.append(confirmationModal);

	const confirmationMessage = confirmationModal.querySelector(".confirmation-message");
	const cancelConfirmation = confirmationModal.querySelector(".confirmation-cancel");
	const deleteConfirmation = confirmationModal.querySelector(".confirmation-delete");
	let activeDeleteForm;
	let lastFocusedElement;

	const closeConfirmation = () => {
		confirmationModal.classList.remove("is-visible");
		confirmationModal.setAttribute("aria-hidden", "true");
		activeDeleteForm = null;
		lastFocusedElement?.focus();
	};

	const openConfirmation = (form, filename) => {
		activeDeleteForm = form;
		lastFocusedElement = document.activeElement;
		confirmationMessage.textContent = `Are you sure you want to delete ${filename}?`;
		confirmationModal.classList.add("is-visible");
		confirmationModal.setAttribute("aria-hidden", "false");
		cancelConfirmation.focus();
	};

	cancelConfirmation.addEventListener("click", closeConfirmation);
	confirmationModal.querySelector(".confirmation-backdrop").addEventListener("click", closeConfirmation);
	deleteConfirmation.addEventListener("click", () => {
		activeDeleteForm?.submit();
	});
	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape" && confirmationModal.classList.contains("is-visible")) {
			closeConfirmation();
		}
	});

	document.querySelectorAll(".delete-form").forEach((form) => {
		form.addEventListener("submit", (event) => {
			const filename = form.querySelector(".delete-button")?.getAttribute("aria-label")
				?.replace(/^Delete\s+/i, "") || "this file";

			event.preventDefault();
			openConfirmation(form, filename);
		});
	});
});
