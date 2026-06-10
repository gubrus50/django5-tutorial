function isScrolledIntoView(el) {
    const rect = el.getBoundingClientRect()
    const elemTop = rect.top
    const elemBottom = rect.bottom
    return elemTop < window.innerHeight && elemBottom >= 0
}