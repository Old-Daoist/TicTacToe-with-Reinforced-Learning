// Pure Reinforcement Learning (DQN) Inference Engine in JavaScript
class AIAgent {
  constructor() {
    this.weights = window.MODEL_WEIGHTS || null;
  }

  forward(obs) {
    if (!this.weights) return null;
    const { w1, b1, w2, b2, w3, b3 } = this.weights;

    // Layer 1: 9 -> 256 (Linear + ReLU)
    const h1 = new Float32Array(256);
    for (let i = 0; i < 256; i++) {
      let sum = b1[i];
      const row = w1[i];
      for (let j = 0; j < 9; j++) {
        sum += row[j] * obs[j];
      }
      h1[i] = sum > 0 ? sum : 0; // ReLU
    }

    // Layer 2: 256 -> 256 (Linear + ReLU)
    const h2 = new Float32Array(256);
    for (let i = 0; i < 256; i++) {
      let sum = b2[i];
      const row = w2[i];
      for (let j = 0; j < 256; j++) {
        sum += row[j] * h1[j];
      }
      h2[i] = sum > 0 ? sum : 0; // ReLU
    }

    // Output Layer: 256 -> 9 (Q-values)
    const q = new Float32Array(9);
    for (let i = 0; i < 9; i++) {
      let sum = b3[i];
      const row = w3[i];
      for (let j = 0; j < 256; j++) {
        sum += row[j] * h2[j];
      }
      q[i] = sum;
    }

    return q;
  }

  getMove(board, aiPiece) {
    const empty = [];
    for (let i = 0; i < 9; i++) {
      if (board[i] === 0) empty.push(i);
    }
    if (empty.length === 0) return null;

    if (this.weights) {
      // RL Observation: +1 for AI piece, -1 for opponent piece, 0 for empty
      const obs = board.map(x => (x === aiPiece ? 1 : (x !== 0 ? -1 : 0)));
      const q = this.forward(obs);

      if (q) {
        // Select legal action with highest predicted Q-value
        let bestMove = empty[0];
        let bestQ = q[bestMove];
        for (let i = 1; i < empty.length; i++) {
          const idx = empty[i];
          if (q[idx] > bestQ) {
            bestQ = q[idx];
            bestMove = idx;
          }
        }
        return bestMove;
      }
    }

    // Fallback if weights missing
    const randIdx = Math.floor(Math.random() * empty.length);
    return empty[randIdx];
  }
}

window.AIAgent = AIAgent;
