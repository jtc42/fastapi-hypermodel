const syncTabsByName = (tab) => () => {
    const selected = document.querySelector(`label[for=${tab.id}]`)
    const previousPosition = selected.getBoundingClientRect().top
    const labelSelector = '.tabbed-set > label, .tabbed-alternate > .tabbed-labels > label'

    Array.from(document.querySelectorAll(labelSelector))
        .filter(label => label.innerText === selected.innerText)
        .forEach(label => document.querySelector(`input[id=${label.getAttribute('for')}]`).click())

    // Preserve scroll position
    const currentPosition = selected.getBoundingClientRect().top
    const delta = currentPosition - previousPosition
    window.scrollBy(0, delta)
}

const tabSync = () => {
    document.querySelectorAll(".tabbed-set > input")
        .forEach(tab => tab.addEventListener("click", syncTabsByName(tab)))
}

tabSync();