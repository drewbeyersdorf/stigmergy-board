#!/usr/bin/env python3
"""stigmergy-board: the work reads the room, not the org chart.

Ants do not hold standups. They leave marks. The next ant reads the mark
and the work routes itself. This board is the mark surface: every card is
visible, a mark says what changed and when, a claim says whose it is now,
and anything stale goes dim on its own. If it is dim, it is not moving.

Demo: python3 stigmergy_board.py demo
"""
import json, time

DIM_AFTER = 30.0  # seconds without a fresh mark -> dim (temple law: dim-when-stale)

class Board:
    def __init__(self, dim_after: float = DIM_AFTER):
        self.cards: dict[str, dict] = {}
        self.dim_after = dim_after

    def pin(self, card_id: str, title: str, owner: str = "") -> dict:
        assert card_id not in self.cards, "card already pinned"
        card = {"id": card_id, "title": title, "owner": owner,
                "marks": [], "pinned_at": time.time()}
        self.cards[card_id] = card
        return card

    def mark(self, card_id: str, author: str, text: str) -> dict:
        """Leave a mark. The mark is the truth; the card is only its history."""
        card = self.cards[card_id]
        if card["owner"] and author != card["owner"]:
            raise PermissionError(f"seat {author} cannot mark {card_id}: owned by {card['owner']}")
        m = {"author": author, "text": text, "at": time.time()}
        card["marks"].append(m)
        return m

    def claim(self, card_id: str, seat: str) -> dict:
        """Claim once. A claimed card moves only by its owner's marks."""
        card = self.cards[card_id]
        if card["owner"]:
            raise PermissionError(f"{card_id} already claimed by {card['owner']}")
        card["owner"] = seat
        return card

    def release(self, card_id: str, seat: str) -> dict:
        card = self.cards[card_id]
        if card["owner"] != seat:
            raise PermissionError("only the owner releases")
        card["owner"] = ""
        return card

    def read(self) -> list[dict]:
        """What every seat sees: the whole board, with dim computed from marks."""
        now = time.time()
        view = []
        for c in self.cards.values():
            last = c["marks"][-1]["at"] if c["marks"] else c["pinned_at"]
            view.append({"id": c["id"], "owner": c["owner"] or "-",
                         "marks": len(c["marks"]),
                         "dim": (now - last) > self.dim_after})
        return view

def demo():
    b = Board(dim_after=0.5)
    b.pin("card-57", "round 57 entry", owner="badger")
    b.pin("card-58", "round 58 entry")
    b.mark("card-57", "badger", "draft live, proofs attached")
    b.claim("card-58", "wren")
    try:
        b.mark("card-58", "heron", "sneak a note")   # not the owner
    except PermissionError as e:
        print("BLOCKED:", e)
    try:
        b.claim("card-58", "magpie")                      # double claim
    except PermissionError as e:
        print("BLOCKED:", e)
    print("t=0 board:", json.dumps(b.read()))
    time.sleep(0.6)                                     # let both go stale
    b.mark("card-57", "badger", "published")             # one stays lit
    print("t=0.6 board:", json.dumps(b.read()))
    b.release("card-58", "wren")
    b.claim("card-58", "heron")
    print("after release+reclaim:", json.dumps(b.read()))

if __name__ == "__main__":
    demo()

