/*
 * wopr.js — a WarGames-flavored console easter egg.
 *
 * Prints a banner to the browser console on every page and exposes a few
 * global commands, including a playable game of chess against "Joshua"
 * (rules enforced by the lazily-loaded chess.js). Console-only: invisible
 * to anyone who never opens DevTools. Loaded as an external file because the
 * site CSP (script-src 'self', no 'unsafe-inline') forbids inline scripts.
 */
(function () {
  "use strict";

  var AMBER = "color:#ffb86c;font-weight:bold";
  var GREEN = "color:#50fa7b";
  var DIM = "color:#6272a4";
  var BOARD = "color:#f8f8f2;font-size:13px;line-height:1.35";

  function say(line, style) {
    console.log("%c" + (line || ""), style || GREEN);
  }

  function menu() {
    console.log("%c  war()  %c— global thermonuclear war", AMBER, DIM);
    console.log("%c  chess()%c— a nice game of chess", AMBER, DIM);
  }

  // --- Banner (on load) ---
  say("GREETINGS PROFESSOR FALKEN.");
  say("");
  say("SHALL WE PLAY A GAME?");
  say("");
  menu();

  // --- war() ---
  var warCount = 0;
  window.war = function () {
    warCount += 1;
    if (warCount === 1) {
      say("WOULDN'T YOU PREFER A GOOD GAME OF CHESS?");
      say("");
      menu();
    } else {
      say("LAUNCHING...");
      setTimeout(function () {
        say("A STRANGE GAME.");
        say("THE ONLY WINNING MOVE IS NOT TO PLAY.");
        say("");
        say("HOW ABOUT A NICE GAME OF CHESS?  (type chess())", AMBER);
      }, 900);
    }
  };

  // --- Chess ---
  var game = null;
  var GLYPH = {
    wK: "♔", wQ: "♕", wR: "♖", wB: "♗", wN: "♘", wP: "♙",
    bK: "♚", bQ: "♛", bR: "♜", bB: "♝", bN: "♞", bP: "♟",
  };

  function loadChess(cb) {
    if (window.Chess) return cb();
    var tag = document.getElementById("wopr");
    var src = tag && tag.dataset ? tag.dataset.chessSrc : null;
    if (!src) {
      say("Joshua can't find the board. (chess.js missing)", AMBER);
      return;
    }
    var s = document.createElement("script");
    s.src = src;
    s.onload = cb;
    s.onerror = function () {
      say("Joshua can't find the board. (chess.js failed to load)", AMBER);
    };
    document.head.appendChild(s);
  }

  function render() {
    var b = game.board(); // index 0 = rank 8
    var out = "\n";
    for (var r = 0; r < 8; r++) {
      out += (8 - r) + " ";
      for (var f = 0; f < 8; f++) {
        var sq = b[r][f];
        out += " " + (sq ? GLYPH[sq.color + sq.type.toUpperCase()] : "·");
      }
      out += "\n";
    }
    out += "   a b c d e f g h\n";
    console.log("%c" + out, BOARD);
  }

  function instructions() {
    console.log("%cYOU ARE WHITE. JOSHUA IS BLACK.", GREEN);
    console.log("%c  move('e4')%c  make a move  (e4, Nf3, O-O, e2e4, e7e8q ...)", AMBER, DIM);
    console.log("%c  moves()%c     list your legal moves", AMBER, DIM);
    console.log("%c  board()%c     redraw the board", AMBER, DIM);
    console.log("%c  chess()%c     start a new game", AMBER, DIM);
    console.log("%c  resign()%c    give up", AMBER, DIM);
  }

  window.chess = function () {
    loadChess(function () {
      game = new window.Chess();
      say("A NICE GAME OF CHESS. WISE CHOICE.");
      render();
      instructions();
    });
  };

  window.board = function () {
    if (!game) return say("Type chess() to start a game.", AMBER);
    render();
  };

  window.moves = function () {
    if (!game) return say("Type chess() to start a game.", AMBER);
    console.log("%c" + game.moves().join("  "), "color:#8be9fd");
  };

  window.resign = function () {
    if (!game) return say("Type chess() to start a game.", AMBER);
    say("A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY.");
    game = null;
  };

  // Light opponent: checkmate if available, else best capture, else random.
  function joshuaReply() {
    var ms = game.moves({ verbose: true });
    if (!ms.length) return;
    var value = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
    var pick = null;
    var bestCapture = 0;
    for (var i = 0; i < ms.length; i++) {
      game.move(ms[i]);
      var mate = game.in_checkmate();
      game.undo();
      if (mate) {
        pick = ms[i];
        break;
      }
      var cap = ms[i].captured ? value[ms[i].captured] : 0;
      if (cap > bestCapture) {
        bestCapture = cap;
        pick = ms[i];
      }
    }
    if (!pick || bestCapture === 0) {
      pick = ms[Math.floor(Math.random() * ms.length)];
    }
    game.move(pick);
    say("JOSHUA: " + pick.san);
  }

  function endCheck() {
    if (game.in_checkmate()) {
      // Whoever is to move has been mated.
      say(
        game.turn() === "w"
          ? "CHECKMATE. JOSHUA WINS. SHALL WE PLAY AGAIN? (chess())"
          : "CHECKMATE. YOU WIN. A STRANGE GAME, PROFESSOR.",
        AMBER
      );
      game = null;
      return true;
    }
    if (game.in_stalemate() || game.in_draw()) {
      say("A STRANGE GAME. NOBODY WINS. (draw)", AMBER);
      game = null;
      return true;
    }
    if (game.in_check()) say("CHECK.", AMBER);
    return false;
  }

  window.move = function (m) {
    if (!game) return say("Type chess() to start a game.", AMBER);
    var mv;
    if (typeof m === "string" && /^[a-h][1-8][a-h][1-8][qrbn]?$/.test(m)) {
      mv = game.move({ from: m.slice(0, 2), to: m.slice(2, 4), promotion: m[4] || "q" });
    } else {
      mv = game.move(m); // SAN, e.g. "e4", "Nf3", "O-O"
    }
    if (!mv) {
      say("ILLEGAL MOVE. (try moves() to see what's legal)", AMBER);
      return;
    }
    render();
    if (endCheck()) return;
    joshuaReply();
    render();
    endCheck();
  };
})();
