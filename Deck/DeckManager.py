import pygame
import random
from Cards.Card import Suit, Rank, Card
from Cards.Jokers import Jokers
from Levels.SubLevel import SubLevel

class DeckManager:
    def __init__(self):
        self.resetDeck = False
        self.srcCardW, self.srcCardH = 70, 94  # Poker Cards source dimensions
        self.srcJokerW, self.srcJokerH = 133, 187 # Joker sheet dimensions
        self.targetJokerH = 150 # Unified Joker display height
        # === Joker names in order (left-to-right, top-to-bottom) ===
        self.jokerNames = [
            "Fibonacci", "Michael Myers", "? Block", "Hogwarts", "StrawHat",
            "802", "Ogre", "Hog Rider", "Gauntlet", "The Joker"
        ]
    # ---------- Helpers ----------
    def _scaleToHeightIntegerish(self, surf: pygame.Surface, targetH: int) -> pygame.Surface:
        h = surf.get_height()
        if h <= 0 or targetH == h:
            return surf.copy()
        factor = max(1, round(targetH / h))
        scaled = pygame.transform.scale(surf, (surf.get_width() * factor, h * factor))
        if scaled.get_height() != targetH:
            newW = int(scaled.get_width() * (targetH / scaled.get_height()))
            scaled = pygame.transform.scale(scaled, (newW, targetH))
        return scaled

    def _trim_transparent_border(self, surf: pygame.Surface) -> pygame.Surface:
        """
        Remove fully-transparent rows/columns around a surface. Returns a new surface
        cropped to the minimal bounding box that contains non-transparent pixels.
        """
        w, h = surf.get_size()
        pix = surf.copy()
        # Find bounds
        left, right = w, 0
        top, bottom = h, 0
        found = False
        for y in range(h):
            for x in range(w):
                a = pix.get_at((x, y))[3]
                if a != 0:
                    found = True
                    if x < left:
                        left = x
                    if x > right:
                        right = x
                    if y < top:
                        top = y
                    if y > bottom:
                        bottom = y
        if not found:
            return surf.copy()
        rect = pygame.Rect(left, top, right - left + 1, bottom - top + 1)
        return pix.subsurface(rect).copy()

    # ---------- Loading ----------
    def load_card_images(self, subLevel: SubLevel = None):
        """
        Load 52 card faces at their original resolution (70x94),
        optionally applying 'The Mark' modifications if the boss requires it.
        """
        sheet = pygame.image.load('Graphics/Cards/Poker_Sprites.png').convert_alpha()

        cardImages = {}
        useMark = False

        if subLevel is not None:
            bossName = getattr(subLevel, "bossLevel", None)
            if bossName == "The Mark":
                useMark = True
                markFace = sheet.subsurface(pygame.Rect(0, 0, self.srcCardW, self.srcCardH)).copy()

        suits = [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]

        for suitIdx, suit in enumerate(suits):
            for colIdx, rank in enumerate([
                Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX,
                Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
                Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE
            ], start=1):
                x = colIdx * self.srcCardW
                y = suitIdx * self.srcCardH
                cell = sheet.subsurface(pygame.Rect(x, y, self.srcCardW, self.srcCardH)).copy()

                if useMark and rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
                    cell = markFace.copy()

                cardImages[(suit, rank)] = cell

        return cardImages

    def loadJokerImages(self):
        """
        Load Joker sprites from the new 2x5 layout sheet and scale them
        uniformly to the target height. Automatically adjusts slicing
        to prevent out-of-bounds errors.
        """
        sheet = pygame.image.load('Graphics/Cards/Joker_Sprites.png').convert_alpha()
        sheetW, sheetH = sheet.get_width(), sheet.get_height()

        # expected layout is 5 columns x 2 rows — compute cell size from sheet
        cols, rows = 5, 2
        cellW = max(1, sheetW // cols)
        cellH = max(1, sheetH // rows)

        jokers = {}
        for index, name in enumerate(self.jokerNames):
            row = index // cols
            col = index % cols
            x = col * cellW
            y = row * cellH

            # clamp width/height so we don't request out-of-bounds area
            w = min(cellW, max(1, sheetW - x))
            h = min(cellH, max(1, sheetH - y))
            rect = pygame.Rect(x, y, w, h)
            subImg = sheet.subsurface(rect).copy()

            # Trim empty transparent border that often exists in sprite cells
            subImg = self._trim_transparent_border(subImg)

            # Ensure a small uniform padding so the sprite isn't cut too tight
            pad = 4
            if subImg.get_width() > pad * 2 and subImg.get_height() > pad * 2:
                padded = pygame.Surface(((subImg.get_width() + pad * 2) - 3, subImg.get_height() + pad * 2), pygame.SRCALPHA)
                padded.fill((0, 0, 0, 0))
                padded.blit(subImg, (pad, pad))
                subImg = padded

            # Scale to target height while preserving crispness
            subImg = self._scaleToHeightIntegerish(subImg, self.targetJokerH)

            jokers[name] = subImg

        return jokers

    # ---------- Deck creation ----------
    # TODO (TASK 1): Implement a function that creates a full deck of Cards.
    #   Loop through all possible suits and ranks, retrieve the corresponding image
    #   from the card_images dictionary using (suit, rank) as the key, and create a Card
    #   object for each valid combination. If a matching image is not found, skip that card.
    #   Add each created Card to a list called 'deck' and return the completed list at the end.
    def createDeck(self, subLevel: SubLevel = None):
        cardImages = self.load_card_images(subLevel)
        deck = []

        suits = [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]
        ranks = [
            Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX,
            Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
            Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE
        ]

        for suit in suits:
            for rank in ranks:
                image = cardImages.get((suit, rank), None)
                if image is None:
                    continue
                deck.append(Card(suit=suit, rank=rank, image=image))

        return deck

    # TODO (TASK 5.1): Complete the priceMap variable by assigning each joker a price.
    #   The key should represent the joker's name, and the value should be the joker's price.
    def createJokerDeck(self): # Creates a deck of jokers based on the loaded sprites
        jokerImages = self.loadJokerImages()
        deckJokers = []

        priceMap = {
            "Fibonacci": 7,
            "Michael Myers": 8,
            "? Block": 4,
            "Hogwarts": 7,
            "StrawHat": 5,
            "802": 6,
            "Ogre": 6,
            "Hog Rider": 4,
            "Gauntlet": 9,
            "The Joker": 3
        }

        for name, image in jokerImages.items():
            price = priceMap.get(name, 5)
            sellPrice = max(2, price // 2)

            joker = Jokers(name=name, description="Joker Card", image=image)
            joker.price = price
            joker._sell_price = sellPrice
            deckJokers.append(joker)

        return deckJokers


    # ---------- Utilities ----------
    def shuffleDeck(self, deck): # Shuffles any given deck of card or joker objects
        random.shuffle(deck)
        return deck

    def dealCards(self, deck, numCards, subLevel: SubLevel = None): # Deals a number of cards from the deck
        dealtCards = []
        bossName = getattr(subLevel, "bossLevel", None) if subLevel is not None else None

        houseImage = None
        if bossName == "The House":
            sheet = pygame.image.load('Graphics/Cards/Poker_Sprites.png').convert_alpha()
            houseImage = sheet.subsurface(pygame.Rect(0, 0, self.srcCardW, self.srcCardH)).copy()

        take = min(numCards, len(deck))
        for _ in range(take):
            card = deck.pop(0)
            if bossName == "The House":
                card.image = houseImage
                card.faceDown = True
            dealtCards.append(card)

        return dealtCards
