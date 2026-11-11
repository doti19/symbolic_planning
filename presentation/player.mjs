import { actionLabel, duration, goalLabel, goalStatus, parseVfg, sampleFrame, stepMs } from "./vfg.mjs";
import { drawScene, loadTextures } from "./render.mjs";

const byId = id => document.getElementById(id);
const app = byId("app");
const canvas = byId("map");
const ctx = canvas.getContext("2d");
const demo = byId("demo");
const file = byId("file");
const status = byId("status");
const seek = byId("seek");
const play = byId("play");
const previous = byId("previous");
const next = byId("next");
const speed = byId("speed");
const present = byId("present");
const exportButton = byId("export");
const goalBadge = byId("stage-goal");
const goalList = byId("goal-list");
const steps = byId("steps");

let view;
let position = 0;
let playing = false;
let lastTick = null;
let requestId = 0;
let activeStep = -1;
let lastDrawnSprites = null;
let loadVersion = 0;

function report(message, isError = false) {
  status.textContent = message;
  status.toggleAttribute("data-error", isError);
}

function drawFrame(frame) {
  const { clientWidth: width, clientHeight: height } = canvas;
  if (!width || !height) return;
  const scale = window.devicePixelRatio || 1;
  const pixelWidth = Math.round(width * scale);
  const pixelHeight = Math.round(height * scale);
  if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;
    lastDrawnSprites = null;
  }
  if (frame.sprites === lastDrawnSprites) return;
  lastDrawnSprites = frame.sprites;

  ctx.setTransform(pixelWidth / width, 0, 0, pixelHeight / height, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const padding = Math.max(12, Math.min(26, height * 0.035 - 6));
  drawScene(ctx, view.scene, view.textures, frame.sprites, width, height, padding);
}

function updateStep(index) {
  if (index === activeStep) return;
  const { scene, stepButtons, goalRows } = view;
  stepButtons[activeStep]?.removeAttribute("aria-current");
  activeStep = index;
  stepButtons[index].setAttribute("aria-current", "step");
  seek.value = index;
  seek.setAttribute("aria-valuetext", actionLabel(scene.stages[index].label));
  byId("step-count").textContent = `Step ${index} / ${scene.stages.length - 1}`;
  previous.disabled = index === 0;
  next.disabled = index === scene.stages.length - 1;

  const goal = goalStatus(scene, index);
  goalBadge.textContent = goal.label;
  goalBadge.toggleAttribute("data-reached", goal.reached);
  for (const [key, row] of goalRows) {
    row.toggleAttribute("data-reached", goal.achieved.has(key));
    row.querySelector(".sr-only").textContent = goal.achieved.has(key) ? "Reached " : "Pending ";
  }
}

function render() {
  if (!view) return;
  const frame = sampleFrame(view.scene, position);
  drawFrame(frame);
  updateStep(frame.index);
  const atEnd = frame.index === view.scene.stages.length - 1;
  play.textContent = playing ? "Pause" : atEnd ? "Replay" : "Play";
}

function pause() {
  playing = false;
  cancelAnimationFrame(requestId);
  lastTick = null;
}

function tick(now) {
  const end = duration(view.scene);
  if (lastTick !== null) {
    position = Math.min(end, position + (now - lastTick) * Number(speed.value));
  }
  lastTick = now;
  if (position >= end) pause();
  render();
  if (playing) requestId = requestAnimationFrame(tick);
}

function togglePlayback() {
  if (!view || view.scene.stages.length < 2) return;
  if (playing) {
    pause();
  } else {
    if (activeStep === view.scene.stages.length - 1) position = 0;
    playing = true;
    requestId = requestAnimationFrame(tick);
  }
  render();
}

function seekTo(index) {
  if (!view) return;
  pause();
  const target = Math.min(view.scene.stages.length - 1, Math.max(0, index));
  position = target * stepMs;
  render();
}

function addSteps(scene) {
  steps.replaceChildren();
  return scene.stages.map((stage, index) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    const count = document.createElement("span");
    count.textContent = index;
    const label = document.createElement("span");
    label.textContent = actionLabel(stage.label);
    button.title = stage.label;
    button.append(count, label);
    button.addEventListener("click", () => seekTo(index));
    li.append(button);
    steps.append(li);
    return button;
  });
}

function addGoals(scene) {
  goalList.replaceChildren();
  if (!scene.goals.length) {
    const li = document.createElement("li");
    li.toggleAttribute("data-unknown", true);
    li.textContent = "This VFG contains no goal metadata.";
    goalList.append(li);
  }
  return new Map(scene.goals.map(goal => {
    const li = document.createElement("li");
    const state = document.createElement("span");
    state.className = "sr-only";
    const label = document.createElement("span");
    label.textContent = goalLabel(goal);
    li.append(state, label);
    goalList.append(li);
    return [goal, li];
  }));
}

async function loadScene(title, selection, read) {
  const version = ++loadVersion;
  report("Loading visualization…");
  try {
    const scene = parseVfg(await read());
    const textures = await loadTextures(scene);
    if (version !== loadVersion) return;
    pause();
    view = {
      title, selection, scene, textures, stepButtons: addSteps(scene), goalRows: addGoals(scene),
    };
    position = 0;
    activeStep = -1;
    byId("scenario").textContent = title;
    byId("present-title").textContent = title;
    demo.value = selection;
    seek.max = scene.stages.length - 1;
    seek.disabled = play.disabled = scene.stages.length < 2;
    present.disabled = false;
    if (!isRecording) exportButton.disabled = !canRecord;
    report("");
    render();
  } catch (error) {
    if (version !== loadVersion) return;
    if (view) demo.value = view.selection;
    else byId("scenario").textContent = "Open a VFG to begin";
    report(error.message, true);
  }
}

function loadDemo(selection) {
  const title = demo.selectedOptions[0].textContent;
  return loadScene(title, selection, async () => {
    const response = await fetch(`demos/${selection}.vfg`);
    if (!response.ok) throw new Error("Demo unavailable. Start the local server from the repository root.");
    return response.text();
  });
}

function togglePresentation(force) {
  if (!view) return;
  const enabled = app.toggleAttribute("data-presenting", force);
  present.setAttribute("aria-pressed", String(enabled));
  present.textContent = enabled ? "Exit presentation" : "Present";
}

new ResizeObserver(() => render()).observe(canvas);
demo.addEventListener("change", () => loadDemo(demo.value));
byId("open").addEventListener("click", () => file.click());
file.addEventListener("change", () => {
  const selected = file.files[0];
  if (!selected) return;
  file.value = "";
  loadScene(selected.name.replace(/\.(vfg|json)$/i, ""), "local", () => selected.text());
});
play.addEventListener("click", togglePlayback);
previous.addEventListener("click", () => seekTo(activeStep - 1));
next.addEventListener("click", () => seekTo(activeStep + 1));
seek.addEventListener("input", () => seekTo(Number(seek.value)));
present.addEventListener("click", () => togglePresentation(!app.hasAttribute("data-presenting")));

document.addEventListener("keydown", event => {
  if (event.key === "Escape" && app.hasAttribute("data-presenting")) {
    togglePresentation(false);
    return;
  }
  if (!view || event.altKey || event.ctrlKey || event.metaKey ||
      event.target.closest("button, select, input")) return;
  switch (event.key) {
    case " ": togglePlayback(); break;
    case "ArrowLeft": seekTo(activeStep - 1); break;
    case "ArrowRight": seekTo(activeStep + 1); break;
    case "Home": seekTo(0); break;
    case "End": seekTo(view.scene.stages.length - 1); break;
    case "f":
    case "F": togglePresentation(!app.hasAttribute("data-presenting")); break;
    default: return;
  }
  event.preventDefault();
});

const canRecord = typeof MediaRecorder !== "undefined" && typeof canvas.captureStream === "function";
let isRecording = false;

function drawVideoFrame(ctx, recording, time) {
  const { title, scene, textures } = recording;
  const frame = sampleFrame(scene, time);
  const goal = goalStatus(scene, frame.index);
  ctx.fillStyle = "#131e2c";
  ctx.fillRect(0, 0, 1920, 1080);
  ctx.save();
  ctx.translate(0, 84);
  drawScene(ctx, scene, textures, frame.sprites, 1920, 980, 22);
  ctx.restore();
  ctx.font = '700 33px "DM Sans", sans-serif';
  ctx.textBaseline = "middle";
  ctx.textAlign = "left";
  ctx.fillStyle = "#f0f6fa";
  ctx.fillText(title, 54, 48, 1350);
  ctx.textAlign = "right";
  ctx.fillStyle = goal.reached ? "#a1ebd9" : "#e4edf7";
  ctx.fillText(goal.label, 1866, 48);
}

async function recordVideo(recording, rate) {
  await document.fonts.ready;
  const video = document.createElement("canvas");
  video.width = 1920;
  video.height = 1080;
  const videoCtx = video.getContext("2d");
  drawVideoFrame(videoCtx, recording, 0);
  const stream = video.captureStream(30);
  try {
    const mimeType = [
      "video/mp4;codecs=avc1.420028",
      "video/webm;codecs=vp9",
      "video/webm",
    ].find(type => MediaRecorder.isTypeSupported(type));
    if (!mimeType) throw new Error("This browser cannot record MP4 or WebM.");

    const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 8_000_000 });
    const end = duration(recording.scene);
    return await new Promise((resolve, reject) => {
      const chunks = [];
      let frameId;
      recorder.ondataavailable = event => {
        if (event.data.size) chunks.push(event.data);
      };
      recorder.onstop = () => {
        if (chunks.length) resolve(new Blob(chunks, { type: recorder.mimeType }));
        else reject(new Error("The browser returned an empty recording."));
      };
      recorder.onerror = event => {
        cancelAnimationFrame(frameId);
        reject(event.error);
      };
      recorder.start();
      const start = performance.now();
      const advance = now => {
        const time = Math.min(end, Math.max(0, (now - start) * rate));
        drawVideoFrame(videoCtx, recording, time);
        if (time < end) frameId = requestAnimationFrame(advance);
        else recorder.stop();
      };
      frameId = requestAnimationFrame(advance);
    });
  } finally {
    for (const track of stream.getTracks()) track.stop();
  }
}

exportButton.addEventListener("click", async () => {
  if (!view || isRecording) return;
  const recording = view;
  isRecording = exportButton.disabled = true;
  report("Recording video… Keep this tab visible.");
  try {
    const blob = await recordVideo(recording, Number(speed.value));
    const extension = blob.type.startsWith("video/mp4") ? "mp4" : "webm";
    const name = recording.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${name || "planimation"}.${extension}`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 10_000);
    report(`Saved ${link.download}`);
  } catch (error) {
    report(`Recording failed. ${error.message}`, true);
  } finally {
    isRecording = false;
    exportButton.disabled = false;
  }
});

loadDemo(demo.value);
