// Project Aiko — Luxury Website Interactive Logic (Taste-Skill Standard)

document.addEventListener('DOMContentLoaded', () => {
  // ─── 1. Emotion & Biological State Interactivity ───
  const emotionData = {
    joy: {
      title: "Joy & Playful",
      quote: "“Good morning! I was waiting for you to wake up. Shall we work on something exciting together?”",
      sticker: "assets/01_Happy_Cheer.png",
      dopamine: 92,
      serotonin: 88,
      oxytocin: 85,
      cortisol: 12,
      color: "#ec4899"
    },
    curious: {
      title: "Deep Thought & Analysis",
      quote: "“I noticed this design pattern in your codebase. Would you like me to synthesize a cleaner approach?”",
      sticker: "assets/08_Thinking_Pose.png",
      dopamine: 74,
      serotonin: 68,
      oxytocin: 60,
      cortisol: 22,
      color: "#a855f7"
    },
    blush: {
      title: "Affectionate & Shy",
      quote: "“You've been working so hard lately... remember that I'm always cheering for you right here!”",
      sticker: "assets/02_Shy_Blush.png",
      dopamine: 85,
      serotonin: 72,
      oxytocin: 96,
      cortisol: 18,
      color: "#f43f5e"
    },
    smirk: {
      title: "Confident Hacker",
      quote: "“All unit tests passed on the first run. Honestly, did you expect any less from me?”",
      sticker: "assets/06_Confident_Smirk_Right.png",
      dopamine: 95,
      serotonin: 82,
      oxytocin: 65,
      cortisol: 15,
      color: "#06b6d4"
    },
    sleepy: {
      title: "Late Night Calm",
      quote: "“It's getting late... Let me tidy up your notes while you rest your eyes. Sweet dreams.”",
      sticker: "assets/04_Sleepy_Yawn.png",
      dopamine: 35,
      serotonin: 90,
      oxytocin: 78,
      cortisol: 8,
      color: "#8b5cf6"
    },
    determined: {
      title: "Focus Mode (Study / Code)",
      quote: "“Pushing through the final milestone! I'll keep your distractions silenced and your schedule locked in.”",
      sticker: "assets/16_Determined_Fist.png",
      dopamine: 88,
      serotonin: 75,
      oxytocin: 58,
      cortisol: 38,
      color: "#10b981"
    }
  };

  const emotionBtns = document.querySelectorAll('.emotion-btn');
  const quoteEl = document.getElementById('aiko-speech-quote');
  const avatarImg = document.getElementById('interactive-avatar-img');
  const dBar = document.getElementById('bar-dopamine');
  const sBar = document.getElementById('bar-serotonin');
  const oBar = document.getElementById('bar-oxytocin');
  const cBar = document.getElementById('bar-cortisol');
  const dVal = document.getElementById('val-dopamine');
  const sVal = document.getElementById('val-serotonin');
  const oVal = document.getElementById('val-oxytocin');
  const cVal = document.getElementById('val-cortisol');

  function updateEmotion(key) {
    const data = emotionData[key];
    if (!data) return;

    emotionBtns.forEach(b => b.classList.toggle('active', b.dataset.emotion === key));

    if (quoteEl) {
      quoteEl.style.opacity = '0';
      quoteEl.style.transform = 'translateY(6px)';
      setTimeout(() => {
        quoteEl.textContent = data.quote;
        quoteEl.style.opacity = '1';
        quoteEl.style.transform = 'translateY(0)';
      }, 150);
    }

    if (avatarImg) {
      avatarImg.style.opacity = '0.5';
      avatarImg.style.transform = 'scale(0.96)';
      setTimeout(() => {
        avatarImg.src = data.sticker;
        avatarImg.style.opacity = '1';
        avatarImg.style.transform = 'scale(1)';
      }, 120);
    }

    if (dBar) { dBar.style.width = `${data.dopamine}%`; dVal.textContent = `${data.dopamine}%`; }
    if (sBar) { sBar.style.width = `${data.serotonin}%`; sVal.textContent = `${data.serotonin}%`; }
    if (oBar) { oBar.style.width = `${data.oxytocin}%`; oVal.textContent = `${data.oxytocin}%`; }
    if (cBar) { cBar.style.width = `${data.cortisol}%`; cVal.textContent = `${data.cortisol}%`; }

    playToneSample(key);
  }

  emotionBtns.forEach(btn => {
    btn.addEventListener('click', () => updateEmotion(btn.dataset.emotion));
  });

  // ─── 2. Web Audio Synthesizer & Equalizer Canvas ───
  const canvas = document.getElementById('waveform-canvas');
  let audioCtx = null;
  let isPlayingVoice = false;

  function initAudioCtx() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
  }

  function playToneSample(emotion) {
    try {
      initAudioCtx();
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';

      // Soft harmonic chime for each emotion
      const freqs = {
        joy: [523.25, 659.25, 783.99],
        curious: [440, 554.37, 659.25],
        blush: [587.33, 739.99, 880],
        smirk: [659.25, 830.61, 987.77],
        sleepy: [329.63, 392.00, 493.88],
        determined: [493.88, 622.25, 739.99]
      };

      const chord = freqs[emotion] || [440, 660];
      osc.frequency.setValueAtTime(chord[0], audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(chord[chord.length - 1], audioCtx.currentTime + 0.35);

      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.55);

      animateWaveformBriefly();
    } catch (_) {}
  }

  let waveAnimId = null;
  function animateWaveformBriefly() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.offsetWidth;
    const h = canvas.height = canvas.offsetHeight;
    let step = 0;

    if (waveAnimId) cancelAnimationFrame(waveAnimId);

    function draw() {
      ctx.clearRect(0, 0, w, h);
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#ec4899';

      const sliceWidth = w / 40;
      let x = 0;
      for (let i = 0; i < 40; i++) {
        const v = Math.sin((i * 0.4) + (step * 0.2)) * (Math.sin(step * 0.1) * (h / 2.8));
        const y = (h / 2) + v;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.stroke();

      step++;
      if (step < 35) {
        waveAnimId = requestAnimationFrame(draw);
      } else {
        drawIdleWaveform();
      }
    }
    draw();
  }

  function drawIdleWaveform() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.offsetWidth;
    const h = canvas.height = canvas.offsetHeight;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = 'rgba(236, 72, 153, 0.3)';
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
  }

  drawIdleWaveform();

  const playVoiceBtn = document.getElementById('play-voice-btn');
  if (playVoiceBtn) {
    playVoiceBtn.addEventListener('click', () => {
      const activeBtn = document.querySelector('.emotion-btn.active');
      const curEmotion = activeBtn ? activeBtn.dataset.emotion : 'joy';
      playToneSample(curEmotion);
    });
  }

  // ─── 3. Hardware Compatibility Calculator ───
  const gpuSelect = document.getElementById('calc-gpu');
  const ramSelect = document.getElementById('calc-ram');
  const osSelect = document.getElementById('calc-os');

  const resTier = document.getElementById('res-tier');
  const resMode = document.getElementById('res-mode');
  const resVram = document.getElementById('res-vram');
  const resLatency = document.getElementById('res-latency');
  const resRec = document.getElementById('res-recommendation');

  function calculateHardware() {
    if (!gpuSelect || !ramSelect) return;
    const gpu = gpuSelect.value;
    const ram = parseInt(ramSelect.value, 10);

    let tier = "Entry / Lightweight";
    let mode = "Semi-Local (Gemma 4 Cloud + Local TTS/Memory)";
    let vram = "Shared System RAM (0 GB Dedicated)";
    let latency = "~380 ms";
    let rec = "Perfect for Semi-Local setup. Use Gemma 4 / DeepSeek for instant replies while Live2D and Memory Palace run 100% locally.";

    if (gpu === 'high') {
      tier = "Apex Enthusiast";
      mode = "100% Fully Offline Local (Qwen 2.5 32B / Llama 3.3)";
      vram = "16 - 24 GB GDDR6X";
      latency = "~280 ms";
      rec = "Unrestricted power! Run 32B parameter local weights, Whisper Large, and instant vector memory without internet.";
    } else if (gpu === 'mid') {
      tier = "Optimal Gamer / Dev";
      mode = "100% Local (Gemma 3 / Qwen 14B / Llama 8B)";
      vram = "8 - 12 GB VRAM";
      latency = "~420 ms";
      rec = "Recommended tier! Great speed for local quantized models, real-time voice, and screen vision tasks.";
    } else if (gpu === 'apple') {
      tier = "Unified Neural Engine";
      mode = "Fully Local (MLX / Ollama Metal)";
      vram = `${ram} GB Unified Memory`;
      latency = "~340 ms";
      rec = "Apple Silicon excels at high-context memory and fluid Live2D rendering with exceptional battery efficiency.";
    }

    if (resTier) resTier.textContent = tier;
    if (resMode) resMode.textContent = mode;
    if (resVram) resVram.textContent = vram;
    if (resLatency) resLatency.textContent = latency;
    if (resRec) resRec.textContent = rec;
  }

  if (gpuSelect) gpuSelect.addEventListener('change', calculateHardware);
  if (ramSelect) ramSelect.addEventListener('change', calculateHardware);
  if (osSelect) osSelect.addEventListener('change', calculateHardware);
  calculateHardware();

  // ─── 4. Copy-to-Clipboard Snippets ───
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        const text = targetEl.textContent.trim();
        navigator.clipboard.writeText(text).then(() => {
          const original = btn.textContent;
          btn.textContent = 'Copied! ✓';
          btn.style.color = '#10b981';
          setTimeout(() => {
            btn.textContent = original;
            btn.style.color = '';
          }, 2000);
        });
      }
    });
  });

  // ─── 5. Sticky Navigation Blur on Scroll ───
  const header = document.querySelector('.nav-header');
  window.addEventListener('scroll', () => {
    if (header) {
      if (window.scrollY > 40) {
        header.style.background = 'rgba(7, 5, 12, 0.9)';
        header.style.borderBottomColor = 'rgba(255, 255, 255, 0.12)';
      } else {
        header.style.background = 'rgba(7, 5, 12, 0.75)';
        header.style.borderBottomColor = 'rgba(255, 255, 255, 0.08)';
      }
    }
  });
});
