import pygame
import random
from States.Menus.DebugState import DebugState
from States.Core.StateClass import State
from Cards.Card import Suit, Rank
from States.Core.PlayerInfo import PlayerInfo
from Deck.HandEvaluator import evaluate_hand


HAND_SCORES = {
    "Straight Flush": {"chips": 100, "multiplier": 8, "level": 1},
    "Four of a Kind": {"chips": 60, "multiplier": 7, "level": 1},
    "Full House": {"chips": 40, "multiplier": 4, "level": 1},
    "Flush": {"chips": 35, "multiplier": 4, "level": 1},
    "Straight": {"chips": 30, "multiplier": 4, "level": 1},
    "Three of a Kind": {"chips": 30, "multiplier": 3, "level": 1},
    "Two Pair": {"chips": 20, "multiplier": 2, "level": 1},
    "One Pair": {"chips": 10, "multiplier": 2, "level": 1},
    "High Card": {"chips": 5, "multiplier": 1, "level": 1},
}

class GameState(State):
    def __init__(self, nextState: str = "", player: PlayerInfo = None):
        super().__init__(nextState)
        # ----------------------------Deck and Hand initialization----------------------------
        self.playerInfo = player # playerInfo object
        self.deck = State.deckManager.shuffleDeck(State.deckManager.createDeck(self.playerInfo.levelManager.curSubLevel))
        self.hand = State.deckManager.dealCards(self.deck, 8)
        self.cards = {}
        
        self.jokerDeck = State.deckManager.createJokerDeck()
        self.playerJokers = []
        self.jokers = {}
        # track which jokers activated for the current played hand (used to offset their draw)
        self.activated_jokers = set()
        
        # for joker in self.jokerDeck:
        #     print(joker.name)
        
        self.cardsSelectedList = []
        self.cardsSelectedRect = {}
        self.playedHandNameList = ['']
        self.used = []

        self.redTint = pygame.image.load("Graphics/Backgrounds/redTint.png").convert_alpha()
        self.redTint = pygame.transform.scale(self.redTint, (1300, 750))
        self.showRedTint = False
        self.redAlpha = 0

        self.gameOverSound = pygame.mixer.Sound("Graphics/Sounds/gameEnd.mp3")
        self.gameOverSound.set_volume(0.6)  # adjust loudness if needed

        # --------------------------------Images----------------------------------------------
        self.backgroundImage = pygame.image.load('Graphics/Backgrounds/gameplayBG.jpg')
        self.background = pygame.transform.scale(self.backgroundImage, (1300, 750))
        self.smallBlind = pygame.image.load('Graphics/Backgrounds/Blinds/smallBlind.png')

        self.tvOverlay = pygame.image.load('Graphics/Backgrounds/CRT.png').convert_alpha()
        self.tvOverlay = pygame.transform.scale(self.tvOverlay, (1300, 750))
        # ----------------------------Player Options UI---------------------------------------

        # ----------------------------Boss Theme & Background----------------------------
        # Use the music channel for background themes (main/boss) to avoid overlaps
        self.bossMusic_path = "Graphics/Sounds/bossBlindTheme.mp3"
        self.bossBackgroundImage = pygame.image.load('Graphics/Backgrounds/bossBG.png')
        self.bossBackground = pygame.transform.scale(self.bossBackgroundImage, (1300, 750))
        self.isBossActive = False
        self.bossMusicPlaying = False

        self.playerOpcions = pygame.Surface((500, 650), pygame.SRCALPHA)
        self.playerOpcionsRect = pygame.Rect(460, 650, 400, 100)

        total_w = self.playerOpcions.get_width()
        third_w = total_w // 3
        btn_h = 84

        self.playHandButtonRect = pygame.Rect(0, 0, third_w, btn_h)
        self.sortHandRect = pygame.Rect(third_w, 0, third_w, btn_h)
        self.discardButtonRect = pygame.Rect(third_w * 2, 0, third_w, btn_h)

        inner_margin = 8
        inner_w = (self.sortHandRect.width - inner_margin * 3) // 2
        inner_h = 48
        self.sort_inner_shift = 9
        inner_y = (self.sortHandRect.height - inner_h) // 2 + self.sort_inner_shift
        self.sortRankRect = pygame.Rect(self.sortHandRect.x + inner_margin, inner_y, inner_w, inner_h)
        self.sortSuitRect = pygame.Rect(self.sortHandRect.x + inner_margin * 2 + inner_w, inner_y, inner_w, inner_h)

        # -------------------------------Text surfaces--------------------------------------
        self.playHandText = self.playerInfo.textFont2.render("Play Hand", False, 'white')
        self.discardText = self.playerInfo.textFont2.render("Discard", False, 'white')
        self.sortRankText = self.playerInfo.textFont2.render("Rank", False, 'white')
        self.sortSuitText = self.playerInfo.textFont2.render("Suit", False, 'white')
        self.sortTitleText = self.playerInfo.textFont2.render("Sort Hand", False, 'white')

        # ----------------------------Game Areas----------------------------------------------
        self.centerCardsRect = pygame.Rect(450, 300, 500, 140)
        self.centerCardsSurface = pygame.Surface(self.centerCardsRect.size, pygame.SRCALPHA)
        self.deckContainer = pygame.Rect(380, 510, 680, 120)
        self.jokerContainer = pygame.Rect(380, 40, 340, 130)
        self.pileContainer = pygame.Rect(1120, 550, 100, 140)

        # ----------------------------Sound Effects-------------------------------------------
        self.select_sfx = pygame.mixer.Sound('Graphics/Sounds/selectCard.ogg')
        self.deselect_sfx = pygame.mixer.Sound('Graphics/Sounds/deselectCard.ogg')

        # ----------------------------Deck Pile UI--------------------------------------------
        self.show_deck_pile = False
        self.deck_button_rect = self.pileContainer.copy()

        # ----------------------------Play Hand Logic-----------------------------------------
        self.playHandActive = False
        self.playHandStartTime = 0
        self.playHandDuration = 5000   # show chips/mult for 5 seconds
        self.playedHandName = ""
        self.playedHandTextSurface = None
        self.scoreBreakdownTextSurface = None
        self.pending_round_add = 0      # amount to add to roundScore when timer expires

        self.updateCards(400, 520, self.cards, self.hand, scale=1.2)

        # ------ Debug Overlay Setup -------
        self.debugState = DebugState(game_state=self)
        # ------------------------------------------------------------------------------------

    def _pretty_joker_description(self, joker_obj):
        desc_map = {
            "The Joker": "Increase the hand multiplier by +4.",
            "Michael Myers": "Add a random multiplier between 0 and 23.",
            "Fibonacci": "For each Ace/2/3/5/8 played, add +8 to the multiplier.",
            "Gauntlet": "Grant +250 chips but reduce remaining hands by 2.",

            "Ogre": "Add +3 to the multiplier for each joker you own.",
            "StrawHat": "Grant +100 chips, then -5 per hand already played this round.",
            "Hog Rider": "If the played hand is a Straight, add +100 chips.",
            "? Block": "If the played hand used exactly 4 Cards, add +4 chips.",
            "Hogwarts": "Each Ace played grants +4 multiplier and +20 chips.",
            "802": "If this is the last hand of the round, double the final gain.",
        }
        return desc_map.get(joker_obj.name, "No description available.")

    def gray_overlay_(self, destSurface, rect):
        shade = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        destSurface.blit(shade, rect.topleft)

    def update(self):
        # Always update LevelManager first so win/levelFinished flags are fresh
        self.playerInfo.levelManager.update()

        # If LevelManager flagged playerWins (no more levels), transition to GameWinState
        if self.playerInfo.levelManager.playerWins:
            self.isFinished = True
            self.nextState = "GameWinState"
            self.switchToNormalTheme()
            # dont continue updating GameState
            return

        # Check if we need to reset deck (coming back from LevelSelectState)
        if self.deckManager.resetDeck:
            self.deck = State.deckManager.shuffleDeck(State.deckManager.createDeck(self.playerInfo.levelManager.next_unfinished_sublevel()))
            self.hand = State.deckManager.dealCards(self.deck, 8, self.playerInfo.levelManager.next_unfinished_sublevel())
            self.used = []
            self.cardsSelectedList = []
            self.cardsSelectedRect = {}
            self.updateCards(400, 520, self.cards, self.hand, scale=1.2)
            self.deckManager.resetDeck = False  # Clear the flag

        # Check if level is finished and transition to LevelSelectState
        if self.playerInfo.levelFinished:
            reward = self.calculate_gold_reward(self.playerInfo)
            self.playerInfo.playerMoney += reward
            self.playerInfo.amountOfHands = 4
            self.playerInfo.amountOfDiscards = 4
            self.playerInfo.update()
            self.drawDeckPile()
            self.drawJokers()
            self.drawDeckContainer()
            self.screen.blit(self.tvOverlay,(0,0))

            State.screenshot = self.screen.copy()
            State.player_info = self.playerInfo
            self.isFinished = True
            self.deck = State.deckManager.shuffleDeck(State.deckManager.createDeck(self.playerInfo.levelManager.next_unfinished_sublevel()))
            self.hand = State.deckManager.dealCards(self.deck, 8, self.playerInfo.levelManager.next_unfinished_sublevel())
            self.playerInfo.amountOfHands = 4
            self.nextState = "ShopState"

            return
        
        # Handle boss level music switching
        bossName = self.playerInfo.levelManager.curSubLevel.bossLevel
        if bossName and not self.isBossActive:
            self.isBossActive = True
            self.switchToBossTheme()
        elif not bossName and self.isBossActive:
            self.isBossActive = False
            self.switchToNormalTheme()
            
        # Handle play hand timing
        if self.playHandActive and self.playHandStartTime > 0:
            curTime = pygame.time.get_ticks()
            if curTime - self.playHandStartTime > self.playHandDuration:
                # Commit pending round addition and reset displayed chips/multiplier
                if getattr(self, "pending_round_add", 0) > 0:
                    self.playerInfo.roundScore += self.pending_round_add
                    self.pending_round_add = 0
                self.playerInfo.playerChips = 0
                self.playerInfo.playerMultiplier = 0

                self.playerInfo.curHandOfPlayer = ""
                self.playerInfo.curHandText = self.playerInfo.textFont1.render("", False, 'white')

                self.playHandActive = False
                # clear activated jokers when the display period ends so they return to normal position
                self.activated_jokers.clear()
                self.playHandStartTime = 0
                # Special boss effect: The Hook discards 2 random Cards from the hand
                if bossName == "The Hook":
                    # choose Cards that are currently in hand and not the selected Cards
                    posiblesCardToDiscard = []
                    for card in self.hand:
                        if card not in self.cardsSelectedList:
                            posiblesCardToDiscard.append(card)

                    discardCount = min(2, len(posiblesCardToDiscard)) # what happends if less than 2 Cards available?
                    if discardCount > 0:
                        cardsToDiscard = random.sample(posiblesCardToDiscard, discardCount)
                        for c in cardsToDiscard:
                                self.used.append(c)
                                self.hand.remove(c)
                                self.deselect_sfx.play()


                self.discardCards(removeFromHand=True)
        self.draw()
        self.checkHoverCards()
        self.debugState.update()

    def draw(self):
        # --- Call funcions ---
        self.playerInfo.update()
        self.drawDeckContainer()
        self.drawCardsInHand()
        self.drawCenterCards()
        self.drawJokers()
        self.drawDeckPile()
        self.drawPlayerOptions()
        self.drawPlayedHandName()
        self.drawDeckPileOverlay()
        self.screen.blit(self.tvOverlay, (0, 0))

    def switchToBossTheme(self):
        # Switch background music to the boss theme using the music channel
        if not self.bossMusicPlaying:
            pygame.mixer.music.load(self.bossMusic_path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.4)
            self.bossMusicPlaying = True

    def switchToNormalTheme(self):
        # Restore the normal main theme on the music channel
        if self.bossMusicPlaying:
            pygame.mixer.music.load("Graphics/Sounds/mainTheme.mp3")
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.3)
            self.bossMusicPlaying = False

    # ----------------------------Draw Methods------------------------------------------------
    def drawDeckContainer(self):
        deckContainer = pygame.Surface(self.deckContainer.size, pygame.SRCALPHA)
        pygame.draw.rect(deckContainer, (0, 0, 0, 120), deckContainer.get_rect())
        self.screen.blit(deckContainer, self.deckContainer.topleft)

    def drawCardsInHand(self):
        for card in self.cards:
            if self.playHandActive and card in self.cardsSelectedList:
                continue
            img_to_draw = getattr(card, "scaled_image", card.image)
            State.screen.blit(img_to_draw, self.cards[card])
        self.drawCardTooltip()

    def drawCenterCards(self):
        self.centerCardsSurface.fill((0, 0, 0, 0))  # Clear surface

        if len(self.cardsSelectedRect) > 0:
            for card, rect in self.cardsSelectedRect.items():
                img_to_draw = getattr(card, "scaled_image", card.image)
                self.centerCardsSurface.blit(img_to_draw, rect)

        self.screen.blit(self.centerCardsSurface, self.centerCardsRect)

    def drawPlayedHandName(self):
        if self.playHandActive and self.playedHandTextSurface:
            text_rect = self.playedHandTextSurface.get_rect(centerx=self.centerCardsRect.centerx)
            text_rect.bottom = self.centerCardsRect.top - 40  # Positioned higher
            self.screen.blit(self.playedHandTextSurface, text_rect)

        if self.playHandActive and self.scoreBreakdownTextSurface:
            score_rect = self.scoreBreakdownTextSurface.get_rect(centerx=self.centerCardsRect.centerx)
            # Position it relative to the hand name's rect for perfect alignment
            score_rect.top = text_rect.bottom + 5
            self.screen.blit(self.scoreBreakdownTextSurface, score_rect)

    def drawJokers(self):
        # Draw container background
        jokerSurface = pygame.Surface(self.jokerContainer.size, pygame.SRCALPHA)
        pygame.draw.rect(jokerSurface, (0, 0, 0, 120), jokerSurface.get_rect(), border_radius=6)
        self.screen.blit(jokerSurface, self.jokerContainer.topleft)

        # Build joker objects list in the exact order of self.playerJokers
        player_joker_objs = []
        for name in self.playerJokers:
            for joker in self.jokerDeck:
                if joker.name == name:
                    player_joker_objs.append(joker)
                    break
        self.jokers.clear()
        n = max(1, len(player_joker_objs))
        inner_margin = 8
        avail_w = self.jokerContainer.width - inner_margin * (n + 1)
        slot_w = max(10, avail_w // n) if n > 0 else self.jokerContainer.width - inner_margin * 2
        slot_h = self.jokerContainer.height - inner_margin * 2

        for i, joker in enumerate(player_joker_objs):
            img = getattr(joker, "image", None)
            if img is None:
                continue

            # Determine scale to fit slot height
            target_h = slot_h
            iw, ih = img.get_width(), img.get_height()
            scale = 1.0
            if ih > 0 and ih != target_h:
                scale = target_h / ih
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))
            scaled = pygame.transform.scale(img, (new_w, new_h))
            joker.scaled_image = scaled

            # center the scaled image inside its slot
            slot_x = self.jokerContainer.x + inner_margin + i * (slot_w + inner_margin)
            slot_y = self.jokerContainer.y + inner_margin
            # horizontally center within slot area
            draw_x = slot_x + max(0, (slot_w - new_w) // 2)
            draw_y = slot_y + max(0, (slot_h - new_h) // 2)

            rect = pygame.Rect(draw_x, draw_y, new_w, new_h)
            if self.playHandActive and joker.name in self.activated_jokers:
                rect = rect.move(0, 50)

            self.jokers[joker] = rect
            State.screen.blit(scaled, rect)

        # count/title text (keeps old placement just under container)
        jokerTitleText = self.playerInfo.textFont1.render((str(len(self.playerJokers))) + "/ 2", True, 'white')
        self.screen.blit(jokerTitleText, (self.jokerContainer.x + 1, self.jokerContainer.y + self.jokerContainer.height + 0))

    def drawDeckPile(self):
        pileContainer = pygame.Surface(self.pileContainer.size, pygame.SRCALPHA)
        pygame.draw.rect(pileContainer, (0, 0, 0, 120), pileContainer.get_rect())
        balatro_card = pygame.image.load('Graphics/Cards/Poker_Sprites.png').convert_alpha()
        card_width, card_height = 70, 94
        card_img = balatro_card.subsurface(pygame.Rect(0, 0, card_width, card_height))
        scaled_card = pygame.transform.scale(card_img, self.pileContainer.size)
        pileContainer.blit(scaled_card, (0, 0))
        self.screen.blit(pileContainer, self.pileContainer.topleft)
        pileCountText = self.playerInfo.textFont1.render(str(len(self.deck)) + "/44", True, 'white')
        textX = self.pileContainer.x + 5
        textY = self.pileContainer.y + self.pileContainer.height + 5
        self.screen.blit(pileCountText, (textX, textY))
        pygame.draw.rect(self.screen, (50, 50, 200), self.deck_button_rect, 3)

    def drawPlayerOptions(self):
        mousePos = pygame.mouse.get_pos()
        mousePosPlayerOpcions = (mousePos[0] - self.playerOpcionsRect.x, mousePos[1] - self.playerOpcionsRect.y)
        self.playerOpcions.fill((0, 0, 0, 0))
        pygame.draw.rect(self.playerOpcions, (255, 255, 255), self.sortHandRect, 2, border_radius=12)

        if self.sortRankRect.collidepoint(mousePosPlayerOpcions):
            pygame.draw.rect(self.playerOpcions, (200, 170, 0), self.sortRankRect, border_radius=8)
        else:
            pygame.draw.rect(self.playerOpcions, 'orange', self.sortRankRect, border_radius=8)

        if self.sortSuitRect.collidepoint(mousePosPlayerOpcions):
            pygame.draw.rect(self.playerOpcions, (200, 170, 0), self.sortSuitRect, border_radius=8)
        else:
            pygame.draw.rect(self.playerOpcions, 'orange', self.sortSuitRect, border_radius=8)

        self.playerOpcions.blit(self.sortRankText, self.sortRankText.get_rect(center=self.sortRankRect.center))
        self.playerOpcions.blit(self.sortSuitText, self.sortSuitText.get_rect(center=self.sortSuitRect.center))
        sort_title_rect = self.sortTitleText.get_rect(centerx=self.sortHandRect.centerx)
        sort_title_rect.centery = self.sortRankRect.y - (sort_title_rect.height // 2) - 6
        self.playerOpcions.blit(self.sortTitleText, sort_title_rect)

        if len(self.cardsSelectedList) > 0:
            if self.playHandButtonRect.collidepoint(mousePosPlayerOpcions):
                pygame.draw.rect(self.playerOpcions, (0, 0, 139), self.playHandButtonRect, border_radius=12)
            else:
                pygame.draw.rect(self.playerOpcions, 'blue', self.playHandButtonRect, border_radius=12)

            if self.discardButtonRect.collidepoint(mousePosPlayerOpcions):
                pygame.draw.rect(self.playerOpcions, (128, 0, 0), self.discardButtonRect, border_radius=12)
            else:
                pygame.draw.rect(self.playerOpcions, 'red', self.discardButtonRect, border_radius=12)

            self.playerOpcions.blit(self.playHandText,
                                    self.playHandText.get_rect(center=self.playHandButtonRect.center))
            self.playerOpcions.blit(self.discardText, self.discardText.get_rect(center=self.discardButtonRect.center))

        State.screen.blit(self.playerOpcions, self.playerOpcionsRect.topleft)

    def drawDeckPileOverlay(self):
        if self.show_deck_pile:
            overlay = pygame.Surface((1300, 750), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            card_images = State.deckManager.load_card_images(self.playerInfo.levelManager.next_unfinished_sublevel())
            suits = [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]
            ranks = [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN,
                     Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING]
            start_x, start_y = 100, 100
            spacing_x, spacing_y = 75, 100

            unusable = set()
            for c in self.cardsSelectedList:
                unusable.add((c.suit, c.rank))
            for c in self.hand:
                unusable.add((c.suit, c.rank))
            for c in self.used:
                unusable.add((c.suit, c.rank))

            for row, suit in enumerate(suits):
                for col, rank in enumerate(ranks):
                    img = card_images.get((suit, rank))
                    if img:
                        x = start_x + col * spacing_x
                        y = start_y + row * spacing_y
                        self.screen.blit(img, (x,y))

                    if (suit, rank)  in unusable: #or (suit, rank) in deck_selected:
                        rect = pygame.Rect(start_x + col * spacing_x, start_y + row * spacing_y, img.get_width(), img.get_height())
                        self.gray_overlay_(self.screen, rect)

            close_text = self.playerInfo.textFont2.render("Click anywhere to close", True, 'white')
            self.screen.blit(close_text, (start_x, start_y + len(suits) * spacing_y + 20))

    # ----------------------------Input Methods-----------------------------------------------
    def userInput(self, events):
        mousePos = pygame.mouse.get_pos()
        mousePosPlayerOpcions = (mousePos[0] - self.playerOpcionsRect.x, mousePos[1] - self.playerOpcionsRect.y)

        if events.type == pygame.QUIT:
            self.isFinished = True
            self.nextState = "StartState"

        # Escape key to quit
        if events.type == pygame.KEYDOWN:
            if events.key == pygame.K_ESCAPE:
                self.isFinished = True
                self.nextState = "StartState"

        # ---------------- Mouse clicks below ----------------
        if events.type == pygame.MOUSEBUTTONDOWN:
            if self.show_deck_pile:
                self.show_deck_pile = False
                return

            if self.deck_button_rect.collidepoint(mousePos):
                self.show_deck_pile = True

            if self.discardButtonRect.collidepoint(mousePosPlayerOpcions):
                if not self.playHandActive and len(self.cardsSelectedList) > 0 and self.playerInfo.amountOfDiscards > 0:
                    self.discardCards(True)
                    self.playerInfo.amountOfDiscards -= 1

            if self.playHandButtonRect.collidepoint(mousePosPlayerOpcions):
                if not self.playHandActive and len(self.cardsSelectedList) > 0:
                    self.playHand()

            if self.sortRankRect.collidepoint(mousePosPlayerOpcions):
                self.SortCards(sort_by="rank")

            if self.sortSuitRect.collidepoint(mousePosPlayerOpcions):
                self.SortCards(sort_by="suit")

            if self.playerInfo.runInfoRect.collidepoint(
                    (mousePos[0] - self.playerInfo.playerInfo2.x, mousePos[1] - self.playerInfo.playerInfo2.y)):
                State.screenshot = self.screen.copy()
                self.isFinished = True
                self.nextState = "RunInfoState"

            # Joker click info
            for joker_obj, joker_rect in self.jokers.items():
                if joker_rect.collidepoint(mousePos):
                    desc_text = self._pretty_joker_description(joker_obj)
                    price = getattr(joker_obj, 'price', None)
                    extra = f" — Price: {price}$" if price is not None else ""
                    print("------------------------------------------------------------")
                    print(f"[JOKER] {joker_obj.name} — {desc_text}{extra}")
                    return

        # Pass input to playerInfo and debugState
        self.playerInfo.userInput(events)
        self.debugState.userInput(events)
        self.userInputCards(events)

    def userInputCards(self, events):
        if events.type == pygame.MOUSEBUTTONDOWN and not self.playHandActive:
            mousePos = pygame.mouse.get_pos()
            # Iterate in reverse to select the top-most card first
            for card in reversed(list(self.cards.keys())):
                if self.cards[card].collidepoint(mousePos):
                    if not card.isSelected:
                        if len(self.cardsSelectedList) < 5:
                            card.isSelected = True
                            self.cards[card].y -= 50
                            self.cardsSelectedList.append(card)
                            self.select_sfx.play()
                    else:
                        card.isSelected = False
                        self.cards[card].y += 50
                        self.cardsSelectedList.remove(card)
                        self.deselect_sfx.play()
                    return  # Stop after interacting with one card

    # TODO (TASK 7) - Rewrite this function so that it calculates the player's gold reward *recursively*.
    #   The recursion should progress through each step of the reward process (base reward, bonus for overkill, etc.)
    #   by calling itself with updated parameters or stages instead of using loops.
    #   Each recursive call should handle a single part of the reward logic, and the final base case should
    #   return the total combined reward once all calculations are complete.
    #   The function must include:
    #     - Base gold depending on blind type (SMALL=4, BIG=8, BOSS=10)
    #     - Recursive calculation of the overkill bonus (based on how much score exceeds the target)
    #     - A clear base case to stop recursion when all parts are done
    #   Avoid any for/while loops — recursion alone must handle the repetition.
    def calculate_gold_reward(self, playerInfo, stage=0):
            return 0

    def updateCards(self, posX, posY, cardsDict, cardsList, scale=1.5, spacing=90, baseYOffset=-20, leftShift=40):
        cardsDict.clear()
        for i, card in enumerate(cardsList):
            w, h = card.image.get_width(), card.image.get_height()
            new_w, new_h = int(w * scale), int(h * scale)
            card.scaled_image = pygame.transform.scale(card.image, (new_w, new_h))
            x = posX + i * spacing - leftShift
            y = posY + baseYOffset
            if getattr(card, "isSelected", False):
                y -= 50
            cardsDict[card] = pygame.Rect(x, y, new_w, new_h)

    # TODO (TASK 2) - Implement a basic card-sorting system without using built-in sort functions.
    #   Create a 'suitOrder' list (Hearts, Clubs, Diamonds, Spades), then use nested loops to compare each card
    #   with the ones after it. Depending on the mode, sort by rank first or suit first, swapping cards when needed
    #   until the entire hand is ordered correctly.
    def SortCards(self, sort_by: str = "suit"):
        suitOrder = [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]

        suitValue = {
            Suit.HEARTS: 0,
            Suit.CLUBS: 1,
            Suit.DIAMONDS: 2,
            Suit.SPADES: 3
        }

        n = len(self.hand)

        for i in range(n):
            for j in range(i + 1, n):
                a = self.hand[i]
                b = self.hand[j]

                a_s = suitValue.get(a.suit, 999)
                b_s = suitValue.get(b.suit, 999)
                a_r = a.rank.value
                b_r = b.rank.value

                should_swap = False

                if sort_by == "rank":
                    # Rank-first (higher ranks first), then suit order
                    if b_r > a_r:
                        should_swap = True
                    elif b_r == a_r and b_s < a_s:
                        should_swap = True
                else:
                    if b_s < a_s:
                        should_swap = True
                    elif b_s == a_s and b_r > a_r:
                        should_swap = True

                if should_swap:
                    self.hand[i], self.hand[j] = self.hand[j], self.hand[i]

        self.updateCards(400, 520, self.cards, self.hand, scale=1.2)


    def checkHoverCards(self):
        mousePos = pygame.mouse.get_pos()
        for card, rect in self.cards.items():
            if rect.collidepoint(mousePos):
                break
    
    def drawCardTooltip(self):
        mousePos = pygame.mouse.get_pos()
        for card, rect in self.cards.items():
            if rect.collidepoint(mousePos):
                tooltip_text = f"{card.rank.name.title()} of {card.suit.name.title()} ({card.chips} Chips)"
                font = self.playerInfo.textFont1
                if self.playerInfo.levelManager.curSubLevel.bossLevel == "The Mark":
                    if card.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
                        text_surf = font.render("???", False, 'White')
                    else:
                        text_surf = font.render(tooltip_text, False, 'white')
                elif self.playerInfo.levelManager.curSubLevel.bossLevel == "The House":
                    if card.faceDown:
                        text_surf = font.render("???", False, 'White')
                    else:
                        text_surf = font.render(tooltip_text, False, 'white')
                else:
                    text_surf = font.render(tooltip_text, False, 'white')
                padding = 6
                tooltip_w, tooltip_h = text_surf.get_width() + padding * 2, text_surf.get_height() + padding * 2
                tooltip_surf = pygame.Surface((tooltip_w, tooltip_h), pygame.SRCALPHA)
                pygame.draw.rect(tooltip_surf, (0, 0, 0, 180), tooltip_surf.get_rect(), border_radius=6)
                tooltip_surf.blit(text_surf, (padding, padding))
                tooltip_x = rect.x + (rect.width - tooltip_w) // 2
                tooltip_y = rect.y - tooltip_h - 10
                self.screen.blit(tooltip_surf, (tooltip_x, tooltip_y))
                break
    
    # -------- Play Hand Logic -----------
    def playHand(self):
        if self.playerInfo.amountOfHands == 0: # Check if last hand and failed the round
            target_score = self.playerInfo.levelManager.curSubLevel.score
            if self.playerInfo.roundScore < target_score:
                pygame.mixer.music.stop()
                self.gameOverSound.play()
                self.showRedTint = True

                for alpha in range(0, 180, 10):
                    self.redAlpha = alpha
                    self.draw()
                    tint = pygame.Surface((1300, 750), pygame.SRCALPHA)
                    tint.fill((255, 0, 0, alpha))
                    self.screen.blit(tint, (0, 0))
                    pygame.display.update()
                    pygame.time.wait(80)

                pygame.time.wait(1200)
                pygame.quit()

        self.playerInfo.amountOfHands -= 1
        hand_name = evaluate_hand(self.cardsSelectedList)
        self.playedHandName = hand_name
        self.playedHandNameList.append(hand_name)

        # Base values from HAND_SCORES
        score_info = HAND_SCORES.get(hand_name, {"chips": 0, "multiplier": 1})
        hand_chips = score_info.get("chips", 0)
        hand_mult = score_info.get("multiplier", 1)

        # Prepare helpers
        sel = list(self.cardsSelectedList)
        # group by rank value and by suit
        by_rank = {}
        for c in sel:
            by_rank.setdefault(c.rank.value, []).append(c)
        by_suit = {}
        for c in sel:
            by_suit.setdefault(c.suit, []).append(c)

        used_cards = []

        # Helper: find straight sequence in a list of ranks -> returns list of rank values
        def find_straight_ranks(ranks_set):
            vals = sorted(set(ranks_set))
            # include low-Ace (1) if Ace present
            if 14 in vals:
                vals_with_ace_low = sorted(set(vals + [1]))
            else:
                vals_with_ace_low = vals
            seq_start = None
            consec = 1
            best_seq = []
            arr = vals_with_ace_low
            for i in range(len(arr)):
                if i == 0:
                    consec = 1
                    seq_start = arr[0]
                    cur_seq = [arr[0]]
                else:
                    if arr[i] == arr[i-1]:
                        continue
                    if arr[i] == arr[i-1] + 1:
                        consec += 1
                        cur_seq.append(arr[i])
                    else:
                        consec = 1
                        cur_seq = [arr[i]]
                    if consec >= 5:
                        best_seq = cur_seq[-5:]
                        break
            return best_seq  # may be empty

        # Determine used Cards per hand type
        if hand_name == "Straight Flush":
            # find suit with >=5 then detect straight inside that suit
            for suit, cards in by_suit.items():
                if len(cards) >= 5:
                    suit_ranks = [c.rank.value for c in cards]
                    seq = find_straight_ranks(suit_ranks)
                    if seq:
                        # pick the Cards matching those ranks and suit
                        for rv in seq:
                            # map low-Ace (1) back to 14 if needed
                            pick_val = 14 if rv == 1 and not any(c.rank.value == 1 for c in cards) else rv
                            # find card with that rank value (prefer exact match)
                            for c in cards:
                                if c.rank.value == pick_val or (rv == 1 and c.rank.value == 14):
                                    used_cards.append(c)
                                    break
                        break

        elif hand_name == "Four of a Kind":
            four_rank = None
            for rv, lst in by_rank.items():
                if len(lst) >= 4:
                    if four_rank is None or rv > four_rank:
                        four_rank = rv
            if four_rank:
                used_cards = by_rank[four_rank][:4]

        elif hand_name == "Full House":
            three_rank = None
            pair_rank = None
            for rv in sorted(by_rank.keys(), reverse=True):
                if len(by_rank[rv]) >= 3 and three_rank is None:
                    three_rank = rv
            for rv in sorted(by_rank.keys(), reverse=True):
                if rv != three_rank and len(by_rank[rv]) >= 2:
                    pair_rank = rv
                    break
            if three_rank and pair_rank:
                used_cards = by_rank[three_rank][:3] + by_rank[pair_rank][:2]
            else:
                # fallback: if multiple triples exist, use highest triple + next triple (as pair)
                triples = [rv for rv, lst in by_rank.items() if len(lst) >= 3]
                if len(triples) >= 2:
                    t_sorted = sorted(triples, reverse=True)
                    used_cards = by_rank[t_sorted[0]][:3] + by_rank[t_sorted[1]][:2]

        elif hand_name == "Flush":
            flush_suit = None
            for suit, lst in by_suit.items():
                if len(lst) >= 5:
                    flush_suit = suit
                    break
            if flush_suit:
                # pick top 5 highest rank Cards of that suit
                cards_sorted = sorted(by_suit[flush_suit], key=lambda c: c.rank.value, reverse=True)
                used_cards = cards_sorted[:5]

        elif hand_name == "Straight":
            seq = find_straight_ranks([c.rank.value for c in sel])
            if seq:
                # for each rank in seq pick one available card with that rank (prefer highest suit not important)
                for rv in seq:
                    pick_val = 14 if rv == 1 and any(c.rank.value == 14 for c in sel) else rv
                    for c in sel:
                        if c.rank.value == pick_val or (rv == 1 and c.rank.value == 14):
                            used_cards.append(c)
                            break

        elif hand_name == "Three of a Kind":
            three_rank = None
            for rv in sorted(by_rank.keys(), reverse=True):
                if len(by_rank[rv]) >= 3:
                    three_rank = rv
                    break
            if three_rank:
                used_cards = by_rank[three_rank][:3]

        elif hand_name == "Two Pair":
            pairs = [rv for rv, lst in by_rank.items() if len(lst) >= 2]
            if pairs:
                top_pairs = sorted(pairs, reverse=True)[:2]
                for rv in top_pairs:
                    used_cards += by_rank[rv][:2]

        elif hand_name == "One Pair":
            pair_rank = None
            for rv in sorted(by_rank.keys(), reverse=True):
                if len(by_rank[rv]) >= 2:
                    pair_rank = rv
                    break
            if pair_rank:
                used_cards = by_rank[pair_rank][:2]

        else:  # High Card or fallback
            # pick single highest card
            best = max(sel, key=lambda c: c.rank.value)
            used_cards = [best]

        # Sum chips of only the used Cards
        card_chips_sum = 0
        for c in used_cards:
            card_chips_sum += c.chips

        # total chips for display = base hand value + sum of used Cards' chips
        total_chips = hand_chips + card_chips_sum

        # ------------------- Apply Joker effects -------------------
        owned = set(self.playerJokers)
        # TODO (TASK 5.2): Let the Joker mayhem begin! Implement each Joker’s effect using the Joker table as reference.
        #   Follow this structure for consistency:
        #   if "joker card name" in owned:
        #       # Apply that Joker’s effect
        #       self.activated_jokers.add("joker card name")
        #   The last line ensures the Joker is visibly active and its effects are properly applied.

        procrastinate = False

        # commit modified player multiplier and chips
        self.playerInfo.playerMultiplier = hand_mult
        self.playerInfo.playerChips = total_chips
        self.playerInfo.curHandOfPlayer = hand_name
        self.playerInfo.curHandText = self.playerInfo.textFont1.render(self.playerInfo.curHandOfPlayer, False, 'white')

        # compute amount that will be added to round when timer expires
        added_to_round = total_chips * hand_mult
        # Procrastination doubles the final hand's addition
        if 'procrastinate' in locals() and procrastinate:
            added_to_round *= 2
        self.pending_round_add = added_to_round  # defer actual addition until timer ends

        # prepare on-screen feedback
        self.playedHandTextSurface = self.playerInfo.textFont1.render(hand_name, True, 'yellow')
        score_breakdown_text = f"(Hand: {hand_chips} + Cards: {card_chips_sum}) Chips | x{hand_mult} Mult -> +{added_to_round}"
        self.scoreBreakdownTextSurface = self.playerInfo.textFont2.render(score_breakdown_text, True, 'white')

        self.playHandStartTime = pygame.time.get_ticks()
        self.playHandActive = True
        self.cardsSelectedRect.clear()

        start_x, start_y, spacing = 20, 20, 95
        for i, card in enumerate(self.cardsSelectedList):
            w, h = card.scaled_image.get_width(), card.scaled_image.get_height()
            self.cardsSelectedRect[card] = pygame.Rect(start_x + i * spacing, start_y, w, h)

    # TODO (TASK 4) - The function should remove one selected card from the player's hand at a time, calling itself
    #   again after each removal until no selected cards remain (base case). Once all cards have been
    #   discarded, draw new cards to refill the hand back to 8 cards. Use helper functions but AVOID using
    #   iterations (no for/while loops) — the recursion itself must handle repetition. After the
    #   recursion finishes, reset card selections, clear any display text or tracking lists, and
    #   update the visual layout of the player's hand.
    def discardCards(self, removeFromHand: bool):

        # ---------------- BASE CASE ----------------
        # No more selected cards to remove -> refill hand and reset UI state
        if len(self.cardsSelectedList) == 0:

            # Recursively draw cards until the hand has 8 or the deck is empty
            def refill_to_eight():
                if len(self.hand) >= 8:
                    return
                if len(self.deck) == 0:
                    return

                drawn = State.deckManager.dealCards(self.deck, 1)

                # dealCards usually returns a list
                if isinstance(drawn, list):
                    if len(drawn) > 0:
                        self.hand.append(drawn[0])
                else:
                    # fallback just in case
                    self.hand.append(drawn)

                refill_to_eight()

            refill_to_eight()

            # Reset selections and any related display state
            self.cardsSelectedList.clear()
            self.cardsSelectedRect.clear()

            # Clear any lingering played-hand UI (safe for both manual discard & post-play cleanup)
            self.playedHandName = ""
            self.playedHandTextSurface = None
            self.scoreBreakdownTextSurface = None
            self.playerInfo.curHandOfPlayer = ""
            self.playerInfo.curHandText = self.playerInfo.textFont1.render("", False, 'white')

            # Update visuals
            self.updateCards(400, 520, self.cards, self.hand, scale=1.2)
            return

        # ---------------- RECURSIVE STEP ----------------
        # Remove exactly ONE selected card, then recurse
        card = self.cardsSelectedList[0]

        # Deselect the card
        card.isSelected = False

        # Remove from selected list first
        self.cardsSelectedList.pop(0)

        # If we are truly discarding from hand:
        if removeFromHand:
            if card in self.hand:
                self.hand.remove(card)
            self.used.append(card)

        # Recurse to discard the next selected card
        self.discardCards(removeFromHand)
