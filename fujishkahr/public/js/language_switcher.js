/**
 * Language Switcher
 */
frappe.after_ajax(() => {
	if (!frappe.session || frappe.session.user === "Guest") return;
	if (document.getElementById("global-language-switcher")) return;

	const languages = {
		en: "English",
		ar: "العربية"
	};

	let options = Object.entries(languages)
		.map(([key, label]) =>
			`<option value="${key}" ${frappe.boot.lang === key ? "selected" : ""}>${label}</option>`
		).join("");

	let selector = `
		<select id="global-language-switcher"
			class="form-control"
			style="width:70px; height:26px; margin-left:15px; margin-right:10px;">
			${options}
		</select>
	`;

	const observer = new MutationObserver(() => {
		const brand = document.querySelector(".navbar-brand.navbar-home");
		if (brand && !document.getElementById("global-language-switcher")) {
			brand.insertAdjacentHTML("afterend", selector);
		}
	});

	observer.observe(document.body, { childList: true, subtree: true });

	document.addEventListener("change", function (e) {
		if (e.target.id === "global-language-switcher") {
			frappe.call({
				method: "fujishkahr.api.api.set_user_language",
				args: { lang: e.target.value },
				callback: (r) => {
					if (!r.exc) {
						window.location.reload();
					}
				}
			});
		}
	});
});
