# https://stackoverflow.com/questions/22753160/how-do-i-accept-input-from-arrow-keys-or-accept-directional-input
import sys, tty, termios
import re

ESCAPE = "\x1B"
# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ESCAPE_SEQ = re.compile(r"^\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])$")

CLEAR_LINE = "\x1B[K"
DELETE = "\x1B[3~"

UP = "\x1B[A"
DOWN = "\x1B[B"
RIGHT = "\x1B[C"
LEFT = "\x1B[D"
_arrowKeys = [UP, DOWN, RIGHT, LEFT]

BACKSPACE = "\x7f"
INTERRUPT = "\x03"
EOF = "\x04"


def _getChar(nchars: int = 1):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(nchars)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def _getKey():
    k = _getChar()
    if k == ESCAPE:
        while not ESCAPE_SEQ.match(k):
            k += _getChar()
    return k


def _printHex(s: str) -> None:
    print(" ".join(hex(ord(c)) for c in s))


def _moveCursorRight(distRight: int) -> None:
    if distRight > 0:
        print(f"\x1B[{distRight}C", end="", flush=True)
    elif distRight < 0:
        print(f"\x1B[{-distRight}D", end="", flush=True)


def _resetLine(line: str) -> None:
    print("\r" + line + CLEAR_LINE, end="")


def _bound(val, lowerBound=None, upperBound=None):
    if not lowerBound is None:
        val = max(val, lowerBound)
    if not upperBound is None:
        val = min(val, upperBound)
    return val


class _SingleLineReader:
    def __init__(self, pastLines: list, prompt: str = "", debug: bool = False) -> None:
        self.lines = pastLines
        self.line = ""
        self.lines.append(self.line)
        self.lineIdx = len(self.lines) - 1
        self.charIdx = 0
        self.used = False
        self.debug = debug
        self.prompt = prompt

    def _use(self):
        if self.used:
            raise Exception("using line reader multiple times")
        self.used = True

    def read(self) -> str:
        self._use()

        print(self.prompt, end="", flush=True)

        while (k := _getKey()) != "\r":
            if self.debug:
                print("\r" + CLEAR_LINE, end="")
                _printHex(k)

            if k in _arrowKeys:
                if k == UP:
                    self.moveLineDown(-1)
                elif k == DOWN:
                    self.moveLineDown(1)
                elif k == LEFT:
                    self.moveCharRight(-1)
                elif k == RIGHT:
                    self.moveCharRight(1)
            else:
                if k == BACKSPACE:
                    self.doBackspace()
                elif k == DELETE:
                    self.doDelete()
                elif k == INTERRUPT:
                    raise KeyboardInterrupt()
                elif k == EOF:
                    raise EOFError()
                elif k[0] == ESCAPE:
                    raise Exception(f"unknown ANSI escape: {' '.join(hex(ord(c)) for c in k)}")
                else:
                    self.insertChar(k)
                self.lines[-1] = self.line
        self.lines[-1] = self.line
        print()
        return self.line

    def moveLineDown(self, distDown: int):
        self.lineIdx = _bound(self.lineIdx + distDown, 0, len(self.lines) - 1)
        self.line = self.lines[self.lineIdx]
        self.charIdx = len(self.line)
        self._resetLineAndCursor()

    def moveCharRight(self, distRight: int):
        lastIdx = self.charIdx
        self.charIdx = _bound(self.charIdx + distRight, 0, len(self.line))
        _moveCursorRight(self.charIdx - lastIdx)

    def doBackspace(self):
        if self.charIdx > 0:
            self.line = self.line[: self.charIdx - 1] + self.line[self.charIdx :]
            self.charIdx -= 1
            self._resetLineAndCursor()

    def doDelete(self):
        if self.charIdx < len(self.line):
            self.line = self.line[: self.charIdx] + self.line[self.charIdx + 1 :]
            self._resetLineAndCursor()

    def insertChar(self, k: str):
        self.line = self.line[: self.charIdx] + k + self.line[self.charIdx :]
        self.charIdx += 1
        self._resetLineAndCursor()

    def _resetLineAndCursor(self):
        _resetLine(self.prompt + self.line)
        _moveCursorRight(self.charIdx - len(self.line))


class Input:
    def __init__(self, debug: bool = False) -> None:
        self.lines = []
        self.debug = debug

    def getLine(self, prompt: str = "") -> str:
        return _SingleLineReader(self.lines, prompt, self.debug).read()


def main():
    debug = len(sys.argv) > 1 and sys.argv[1] == "debug"
    input = Input(debug)
    for _ in range(3):
        input.getLine("> ")


if __name__ == "__main__":
    main()
