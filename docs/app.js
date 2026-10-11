// ==========================================================================
// Tic-Tac-Toe Web Application Controller (Mobile & Desktop Responsive)
// ==========================================================================

(() => {
  // ---- Web Audio Synthesizer (Zero External Assets) ----
  class SoundFX {
    constructor() {
      this.ctx = null;
      this.muted = localStorage.getItem('ttt_muted') === 'true';
    }

    init() {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) this.ctx = new AudioCtx();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playTone(freq, type, duration, gainLevel = 0.15) {
      if (this.muted) return;
      this.init();
      if (!this.ctx) return;

      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        gain.gain.setValueAtTime(gainLevel, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + duration);
      } catch (e) {
        // audio fail-safe
      }
    }

    click() {
      this.playTone(320, 'sine', 0.08, 0.1);
    }

    place(piece) {
      if (piece === 'X') {
        this.playTone(440, 'triangle', 0.12, 0.18);
      } else {
        this.playTone(523.25, 'sine', 0.14, 0.18);
      }
    }

    win() {
      if (this.muted) return;
      [523.25, 659.25, 783.99, 1046.5].forEach((freq, idx) => {
        setTimeout(() => this.playTone(freq, 'triangle', 0.28, 0.2), idx * 100);
      });
    }

    draw() {
      if (this.muted) return;
      [392, 349.23, 329.63].forEach((freq, idx) => {
        setTimeout(() => this.playTone(freq, 'sine', 0.25, 0.15), idx * 120);
      });
    }
  }

  // ---- Match History Storage ----
  class HistoryStore {
    static get() {
      try {
        return JSON.parse(localStorage.getItem('ttt_history') || '[]');
      } catch (e) {
        return [];
      }
    }

    static add(winner, mode, p1Name, p2Name) {
      const history = this.get();
      let outcome = "Draw";
      if (winner === 1) outcome = `${p1Name} (X) Won`;
      else if (winner === 2) outcome = `${p2Name} (O) Won`;

      const entry = {
        id: Date.now(),
        outcome,
        mode: mode === 'ai' ? 'vs AI (RL)' : '2 Player (PvP)',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        date: new Date().toLocaleDateString()
      };

      history.unshift(entry);
      if (history.length > 20) history.pop();
      localStorage.setItem('ttt_history', JSON.stringify(history));
    }

    static clear() {
      localStorage.removeItem('ttt_history');
    }
  }

  // ---- Application State ----
  const sfx = new SoundFX();
  const aiAgent = new AIAgent();
  let gameState = null;
  let selectedMode = 'ai';
  let selectedPiece = 'X';
  let isAiThinking = false;

  // DOM Elements
  const viewMenu = document.getElementById('view-menu');
  const viewSetup = document.getElementById('view-setup');
  const viewGame = document.getElementById('view-game');

  const btnPlayAi = document.getElementById('btn-play-ai');
  const btnPlayPvp = document.getElementById('btn-play-pvp');
  const btnMenuHistory = document.getElementById('btn-menu-history');

  const setupTitle = document.getElementById('setup-title');
  const inputP1 = document.getElementById('input-p1');
  const inputP2 = document.getElementById('input-p2');
  const labelP2 = document.getElementById('label-p2');
  const btnPieceX = document.getElementById('btn-piece-x');
  const btnPieceO = document.getElementById('btn-piece-o');
  const btnStartGame = document.getElementById('btn-start-game');
  const btnSetupBack = document.getElementById('btn-setup-back');

  const btnBackMenu = document.getElementById('btn-back-menu');
  const btnRestart = document.getElementById('btn-restart');
  const btnMute = document.getElementById('btn-mute');
  const btnOpenHistory = document.getElementById('btn-open-history');

  const scoreX = document.getElementById('score-x');
  const scoreO = document.getElementById('score-o');
  const scoreD = document.getElementById('score-d');
  const nameX = document.getElementById('name-x');
  const nameO = document.getElementById('name-o');
  const statusBanner = document.getElementById('status-banner');
  const boardGrid = document.getElementById('board-grid');
  const winSvg = document.getElementById('win-svg');

  // Victory Scrim & Modal
  const victoryScrim = document.getElementById('victory-scrim');
  const victoryCard = document.getElementById('victory-card');
  const victoryTitle = document.getElementById('victory-title');
  const victoryIcon = document.getElementById('victory-icon');
  const victoryScoreSummary = document.getElementById('victory-score-summary');
  const btnNextGame = document.getElementById('btn-next-game');
  const btnVictoryMenu = document.getElementById('btn-victory-menu');

  // History Drawer & Scrim
  const historyScrim = document.getElementById('history-scrim');
  const historyDrawer = document.getElementById('history-drawer');
  const historyList = document.getElementById('history-list');
  const btnCloseHistory = document.getElementById('btn-close-history');
  const btnClearHistory = document.getElementById('btn-clear-history');

  // ---- Navigation ----
  function switchView(target) {
    [viewMenu, viewSetup, viewGame].forEach(v => v.classList.remove('active'));
    target.classList.add('active');
  }

  // ---- Audio & Haptic Feedback ----
  function updateMuteButton() {
    btnMute.textContent = sfx.muted ? '🔇' : '🔊';
  }

  function triggerHaptic(duration = 15) {
    if (navigator.vibrate) {
      try { navigator.vibrate(duration); } catch (e) {}
    }
  }

  // ---- Setup Screen Handler ----
  function openSetup(mode) {
    selectedMode = mode;
    selectedPiece = 'X';
    btnPieceX.classList.add('selected');
    btnPieceO.classList.remove('selected');

    if (mode === 'ai') {
      setupTitle.textContent = 'Single Player (vs AI)';
      labelP2.textContent = 'Opponent (Pure RL AI):';
      inputP2.value = 'RL-Agent (DQN)';
      inputP2.disabled = true;
    } else {
      setupTitle.textContent = 'Two Player Pass & Play';
      labelP2.textContent = 'Player 2 Name:';
      inputP2.value = 'Player 2';
      inputP2.disabled = false;
    }
    switchView(viewSetup);
  }

  // ---- Start Game ----
  function startGame() {
    const p1 = inputP1.value.trim() || 'Player 1';
    const p2 = inputP2.value.trim() || (selectedMode === 'ai' ? 'RL-Agent' : 'Player 2');

    gameState = new GameState(selectedMode, p1, p2, selectedPiece);
    isAiThinking = false;

    nameX.textContent = gameState.xName;
    nameO.textContent = gameState.oName;

    updateScores();
    renderBoard();
    updateStatus();
    switchView(viewGame);

    // If AI goes first
    if (gameState.mode === 'ai' && gameState.aiPiece === 1) {
      triggerAiMove();
    }
  }

  // ---- Board Rendering ----
  function renderBoard() {
    boardGrid.innerHTML = '';
    winSvg.innerHTML = '';

    for (let i = 0; i < 9; i++) {
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.dataset.index = i;

      const val = gameState.board[i];
      if (val !== 0) {
        cell.classList.add('taken');
        const piece = document.createElement('div');
        piece.className = `piece ${val === 1 ? 'piece-x' : 'piece-o'}`;
        cell.appendChild(piece);
      }

      if (gameState.winCells.includes(i)) {
        cell.classList.add('win-highlight');
      }

      cell.addEventListener('click', () => handleCellClick(i));
      boardGrid.appendChild(cell);
    }

    if (gameState.winCells.length === 3) {
      drawWinLine(gameState.winCells);
    }
  }

  function handleCellClick(idx) {
    if (!gameState || gameState.gameOver || isAiThinking) return;
    if (gameState.board[idx] !== 0) return;

    // In AI mode, prevent human clicks during AI turn
    if (gameState.mode === 'ai' && gameState.currentPlayer === gameState.aiPiece) return;

    sfx.place(gameState.currentPlayer === 1 ? 'X' : 'O');
    triggerHaptic(15);

    const res = gameState.makeMove(idx);
    if (!res.success) return;

    renderBoard();
    updateScores();
    updateStatus();

    if (res.outcome !== null && res.outcome !== undefined) {
      handleGameOver(res.outcome);
    } else if (gameState.mode === 'ai' && gameState.currentPlayer === gameState.aiPiece) {
      triggerAiMove();
    }
  }

  function triggerAiMove() {
    if (!gameState || gameState.gameOver) return;
    isAiThinking = true;
    updateStatus();

    // Natural 300ms reaction delay for smooth human-like gameplay
    setTimeout(() => {
      if (!gameState || gameState.gameOver) {
        isAiThinking = false;
        return;
      }

      const move = aiAgent.getMove(gameState.board, gameState.aiPiece);
      if (move !== null && move !== undefined) {
        sfx.place(gameState.aiPiece === 1 ? 'X' : 'O');
        triggerHaptic(20);

        const res = gameState.makeMove(move);
        isAiThinking = false;
        renderBoard();
        updateScores();
        updateStatus();

        if (res.outcome !== null && res.outcome !== undefined) {
          handleGameOver(res.outcome);
        }
      } else {
        isAiThinking = false;
      }
    }, 320);
  }

  function updateStatus() {
    if (gameState.gameOver) {
      if (gameState.winner === 1) statusBanner.textContent = `🏆 ${gameState.xName} Wins!`;
      else if (gameState.winner === 2) statusBanner.textContent = `🏆 ${gameState.oName} Wins!`;
      else statusBanner.textContent = `🤝 It's a Draw!`;
    } else if (isAiThinking) {
      statusBanner.textContent = `🧠 AI Thinking...`;
    } else {
      const curName = gameState.currentPlayer === 1 ? gameState.xName : gameState.oName;
      const curPiece = gameState.currentPlayer === 1 ? 'X' : 'O';
      statusBanner.textContent = `${curName}'s Turn (${curPiece})`;
    }
  }

  function updateScores() {
    scoreX.textContent = gameState.scores.X;
    scoreO.textContent = gameState.scores.O;
    scoreD.textContent = gameState.scores.D;
  }

  function drawWinLine(cells) {
    const [c1, , c3] = cells;
    const r1 = Math.floor(c1 / 3), col1 = c1 % 3;
    const r3 = Math.floor(c3 / 3), col3 = c3 % 3;

    // Calculate percentage coordinates (0% to 100%)
    const x1 = (col1 * 33.33) + 16.66;
    const y1 = (r1 * 33.33) + 16.66;
    const x2 = (col3 * 33.33) + 16.66;
    const y2 = (r3 * 33.33) + 16.66;

    winSvg.innerHTML = `
      <line x1="${x1}%" y1="${y1}%" x2="${x2}%" y2="${y2}%" />
    `;
  }

  function handleGameOver(winner) {
    HistoryStore.add(winner, gameState.mode, gameState.xName, gameState.oName);

    if (winner !== 0) {
      sfx.win();
      triggerHaptic(40);
    } else {
      sfx.draw();
    }

    setTimeout(() => {
      showVictoryModal(winner);
    }, 900);
  }

  function showVictoryModal(winner) {
    if (winner === 1) {
      victoryIcon.textContent = '🏆';
      victoryTitle.textContent = `${gameState.xName} Wins!`;
    } else if (winner === 2) {
      victoryIcon.textContent = '🏆';
      victoryTitle.textContent = `${gameState.oName} Wins!`;
    } else {
      victoryIcon.textContent = '🤝';
      victoryTitle.textContent = `Match Drawn!`;
    }

    victoryScoreSummary.textContent = `${gameState.xName}: ${gameState.scores.X}  |  ${gameState.oName}: ${gameState.scores.O}  |  Draws: ${gameState.scores.D}`;
    victoryScrim.classList.add('open');
  }

  function nextGame() {
    victoryScrim.classList.remove('open');
    if (!gameState) return;

    const nextFirst = gameState.reset();
    isAiThinking = false;
    renderBoard();
    updateStatus();

    if (gameState.mode === 'ai' && gameState.aiPiece === nextFirst) {
      triggerAiMove();
    }
  }

  // ---- History Drawer Rendering ----
  function renderHistory() {
    const list = HistoryStore.get();
    historyList.innerHTML = '';

    if (list.length === 0) {
      historyList.innerHTML = `<div class="empty-history">No matches logged yet.<br>Play a game to see stats here!</div>`;
      return;
    }

    list.forEach(item => {
      const el = document.createElement('div');
      el.className = 'history-item';
      el.innerHTML = `
        <div>
          <div class="history-winner">${item.outcome}</div>
          <div class="history-date">${item.mode}</div>
        </div>
        <div class="history-date">${item.time}</div>
      `;
      historyList.appendChild(el);
    });
  }

  function openHistory() {
    renderHistory();
    historyScrim.classList.add('open');
    historyDrawer.classList.add('open');
  }

  function closeHistory() {
    historyDrawer.classList.remove('open');
    historyScrim.classList.remove('open');
  }

  // ---- Outside Click Dismissal (Crucial Requirement) ----
  victoryScrim.addEventListener('click', (e) => {
    if (e.target === victoryScrim) {
      victoryScrim.classList.remove('open');
    }
  });

  historyScrim.addEventListener('click', (e) => {
    if (e.target === historyScrim) {
      closeHistory();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (historyDrawer.classList.contains('open')) {
        closeHistory();
      } else if (victoryScrim.classList.contains('open')) {
        victoryScrim.classList.remove('open');
      }
    }
  });

  // ---- Event Listeners ----
  btnPlayAi.addEventListener('click', () => { sfx.click(); openSetup('ai'); });
  btnPlayPvp.addEventListener('click', () => { sfx.click(); openSetup('pvp'); });
  btnMenuHistory.addEventListener('click', () => { sfx.click(); openHistory(); });

  btnPieceX.addEventListener('click', () => {
    sfx.click();
    selectedPiece = 'X';
    btnPieceX.classList.add('selected');
    btnPieceO.classList.remove('selected');
  });

  btnPieceO.addEventListener('click', () => {
    sfx.click();
    selectedPiece = 'O';
    btnPieceO.classList.add('selected');
    btnPieceX.classList.remove('selected');
  });

  btnStartGame.addEventListener('click', () => { sfx.click(); startGame(); });
  btnSetupBack.addEventListener('click', () => { sfx.click(); switchView(viewMenu); });

  btnBackMenu.addEventListener('click', () => { sfx.click(); switchView(viewMenu); });
  btnRestart.addEventListener('click', () => { sfx.click(); nextGame(); });
  btnOpenHistory.addEventListener('click', () => { sfx.click(); openHistory(); });
  btnCloseHistory.addEventListener('click', () => { sfx.click(); closeHistory(); });

  btnClearHistory.addEventListener('click', () => {
    sfx.click();
    HistoryStore.clear();
    renderHistory();
  });

  btnNextGame.addEventListener('click', () => { sfx.click(); nextGame(); });
  btnVictoryMenu.addEventListener('click', () => {
    sfx.click();
    victoryScrim.classList.remove('open');
    switchView(viewMenu);
  });

  btnMute.addEventListener('click', () => {
    sfx.muted = !sfx.muted;
    localStorage.setItem('ttt_muted', sfx.muted);
    updateMuteButton();
    if (!sfx.muted) sfx.click();
  });

  // Initialize
  updateMuteButton();
  switchView(viewMenu);
})();
