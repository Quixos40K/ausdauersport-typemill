/* Toggle Darkmode */
(function() {

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateIconVisibility(theme);
    }

    function updateIconVisibility(theme) {
        const iconSun = document.querySelector('.icon-sun');
        const iconMoon = document.querySelector('.icon-moon');

        if (iconSun) iconSun.classList.toggle('hidden', theme === 'dark');
        if (iconMoon) iconMoon.classList.toggle('hidden', theme !== 'dark');
    }

    // Initial setup: update icons based on the applied theme
    const currentTheme = document.documentElement.getAttribute('data-theme');
    updateIconVisibility(currentTheme);

    // Attach event listener for dark mode toggle
    const darkModeToggle = document.querySelector('.toggle-darkmode');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

})();

/* Toggle Sidebar */
(function() {
    const sidebar = document.getElementById('left-column');
    const expandIcon = document.getElementById('expand-icon');
    const collapseIcon = document.getElementById('collapse-icon');

    expandIcon.addEventListener('click', () => {
      sidebar.classList.remove('collapsed');
      sidebar.classList.add('expanded');
      expandIcon.classList.remove('show');
      sidebar.setAttribute('aria-expanded', 'true');
    });

    collapseIcon.addEventListener('click', () => {
      sidebar.classList.remove('expanded');
      sidebar.classList.add('collapsed');
      expandIcon.classList.add('show');
      sidebar.setAttribute('aria-expanded', 'false');
    });
})();

/* Toggle folders */
(function() {
    const navigation = document.getElementById("navigation");

    /* Handle individual folder toggles */
    function toggleFolder(event) {
        const toggle = event.target.closest(".folder-toggle");
        if (!toggle) return;

        const folder = toggle.closest(".folder");
        const id = folder.getAttribute("data-id");
        const content = folder.querySelector("ul");

        if (content) {
            const isOpen = folder.classList.toggle("open");
            localStorage.setItem(`folder-${id}`, isOpen);
        }
    }

    /* Handle expand / collapse all */
    function handleExpandCollapseAll(event) {
        const expandButton = event.target.closest("#expander");
        if (!expandButton) return;

        const expandLabel   = expandButton.dataset.expandlabel;
        const collapseLabel = expandButton.dataset.collapselabel;
        const folders = navigation.querySelectorAll(".folder");

        let expanded = localStorage.getItem("nav-expanded") === "true";

        folders.forEach(folder => {
            const id = folder.dataset.id;
            const content = folder.querySelector("ul");
            if (!content) return;

            if (expanded)
            {
                // Keep active folder open
                if (!folder.classList.contains("active") && !folder.classList.contains("activeParent"))
                {
                    folder.classList.remove("open");
                    localStorage.setItem(`folder-${id}`, false);
                }
            } 
            else
            {
                folder.classList.add("open");
                localStorage.setItem(`folder-${id}`, true);

            }
        });

        expanded = !expanded;

        expandButton.innerHTML = expanded ? collapseLabel : expandLabel ;
        localStorage.setItem("nav-expanded", expanded);
    }

    /* Restore previous expand/collapse-all state */
    const expButton = document.getElementById("expander");
    if (expButton) {
        const expandLabel   = expButton.dataset.expandlabel;
        const collapseLabel = expButton.dataset.collapselabel;
        const expanded      = localStorage.getItem("nav-expanded") === "true";

        expButton.innerHTML = expanded ? collapseLabel : expandLabel;
    }

    // Listen for both folder toggles and global expand/collapse
    navigation.addEventListener("click", event => {
        toggleFolder(event);
        handleExpandCollapseAll(event);
    });

    // Mark navigation as visible after initialization
    navigation.classList.add("visible");
})();

/* Toggle foldernavi */
(function() {
    const foldernav = document.getElementById("foldernav");

    if(foldernav)
    {
        function toggleFolder(event) {
            const toggle = event.target.closest(".folder-toggle");
            if (!toggle) return;

            const folder = toggle.closest(".folder");
            const id = folder.getAttribute("data-id");
            const content = folder.querySelector("ul");

            if (content) {
                const isOpen = folder.classList.toggle("open");
            }
        }

        // Listen for clicks to toggle folders
        foldernav.addEventListener("click", toggleFolder);

        // Mark navigation as visible after initialization
        foldernav.classList.add("visible");
    }

})();

/* Content Navigation */
(function() {
    const article = document.querySelector("main");
    const navContainer = document.getElementById("content-nav");

    if (article && navContainer) {
        const headings = Array.from(article.querySelectorAll("h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]"));

        const tocFragment = document.createDocumentFragment();

        // Populate navigation with links
        headings.forEach(heading => {
            const link = document.createElement("a");
            link.href = `#${heading.id}`;
            link.className = `db link f6 pv2 indent-${heading.tagName.toLowerCase()}`;
            link.textContent = heading.textContent;
            tocFragment.appendChild(link);
        });

        navContainer.appendChild(tocFragment);

        // Function to update the active link based on the first visible heading
        const updateActiveLink = () => {
            const firstVisibleHeading = headings.find(heading => {
                const rect = heading.getBoundingClientRect();
                return rect.top >= 0 && rect.bottom <= window.innerHeight;
            });

            document.querySelectorAll("#content-nav a.visible").forEach(link => link.classList.remove("visible"));

            if (firstVisibleHeading) {
                const activeLink = document.querySelector(`a[href="#${firstVisibleHeading.id}"]`);
                if (activeLink) activeLink.classList.add("visible");
            }
        };

        // Run on scroll and on initial load
        window.addEventListener("scroll", updateActiveLink);
        updateActiveLink();
    }
})();