// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded "><a href="intro.html"><strong aria-hidden="true">1.</strong> Introduction</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="install.html"><strong aria-hidden="true">1.1.</strong> Installation</a></li></ol></li><li class="chapter-item expanded "><a href="quickstart.html"><strong aria-hidden="true">2.</strong> Quickstart</a></li><li class="chapter-item expanded "><a href="basics/index.html"><strong aria-hidden="true">3.</strong> Basics</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="basics/design.html"><strong aria-hidden="true">3.1.</strong> Design Principles</a></li></ol></li><li class="chapter-item expanded "><a href="references/index.html"><strong aria-hidden="true">4.</strong> Core References</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="references/suite.html"><strong aria-hidden="true">4.1.</strong> Benchmark Suite</a></li><li class="chapter-item expanded "><a href="references/runtime.html"><strong aria-hidden="true">4.2.</strong> Runtime</a></li><li class="chapter-item expanded "><a href="references/modifier.html"><strong aria-hidden="true">4.3.</strong> Modifier</a></li></ol></li><li class="chapter-item expanded "><a href="commands/index.html"><strong aria-hidden="true">5.</strong> Command References</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="commands/runbms.html"><strong aria-hidden="true">5.1.</strong> runbms</a></li><li class="chapter-item expanded "><a href="commands/minheap.html"><strong aria-hidden="true">5.2.</strong> minheap</a></li><li class="chapter-item expanded "><a href="commands/fillin.html"><strong aria-hidden="true">5.3.</strong> fillin</a></li></ol></li><li class="chapter-item expanded "><a href="cookbook/index.html"><strong aria-hidden="true">6.</strong> Cookbook</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="cookbook/perf_events.html"><strong aria-hidden="true">6.1.</strong> Performance Event Monitoring</a></li></ol></li><li class="chapter-item expanded "><a href="faq.html"><strong aria-hidden="true">7.</strong> Frequently Asked Questions</a></li><li class="chapter-item expanded "><a href="changelog.html"><strong aria-hidden="true">8.</strong> Changelog</a></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString().split("#")[0].split("?")[0];
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
