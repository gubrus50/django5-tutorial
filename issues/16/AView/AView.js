
(function() {

    const selectors = [
        'h1','h2','h3','h4','h5',
        'p',
        'ul','li',
        'button',
        'input','select','textarea',
        '.AVcard','.AVbox','.AVgrid'
    ];
    var animatedElements, sections, load = input => {
        animatedElements = document.querySelectorAll(
        selectors.map(s => `${AV.S} ${s}`).join(', '));
        sections = document.querySelectorAll(AV.S);
        if (input=='run') AV.run(); 
    }

    window.AV = { 'S': '[class^="AView-"]', get $(){return[...document.querySelectorAll(AV.S)]}, load, run };
    AV.load('run');

    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        const windowHeight = window.innerHeight || document.documentElement.clientHeight;
        const windowWidth = window.innerWidth || document.documentElement.clientWidth;

        const visibleHeight = Math.min(rect.bottom, windowHeight) - Math.max(rect.top, 0);
        const visibleWidth = Math.min(rect.right, windowWidth) - Math.max(rect.left, 0);
        const totalArea = rect.height * rect.width;
        const visibleArea = visibleHeight * visibleWidth;

        return visibleArea / totalArea >= 0.15;
    }

    function checkSectionVisibility() {
        sections.forEach(section => {
            const isVisible = isElementInViewport(section);
            
            if (isVisible) {
                section.classList.add('visible');
            } else {
                section.classList.remove('visible');
            }
        });
    }

    function checkElementVisibility() {
        animatedElements.forEach(el => {
            const isVisible = isElementInViewport(el);
            
            if (isVisible) {
                el.classList.add('visible');
            } else {
                el.classList.remove('visible');
            }
        });
    }

    // Combined check function
    function run() {
        checkSectionVisibility();
        checkElementVisibility();
    }

    // Throttled scroll listener
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                run();
                ticking = false;
            });
            ticking = true;
        }
    });

    
    window.addEventListener('load', function() {
        setTimeout(run, 300);
    });

    window.addEventListener('resize', run);

})();