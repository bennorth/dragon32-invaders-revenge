const btns = [
    document.getElementById("sample-btn-1"),
    document.getElementById("sample-btn-2"),
];

const sounds = [
    new Howl({ src: ["defender-base-hit-0.wav"], onend: () => { btns[0].removeAttribute("disabled"); }}),
    new Howl({ src: ["synth-defender-base-hit-0.wav"], onend: () => { btns[1].removeAttribute("disabled"); }}),
];

btns.forEach((btn, i) => {
    const sound = sounds[i];
    btn.addEventListener("click", () => {
	btn.setAttribute("disabled", "");
	sound.play();
    });
});
