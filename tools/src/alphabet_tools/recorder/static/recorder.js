const TOKEN = document.querySelector('meta[name="recorder-token"]').content;
const WAV_HEADER_BYTES = 44;
const INT16_MAX = 0x7fff;

const elements = Object.fromEntries(
  ['language', 'progress', 'clip-id', 'clip-text', 'record', 'play', 'save', 'previous', 'next',
    'next-missing', 'status', 'clip-list'].map((id) => [id, document.getElementById(id)]),
);

const state = { clips: [], index: 0, isRecording: false, chunks: [], sampleRate: 48000, wav: null };
let audio = null;

function setStatus(text) {
  elements.status.textContent = text;
}

function encodeWav(chunks, sampleRate) {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const view = new DataView(new ArrayBuffer(WAV_HEADER_BYTES + length * 2));
  const writeText = (offset, text) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  writeText(0, 'RIFF');
  view.setUint32(4, 36 + length * 2, true);
  writeText(8, 'WAVE');
  writeText(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeText(36, 'data');
  view.setUint32(40, length * 2, true);
  let offset = WAV_HEADER_BYTES;
  for (const chunk of chunks) {
    for (const sample of chunk) {
      view.setInt16(offset, Math.max(-1, Math.min(1, sample)) * INT16_MAX, true);
      offset += 2;
    }
  }
  return new Blob([view], { type: 'audio/wav' });
}

async function ensureAudio() {
  if (audio) return audio;
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
  });
  const context = new AudioContext();
  await context.audioWorklet.addModule('/worklet.js');
  const source = context.createMediaStreamSource(stream);
  const node = new AudioWorkletNode(context, 'capture-processor');
  node.port.onmessage = (event) => {
    if (state.isRecording) state.chunks.push(event.data);
  };
  source.connect(node);
  audio = { context };
  state.sampleRate = context.sampleRate;
  return audio;
}

async function toggleRecording() {
  try {
    const { context } = await ensureAudio();
    await context.resume();
  } catch (error) {
    setStatus(`Microphone not available: ${error.message}`);
    return;
  }
  if (!state.isRecording) {
    state.chunks = [];
    state.isRecording = true;
    setStatus('Recording… press Space to stop');
  } else {
    state.isRecording = false;
    state.wav = encodeWav(state.chunks, state.sampleRate);
    setStatus('Recorded. Play it, then save or record again.');
  }
  render();
}

function playRecording() {
  if (!state.wav) return;
  const url = URL.createObjectURL(state.wav);
  const player = new Audio(url);
  player.addEventListener('ended', () => URL.revokeObjectURL(url));
  player.play();
}

async function saveRecording() {
  const clip = state.clips[state.index];
  if (!state.wav || !clip) return;
  const response = await fetch(`/api/recordings/${encodeURIComponent(clip.id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'audio/wav', 'X-Recorder-Token': TOKEN },
    body: state.wav,
  });
  if (!response.ok) {
    setStatus(`Save failed (${response.status}). Try again.`);
    return;
  }
  clip.isRecorded = true;
  setStatus(`Saved ${clip.id}`);
  moveTo(state.index + 1);
}

function moveTo(index) {
  if (state.isRecording) return;
  state.index = Math.max(0, Math.min(index, state.clips.length - 1));
  state.wav = null;
  render();
}

function moveToNextMissing() {
  const count = state.clips.length;
  for (let step = 1; step <= count; step += 1) {
    const candidate = (state.index + step) % count;
    if (!state.clips[candidate].isRecorded) return moveTo(candidate);
  }
  setStatus('Everything is recorded 🎉');
}

function renderList() {
  const items = state.clips.map((clip, index) => {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${clip.text}  (${clip.id})`;
    button.classList.toggle('is-current', index === state.index);
    button.classList.toggle('is-recorded', clip.isRecorded);
    button.addEventListener('click', () => moveTo(index));
    item.append(button);
    return item;
  });
  elements['clip-list'].replaceChildren(...items);
  elements['clip-list'].children[state.index]?.scrollIntoView({ block: 'nearest' });
}

function render() {
  const clip = state.clips[state.index];
  const recorded = state.clips.filter((c) => c.isRecorded).length;
  elements.progress.textContent = `${recorded} / ${state.clips.length} recorded`;
  elements['clip-id'].textContent = clip ? `${clip.id}${clip.isRecorded ? '  ✓ already recorded' : ''}` : '';
  elements['clip-text'].textContent = clip ? clip.text : '';
  elements.record.textContent = state.isRecording ? '■ Stop' : '● Record';
  elements.record.classList.toggle('is-recording', state.isRecording);
  elements.play.disabled = !state.wav || state.isRecording;
  elements.save.disabled = !state.wav || state.isRecording;
  renderList();
}

function handleKey(event) {
  if (event.repeat || event.target instanceof HTMLButtonElement && event.key === 'Enter') return;
  const actions = {
    ' ': toggleRecording,
    p: playRecording,
    Enter: saveRecording,
    ArrowLeft: () => moveTo(state.index - 1),
    ArrowRight: () => moveTo(state.index + 1),
  };
  const action = actions[event.key];
  if (!action) return;
  event.preventDefault();
  action();
}

async function start() {
  const response = await fetch('/api/clips');
  const data = await response.json();
  state.clips = data.clips;
  elements.language.textContent = data.language;
  elements.record.addEventListener('click', toggleRecording);
  elements.play.addEventListener('click', playRecording);
  elements.save.addEventListener('click', saveRecording);
  elements.previous.addEventListener('click', () => moveTo(state.index - 1));
  elements.next.addEventListener('click', () => moveTo(state.index + 1));
  elements['next-missing'].addEventListener('click', moveToNextMissing);
  document.addEventListener('keydown', handleKey);
  const firstMissing = state.clips.findIndex((clip) => !clip.isRecorded);
  moveTo(firstMissing === -1 ? 0 : firstMissing);
}

start();
