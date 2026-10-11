// Pure Tic-Tac-Toe Game State & Rules
const WINNING_COMBOS = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6]
];

class GameState {
  constructor(mode, p1Name, p2Name, p1Piece) {
    this.mode = mode || 'ai';
    this.p1Name = (p1Name && p1Name.trim()) ? p1Name.trim() : 'Player 1';
    this.p2Name = (p2Name && p2Name.trim()) ? p2Name.trim() : (mode === 'ai' ? 'RL-Agent' : 'Player 2');
    this.p1Piece = p1Piece || 'X';

    if (this.p1Piece === 'X') {
      this.xName = this.p1Name;
      this.oName = this.p2Name;
      this.aiPiece = 2; // O
    } else {
      this.xName = this.p2Name;
      this.oName = this.p1Name;
      this.aiPiece = 1; // X
    }

    this.board = Array(9).fill(0);
    this.currentPlayer = 1; // 1 = X, 2 = O
    this.gameOver = false;
    this.winner = 0; // 0 = none/draw, 1 = X, 2 = O
    this.winCells = [];
    this.scores = { X: 0, O: 0, D: 0 };
  }

  checkWinner() {
    for (const [a, b, c] of WINNING_COMBOS) {
      if (this.board[a] !== 0 && this.board[a] === this.board[b] && this.board[a] === this.board[c]) {
        return { winner: this.board[a], cells: [a, b, c] };
      }
    }
    return { winner: 0, cells: [] };
  }

  makeMove(idx) {
    if (idx < 0 || idx > 8 || this.board[idx] !== 0 || this.gameOver) {
      return { success: false };
    }

    this.board[idx] = this.currentPlayer;
    const { winner, cells } = this.checkWinner();

    if (winner !== 0) {
      this.gameOver = true;
      this.winner = winner;
      this.winCells = cells;
      this.scores[winner === 1 ? 'X' : 'O']++;
      return { success: true, outcome: winner, cells };
    } else if (!this.board.includes(0)) {
      this.gameOver = true;
      this.winner = 0;
      this.winCells = [];
      this.scores.D++;
      return { success: true, outcome: 0, cells: [] };
    } else {
      this.currentPlayer = this.currentPlayer === 1 ? 2 : 1;
      return { success: true, outcome: null };
    }
  }

  reset() {
    const nextFirst = this.winner !== 0 ? this.winner : 1;
    this.board = Array(9).fill(0);
    this.currentPlayer = nextFirst;
    this.gameOver = false;
    this.winner = 0;
    this.winCells = [];
    return nextFirst;
  }
}

window.GameState = GameState;
