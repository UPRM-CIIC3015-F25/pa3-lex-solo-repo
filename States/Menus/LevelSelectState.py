import pygame
from Deck.DeckManager import DeckManager
from States.Core.StateClass import State
from States.Core.PlayerInfo import PlayerInfo

class LevelSelectState(State):
    def __init__(self, playerInfo: PlayerInfo = None, nextState: str = "", deckManager: DeckManager = None):
        super().__init__(nextState)
        
        #--------------------Player Info and Screenshot---------------------------
        self.playerInfo = playerInfo # PlayerInfo object
        self.bg = State.screenshot # Screenshot of the last game state
        self.deckManager = deckManager # DeckManager object

        # -------------------Load CRT Overlay-------------------------------------
        self.tvOverlay = pygame.image.load('Graphics/Backgrounds/CRT.png').convert_alpha()
        self.tvOverlay = pygame.transform.scale(self.tvOverlay, (1300, 750))
        
        # -------------------------Fonts used in the UI---------------------------
        self.font = pygame.font.Font('Graphics/Text/m6x11.ttf', 30)
        self.font2 = pygame.font.Font('Graphics/Text/m6x11.ttf', 22)
        self.font3 = pygame.font.Font('Graphics/Text/m6x11.ttf', 60)
        self.font4 = pygame.font.Font('Graphics/Text/m6x11.ttf', 40)
        
        #----------- Layout for multiple sublevel Cards ---------------------------
        self.cardWidth = 280
        self.cardHeight = 450
        self.cardSpacing = 40
        self.cardsStartX = 280
        self.cardsStartY = 150
        
        # Store card rects for each sublevel
        self.sublevelCards = []
        
        self.continueButtonRect = pygame.Rect(0, 0, 300, 80)
        self.continueButtonRect.centerx = 650
        self.continueButtonRect.centery = 650
        #-------------------------------------------------------------------------
    def update(self):
        self.draw()

    def draw(self):
        # Draw the screenshot background, if available
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((1300, 750), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw level Cards and continue button
        self.drawLevelCards()
        self.drawContinueButton()
        
        # CRT overlay effect
        self.screen.blit(self.tvOverlay, (0, 0))

    """This function handles user input for the LevelSelectState,
    when the player press CONTINUE button, it updates the player's stats.
    
    The player score resets to 0, and the target score is updated, if the next level is a
    boss level, it will reset stats according to the boss's rules."""
    
    def userInput(self, events):
    # Handle mouse click on CONTINUE button
        if events.type == pygame.MOUSEBUTTONDOWN and events.button == 1:
            mousePos = events.pos
            # Check if the continue button was clicked
            if self.continueButtonRect.collidepoint(mousePos):
                # Update level manager to reflect completed sublevel
                self.playerInfo.levelFinished = False
                
                # just helper variables to write less LOL
                lm = self.playerInfo.levelManager
                nxt = lm.next_unfinished_sublevel()

                # If there's no next sublevel, the player likely advanced past the last ante -> Win
                if nxt is None:
                    # Ensure LevelManager flagged the win and transition to GameWinState
                    lm.playerWins = True
                    self.isFinished = True
                    self.nextState = "GameWinState"
                    return

                # If there's a next sublevel, set it as current
                lm.curSubLevel = nxt

                # TODO (TASK 9.2) - Adjust player limits and reset values based on the current Boss Blind.
                #   Implement conditional logic that modifies the player's hand and discard limits depending
                #   on which boss is active.
                #   Finally, make sure to reset the player’s round score to 0 at the end of this setup.
                #   Avoid unnecessary repetition—use clear condition structure to make the logic readable.
                base_hands = 4
                base_discards = 4

                boss_name = lm.curSubLevel.bossLevel

                # Start from defaults
                hands = base_hands
                discards = base_discards

                # Apply boss-specific debuffs
                if boss_name == "The Water":
                    # No discards this blind
                    discards = 0
                elif boss_name == "The Needle":
                    # Only one hand this blind
                    hands = 1
                elif boss_name == "The Manacle":
                    # Fewer hands than normal (simulating a stricter limit)
                    hands = 3
                # Other bosses (The Mark, The House, The Hook, etc.)
                # keep the default limits.

                # Commit limits back to the player
                self.playerInfo.amountOfHands = hands
                self.playerInfo.amountOfDiscards = discards

                self.playerInfo.roundScore = 0
                
                # Set target score for the new sublevel
                self.playerInfo.score = self.playerInfo.levelManager.curSubLevel.score
                
                # Prepare for the nextState : GameState
                self.deckManager.resetDeck = True
                self.isFinished = True
                self.nextState = "GameState"
                self.buttonSound.play()

    def drawLevelCards(self):
        # Make sure there's a current level
        if self.playerInfo.levelManager.curLevel is None:
            return
        # Get current sublevel list of the player's ante
        sublevels = self.playerInfo.levelManager.curLevel
        # Clear previous card rects
        self.sublevelCards = []

        # Dict of boss with their abilities
        # TODO (TASK 9.1) - Define a dictionary called `boss_abilities` that maps each Boss Blind’s name to its special effect.
        #   Each key should be the name of a boss (e.g., "The Mark", "The Needle", etc.), and each value should describe
        #   what unique restriction or ability that boss applies during the round.
        #   This dictionary will later be used to look up and apply special effects based on which boss is active.
        boss_abilities = {
            "The Water": "Start this blind with no discards.",
            "The Mark": "All face cards (J,Q,K) are drawn face down.",
            "The House": "Your first hand of the blind is dealt face down.",
            "The Hook": "After you play a hand, 2 random unplayed cards are discarded.",
            "The Manacle": "Your maximum hand size is reduced by 1.",
            "The Needle": "You may play only one hand this blind (target is Small Blind score).",
            "The Club": "Club cards are debuffed and give no chips or mult this blind.",
            "The Goad": "Spade cards are debuffed and give no chips or mult this blind.",
        }


        # Dict of boss with their color schemes
        # key - boss name : str, value - (header color : tuple, background color : tuple)
        boss_colors = {
            "The Mark": ((120, 40, 160), (60, 30, 80)),        # purple
            "The Needle": ((180, 20, 20), (80, 20, 20)),       # crimson
            "The House": ((200, 160, 20), (100, 80, 10)),      # gold/bronze
            "The Hook": ((20, 150, 140), (10, 70, 80)),        # teal
            "The Water": ((30, 120, 200), (10, 50, 90)),       # blue
            "The Manacle": ((90, 90, 90), (40, 40, 40)),       # steel/gray
            "The Club": ((20, 120, 40), (10, 60, 30)),         # green
            "The Goad": ((70, 40, 140), (30, 20, 70)),         # indigo
        }

        #---------------------------Draw each sublevel card ---------------------------
        for i, sublevel in enumerate(sublevels):
            cardX = self.cardsStartX + i * (self.cardWidth + self.cardSpacing)
            cardY = self.cardsStartY
            
            cardSurface = pygame.Surface((self.cardWidth, self.cardHeight), pygame.SRCALPHA)
            
            cardRect = pygame.Rect(cardX, cardY, self.cardWidth, self.cardHeight)
            self.sublevelCards.append({
                'rect': cardRect,
                'sublevel': sublevel
            })
            
            # Sections of the card
            headerRect = pygame.Rect(10, 10, self.cardWidth - 20, 50)
            blindImageRect = pygame.Rect(10, 70, self.cardWidth - 20, 140)
            scoreRect = pygame.Rect(10, 220, self.cardWidth - 20, 80)
            statusRect = pygame.Rect(10, 310, self.cardWidth - 20, 60)
            
            # Header and background colors by blind type
            if sublevel.blind.name == "SMALL":
                header_color = (70, 130, 180)
                bg_color = (40, 65, 90)
            elif sublevel.blind.name == "BIG":
                header_color = (255, 140, 0)
                bg_color = (127, 70, 0)
            else:
                header_color = (128, 128, 128)
                bg_color = (64, 64, 64)

            # If this sublevel is a boss, prefer boss-specific colors
            boss_name = sublevel.bossLevel
            if boss_name:
                override = boss_colors.get(boss_name)
                if override:
                    header_color, bg_color = override
            
            pygame.draw.rect(cardSurface, bg_color, cardSurface.get_rect(), border_radius=10)
            pygame.draw.rect(cardSurface, header_color, headerRect, border_radius=10)
            pygame.draw.rect(cardSurface, (30, 30, 30), blindImageRect, border_radius=10)
            pygame.draw.rect(cardSurface, (30, 30, 30), scoreRect, border_radius=10)
            
            # Header Text
            if sublevel.bossLevel:
                headerText = self.font.render(f"BOSS: {sublevel.bossLevel.upper()}", False, (255, 255, 255))
            else:
                headerText = self.font.render(f"{sublevel.blind.name} BLIND", False, (255, 255, 255))
            headerTextRect = headerText.get_rect(center=headerRect.center)
            cardSurface.blit(headerText, headerTextRect)
            
            # Blind image
            if sublevel.image:
                scaledImage = pygame.transform.scale(sublevel.image, (140, 120))
                imageRect = scaledImage.get_rect(center=blindImageRect.center)
                cardSurface.blit(scaledImage, imageRect)
            
            # Score requirement
            scoreLabel = self.font2.render("Score at least", False, (200, 200, 200))
            scoreValue = self.font3.render(str(sublevel.score), False, (255, 0, 0))
            scoreLabelRect = scoreLabel.get_rect(centerx=scoreRect.centerx, top=scoreRect.top + 12)
            scoreValueRect = scoreValue.get_rect(centerx=scoreRect.centerx, top=scoreRect.top + 40)
            cardSurface.blit(scoreLabel, scoreLabelRect)
            cardSurface.blit(scoreValue, scoreValueRect)

            # Boss ability Text
            ability_text = None
            if sublevel.bossLevel: 
                ability_text = boss_abilities.get(sublevel.bossLevel)
            
            nextUnfinished = self.playerInfo.levelManager.next_unfinished_sublevel()
            
            if sublevel.finished:
                # COMPLETED
                statusText = self.font4.render("COMPLETED", False, (100, 255, 100))
                statusTextRect = statusText.get_rect(center=statusRect.center)
                cardSurface.blit(statusText, statusTextRect)
                
                darkOverlay = pygame.Surface((self.cardWidth, self.cardHeight), pygame.SRCALPHA)
                darkOverlay.fill((0, 0, 0, 160))
                cardSurface.blit(darkOverlay, (0, 0))
            elif nextUnfinished and nextUnfinished == sublevel:
                # ACTIVE
                statusText = self.font4.render("ACTIVE", False, (255, 200, 100))
                statusTextRect = statusText.get_rect(center=statusRect.center)
                cardSurface.blit(statusText, statusTextRect)
            else:
                # LOCKED
                statusText = self.font4.render("LOCKED", False, (150, 150, 150))
                statusTextRect = statusText.get_rect(center=statusRect.center)
                cardSurface.blit(statusText, statusTextRect)
                
                lockOverlay = pygame.Surface((self.cardWidth, self.cardHeight), pygame.SRCALPHA)
                lockOverlay.fill((0, 0, 0, 80))
                cardSurface.blit(lockOverlay, (0, 0))
            
            # Boss ability description
            if ability_text:
                abilityFont = self.font
                abilitySurf = abilityFont.render(ability_text, False, (245, 245, 245))
                # place just below the status rect
                abilityRect = abilitySurf.get_rect(centerx=scoreRect.centerx, top=statusRect.top + statusRect.height + 8)
                pad_x, pad_y = 12, 8
                bg_rect = abilityRect.inflate(pad_x * 2, pad_y * 2)
                panel = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                panel_color = (header_color[0], header_color[1], header_color[2], 200)
                panel.fill(panel_color)
                cardSurface.blit(panel, bg_rect.topleft)
                cardSurface.blit(abilitySurf, abilityRect)

            # Border by status
            if nextUnfinished and nextUnfinished == sublevel:
                borderColor = (255, 200, 100)
                borderWidth = 4
            elif sublevel.finished:
                borderColor = (100, 255, 100)
                borderWidth = 3
            else:
                borderColor = (80, 80, 80)
                borderWidth = 2
            
            pygame.draw.rect(cardSurface, borderColor, cardSurface.get_rect(), width=borderWidth, border_radius=10)
            self.screen.blit(cardSurface, (cardX, cardY))

    def drawContinueButton(self):
        #--- Draw CONTINUE Button ---
        mouse = pygame.mouse.get_pos()
        hover = self.continueButtonRect.collidepoint(mouse)
        
        if hover:
            buttonColor = (0, 139, 0)
        else:
            buttonColor = (0, 128, 0)

        pygame.draw.rect(self.screen, buttonColor, self.continueButtonRect, border_radius=10)
        
        continueText = self.font.render("CONTINUE", False, (255, 255, 255))
        continueTextRect = continueText.get_rect(center=self.continueButtonRect.center)
        self.screen.blit(continueText, continueTextRect)
