frappe.provide("custom.attendance");

custom.attendance.Heatmap = class {
	constructor(opts) {
		this.wrapper = opts.wrapper;
		this.employee = opts.employee;
		this.year = opts.year || new Date().getFullYear();
		this.data = {};

		this.COLOR_MAP = {
			present: "#14783eff",
			wfh: "#74bff1ff",
			half_day: "#f49a09ff",
			absent: "#c91f0cff",
			leave: "#961bc7ff",
			late_early: "#f4db7bff",
			none: "#ebedf0"
		};

		this.LABEL_MAP = {
			present: "Present",
			wfh: "Work From Home",
			half_day: "Half Day",
			absent: "Absent",
			leave: "Leave",
			late_early: "Late Entry / Early Exit",
			none: "No Record"
		};

		this.init();
	}

	init() {
		this.wrapper.innerHTML = `<div class="attendance-heatmap"></div>`;
		this.container = this.wrapper.querySelector(".attendance-heatmap");
		this.fetch_data();
	}

	fetch_data() {
		frappe.call({
			method: "fujishkahr.api.api.get_employee_attendance_heatmap",
			args: {
				employee: this.employee,
				year: this.year
			},
			callback: (r) => {
				if (r.message) {
					this.data = r.message;
					this.render();
				}
			}
		});
	}

	render() {
		this.container.innerHTML = "";

		const wrapper = document.createElement("div");
		wrapper.className = "heatmap-wrapper";

		const monthsRow = document.createElement("div");
		monthsRow.className = "heatmap-months";

		const grid = document.createElement("div");
		grid.className = "heatmap-grid";

		let columnPointer = 1;

		for (let month = 0; month < 12; month++) {
			const firstDay = new Date(Date.UTC(this.year, month, 1));
			const lastDay = new Date(Date.UTC(this.year, month + 1, 0));
			const daysInMonth = lastDay.getUTCDate();

			// Month label
			const monthLabel = document.createElement("div");
			monthLabel.className = "month-label";
			monthLabel.style.gridColumnStart = columnPointer;
			monthLabel.innerText = firstDay.toLocaleString("default", { month: "short" });
			monthsRow.appendChild(monthLabel);

			// Weekday offset (Mon = 0 ... Sun = 6)
			let startOffset = (firstDay.getUTCDay() + 6) % 7;

			let dayCounter = 1;
			let row = startOffset + 1;

			while (dayCounter <= daysInMonth) {
				for (let r = row; r <= 7 && dayCounter <= daysInMonth; r++) {
					const date = new Date(Date.UTC(this.year, month, dayCounter));
					const dateStr = date.toISOString().slice(0, 10);
					const status = this.data[dateStr] || "none";

					const cell = document.createElement("div");
					cell.className = "heatmap-cell";
					cell.style.backgroundColor = this.COLOR_MAP[status];
					cell.style.gridColumn = columnPointer;
					cell.style.gridRow = r;
					cell.title = `${dateStr}: ${this.LABEL_MAP[status]}`;

					grid.appendChild(cell);
					dayCounter++;
				}

				row = 1;
				columnPointer++;
			}

			// GAP between months
			columnPointer += 1;
		}

		const daysCol = document.createElement("div");
		daysCol.className = "heatmap-days";

		["Mon", " ", "Wed", " ", "Fri", " ", "Sun"].forEach(day => {
			const d = document.createElement("div");
			d.className = "day-label";
			d.innerText = day;
			daysCol.appendChild(d);
		});

		wrapper.appendChild(monthsRow);

		const body = document.createElement("div");
		body.className = "heatmap-body";
		body.appendChild(daysCol);
		body.appendChild(grid);

		wrapper.appendChild(body);

		this.container.appendChild(wrapper);

		this.render_legend();
		this.inject_styles();
	}


	render_legend() {
		const legend = document.createElement("div");
		legend.className = "heatmap-legend";
		legend.style.marginTop = "20px";

		Object.keys(this.COLOR_MAP).forEach(key => {
			if (key === "none") return;
			const item = document.createElement("div");
			item.className = "legend-item";
			
			item.innerHTML = `
				<span class="legend-color" style="background:${this.COLOR_MAP[key]}"></span>
				<span>${this.LABEL_MAP[key]}</span>
			`;
			legend.appendChild(item);
		});
		this.container.appendChild(legend);
	}

	inject_styles() {
		if (document.getElementById("attendance-heatmap-style")) return;

		const style = document.createElement("style");
		style.id = "attendance-heatmap-style";
		style.innerHTML = `
			.heatmap-grid {
				display: grid;
				grid-template-rows: repeat(7, 12px);
				grid-auto-columns: 12px;
				gap: 3px;
			}

			.heatmap-cell {
				width: 12px;
				height: 12px;
				border-radius: 2px;
				cursor: pointer;
			}

			.heatmap-legend {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
				row-gap: 10px;
				column-gap: 20px;
				margin-top: 16px;
				padding-top: 12px;
				border-top: 1px solid #e5e7eb;
				font-size: 12px;
			}

			.legend-item {
				display: flex;
				align-items: center;
				gap: 8px;
			}

			.legend-color {
				width: 12px;
				height: 12px;
				border-radius: 2px;
			}

			.heatmap-wrapper {
				overflow-x: auto;
			}

			.heatmap-months {
				display: grid;
				grid-auto-flow: column;
				grid-auto-columns: 14px;
				margin-left: 52px;
				margin-bottom: 6px;
				font-size: 11px;
				color: #000206ff;
			}

			.month-label {
				grid-row: 1;
				white-space: nowrap;
			}

			.heatmap-body {
				display: flex;
				align-items: flex-start;
			}

			.heatmap-days {
				display: grid;
				grid-template-rows: repeat(7, 12px);
				gap: 3px;
				width: 40px;
				font-size: 11px;
				color: #000206ff;
			}

			.day-label {
				height: 12px;
				line-height: 12px;
				text-align: right;
				padding-right: 6px;
			}

		`;
		document.head.appendChild(style);
	}
};
