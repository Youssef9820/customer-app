document.addEventListener("DOMContentLoaded", function () {
    // ======== Utility: Fetch College Years ========
    function setupYearDropdown(collegeSelectId, yearSelectId) {
        const collegeSelect = document.querySelector(collegeSelectId);
        const yearSelect = document.querySelector(yearSelectId);

        if (!collegeSelect || !yearSelect) return;

        collegeSelect.addEventListener("change", function () {
            const collegeId = this.value;
            yearSelect.innerHTML = `<option value="">Loading...</option>`;

            if (collegeId) {
                fetch(`/get_college_years/${collegeId}`)
                    .then((response) => response.json())
                    .then((data) => {
                        yearSelect.innerHTML = `<option value="">-- Select Year --</option>`;
                        data.years.forEach((year) => {
                            const opt = document.createElement("option");
                            opt.value = year.year_number;
                            opt.textContent = `Year ${year.year_number}`;
                            yearSelect.appendChild(opt);
                        });
                    })
                    .catch(() => {
                        yearSelect.innerHTML = `<option value="">Error loading years</option>`;
                    });
            } else {
                yearSelect.innerHTML = `<option value="">-- Select College First --</option>`;
            }
        });
    }

    // ======== Financial Page Logic (Subjects) ========
    const subjectCollegeSelect = document.querySelector("#subject-college-select");
    const subjectYearSelect = document.querySelector("#subject-year-select");
    const termWrapper = document.querySelector("#term-select-wrapper");
    const moduleWrapper = document.querySelector("#module-select-wrapper");
    const termSelect = document.querySelector("#term-select");
    const moduleSelect = document.querySelector("#module-select");

    if (subjectCollegeSelect && subjectYearSelect) {
        // When a college is selected → fetch years
        subjectCollegeSelect.addEventListener("change", function () {
            const collegeId = this.value;
            subjectYearSelect.innerHTML = `<option value="">Loading...</option>`;
            termWrapper.style.display = "none";
            moduleWrapper.style.display = "none";

            if (collegeId) {
                fetch(`/get_college_years/${collegeId}`)
                    .then((res) => res.json())
                    .then((data) => {
                        subjectYearSelect.innerHTML = `<option value="">-- Select Year --</option>`;
                        data.years.forEach((year) => {
                            const opt = document.createElement("option");
                            opt.value = year.year_number;
                            opt.textContent = `Year ${year.year_number}`;
                            subjectYearSelect.appendChild(opt);
                        });
                    });
            } else {
                subjectYearSelect.innerHTML = `<option value="">-- Select College First --</option>`;
            }
        });

        // When year changes → show terms or modules
        subjectYearSelect.addEventListener("change", function () {
            const collegeId = subjectCollegeSelect.value;
            const year = this.value;

            if (!collegeId || !year) return;

            fetch(`/get_college_structure/${collegeId}`)
                .then((r) => r.json())
                .then((data) => {
                    if (data.structure_type === "term") {
                        fetch(`/get_terms/${collegeId}/${year}`)
                            .then((r) => r.json())
                            .then((termData) => {
                                termSelect.innerHTML = `<option value="">-- Select Term --</option>`;
                                termData.terms.forEach((term) => {
                                    const opt = document.createElement("option");
                                    opt.value = term.id;
                                    opt.textContent = term.name;
                                    termSelect.appendChild(opt);
                                });
                                termWrapper.style.display = "block";
                                moduleWrapper.style.display = "none";
                            });
                    } else if (data.structure_type === "module") {
                        fetch(`/get_modules/${collegeId}/${year}`)
                            .then((r) => r.json())
                            .then((moduleData) => {
                                moduleSelect.innerHTML = `<option value="">-- Select Module --</option>`;
                                moduleData.modules.forEach((module) => {
                                    const opt = document.createElement("option");
                                    opt.value = module.id;
                                    opt.textContent = module.name;
                                    moduleSelect.appendChild(opt);
                                });
                                moduleWrapper.style.display = "block";
                                termWrapper.style.display = "none";
                            });
                    }
                });
        });
    }

    // ======== Structure Page Logic ========
    setupYearDropdown("#term-college-select", "#term-year-select");
    setupYearDropdown("#module-college-select", "#module-year-select");
});
