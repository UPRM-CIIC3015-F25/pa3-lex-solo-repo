import pygame
import random
import os
from Cards.Planets import PLANETS, PlanetCard
from Cards.Jokers import Jokers
from States.GameState import HAND_SCORES
from States.Core.StateClass import State

class ShopState(State):

    def __init__(self, nextState: str = "", game_state=None):
        super().__init__(nextState)
        self.game_state = game_state
        self.playerInfo = self.game_state.playerInfo

        # Background snapshot taken when entering the shop
        self.background = State.screenshot

        # --- CRT overlay ---
        self.tvOverlay_raw = pygame.image.load('Graphics/backgrounds/CRT.png').convert_alpha()
        self.buy_sound = pygame.mixer.Sound("Graphics/Sounds/buySFX.wav")
        self.buy_sound.set_volume(1.0)
        self.tvOverlay = pygame.transform.scale(self.tvOverlay_raw, (1300, 750))
        self.tvOverlay.set_alpha(160)

        # --- main shop surface ---
        self.shopSurface = pygame.Surface((750, 600), pygame.SRCALPHA)
        self.shopSurface.fill((30, 30, 30, 255))

        # === Buttons (left column) ===
        self.skipbuttondisp = pygame.Surface((200, 90), pygame.SRCALPHA)
        self.skipbuttondisp_rect = pygame.Rect(25, 25, 200, 90)

        self.rerollbuttondisp = pygame.Surface((200, 70), pygame.SRCALPHA)
        self.rerollbuttondisp_rect = pygame.Rect(25, 135, 200, 70)

        self.shopFont = pygame.font.Font('graphics/text/m6x11.ttf', 30)
        self.smallFont = pygame.font.Font('graphics/text/m6x11.ttf', 20)
        # Position where self.shopSurface is blitted to the main screen
        self.shopPos = (350, 250)

        # --- State fields ---
        self.joker_for_sell = None   # (joker_obj, screen_rect)
        self.sell_rect = None        # screen-space sell button rect
        self.joker_for_buy = None    # (joker_obj_or_planet, screen_rect)
        self.buy_rect = None         # screen-space buy button rect
        self.shop_random_joker_rects = []  # list[pygame.Rect] in screen coords

        self.selected_info = None
        self.planet_cards = []

        # load planet art and initialize offers
        self.loadPlanets()
        if self.planet_cards:
            self.selected_planet = random.choice(self.planet_cards)
        else:
            self.selected_planet = None
        self.shop_random_jokers = []
        self.removed_offers = set()
        self.pickTwoRandomJokers()

    # ---------- Load planet art ----------
    def loadPlanets(self):
        folder = "Graphics/cards/Planets"
        self.planet_cards = []
        if not os.path.exists(folder):
            print("[ERROR] Planet folder not found:", folder)
            return
        for file in os.listdir(folder):
            if file.startswith("Planet") and file.endswith(".png"):
                name = os.path.splitext(file)[0]
                image = pygame.image.load(os.path.join(folder, file)).convert_alpha()
                key = name[6:]
                # Attach image back into PLANETS and keep reference
                if key in PLANETS:
                    PLANETS[key].image = image
                    self.planet_cards.append(PLANETS[key])

    # ---------- Descriptions ----------
    def _pretty_joker_description(self, joker_obj):
        desc_map = {
            "The Joker": "Increase the hand multiplier by +4.",
            "Michael Myers": "Add a random multiplier between 0 and 23.",
            "Fibonacci": "For each Ace/2/3/5/8 played, add +8 to the multiplier.",
            "Gauntlet": "Grant +250 chips but reduce remaining hands by 2.",
            "Ogre": "Add +3 to the multiplier for each joker you own.",
            "StrawHat": "Grant +100 chips, then -5 per hand already played this round.",
            "Hog Rider": "If the played hand is a Straight, add +100 chips.",
            "? Block": "If the played hand used exactly 4 cards, add +4 chips.",
            "Hogwarts": "Each Ace played grants +4 multiplier and +20 chips.",
            "802": "If this is the last hand of the round, double the final gain.",
        }
        
        return desc_map.get(getattr(joker_obj, 'name', ''), "No description available.")

    # TODO (TASK 6.2): Implement the HAND_SCORES dictionary to define all poker hand types and their base stats.
    #   Each key should be the name of a hand (e.g., "Two Pair", "Straight"), and each value should be a dictionary
    #   containing its "chips", "multiplier", and "level" fields.
    #   Remember: the Sun upgrades all hands, while other planets upgrade only their specific one.
    def activatePlanet(self, planet):
        if planet is None:
            return

        # Sun affects all hands
        if planet.name == "Sun":
            for hand_name in HAND_SCORES:
                HAND_SCORES[hand_name]["chips"] += planet.chips
                HAND_SCORES[hand_name]["multiplier"] += planet.mult
                HAND_SCORES[hand_name]["level"] += 1
            planet.isActive = True
            return

        # Other planets affect one specific hand
        for hand_name, stats in HAND_SCORES.items():
            # safer matching (case-insensitive)
            if hand_name.lower() in planet.description.lower():
                stats["chips"] += planet.chips
                stats["multiplier"] += planet.mult
                stats["level"] += 1
                planet.isActive = True
                break

    # ---------- Helpers ----------
    def _wrap_lines(self, text, font, max_width):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # ----- Info panel -------
    def _draw_bottom_info_panel(self):
        panel = pygame.Rect(25, 230, 700, 160)
        pad = 16
        inner = panel.inflate(-2 * pad, -2 * pad)
        pygame.draw.rect(self.shopSurface, (70, 70, 70), panel, width=2, border_radius=8)

        if not self.selected_info:
            hint = "Click a Joker or Planet to see details here."
            hint_surf = self.smallFont.render(hint, True, (160, 160, 160))
            self.shopSurface.blit(hint_surf, (inner.x, inner.y))
            return

        name = self.selected_info['name']
        desc = self.selected_info['desc']
        price = self.selected_info.get('price', None)

        title = self.shopFont.render(name, True, (255, 255, 255))
        self.shopSurface.blit(title, (inner.x, inner.y))

        lines = self._wrap_lines(desc, self.smallFont, inner.width)
        y = inner.y + title.get_height() + 8
        for line in lines:
            txt = self.smallFont.render(line, True, (220, 220, 220))
            self.shopSurface.blit(txt, (inner.x, y))
            y += txt.get_height() + 4

        # Price + Buy button only when the selected item is a shop offer
        if price is not None and self.selected_info.get('can_buy', False):
            price_txt = self.smallFont.render(f"Price: {price}$", True, (255, 215, 0))
            self.shopSurface.blit(price_txt, (inner.x, y + 10))

            buy_w, buy_h = 120, 45
            buy_x, buy_y = inner.right - buy_w - 10, inner.y + 20
            local_buy_rect = pygame.Rect(buy_x, buy_y, buy_w, buy_h)
            pygame.draw.rect(self.shopSurface, (200, 150, 0), local_buy_rect, border_radius=8)
            text = self.shopFont.render("Buy", True, (255, 255, 255))
            text_rect = text.get_rect(center=local_buy_rect.center)
            self.shopSurface.blit(text, text_rect)
            self.buy_rect = local_buy_rect.move(self.shopPos[0], self.shopPos[1])
        else:
            self.buy_rect = None

    # ---------- Main loop ----------
    def update(self):
        self.draw()

    def draw(self):
        mousePos = pygame.mouse.get_pos()
        shopSurfacePos = mousePos[0] - self.shopPos[0], mousePos[1] - self.shopPos[1]
        # If mouse is over skip/reroll buttons, change their color
        if self.skipbuttondisp_rect.collidepoint(shopSurfacePos):
            skip_color = (255, 100, 100)
        else:
            skip_color = (250, 50, 50)
        # If mouse is over reroll button, change its color
        if self.rerollbuttondisp_rect.collidepoint(shopSurfacePos):
            reroll_color = (70, 200, 100)
        else:
            reroll_color = (50, 160, 80)
        #--- Draw shop UI ---
        self.skipbuttondisp.fill(skip_color)
        self.rerollbuttondisp.fill(reroll_color)
        self.shopSurface.fill((30, 30, 30, 255))

        self.shopSurface.blit(self.skipbuttondisp, (25, 25))
        self.shopSurface.blit(self.rerollbuttondisp, (25, 135))

        next_text = self.shopFont.render("Next Round", True, (255, 255, 255))
        next_rect = next_text.get_rect(center=self.skipbuttondisp_rect.center)
        self.shopSurface.blit(next_text, next_rect)

        reroll_text = self.shopFont.render("Reroll (3$)", True, (255, 255, 255))
        reroll_rect = reroll_text.get_rect(center=self.rerollbuttondisp_rect.center)
        self.shopSurface.blit(reroll_text, reroll_rect)

        # Draw shop offers and info panel
        self.drawRandomJokers()
        self._draw_bottom_info_panel()

        # Render background and UI
        self.screen.blit(self.background, (0, 0))
        self.playerInfo.drawbuttons()
        self.screen.blit(self.playerInfo.leftRectSurface, self.playerInfo.leftRect.topleft)
        self.screen.blit(self.shopSurface, self.shopPos)

        # Apply TV overlay for this state
        self.screen.blit(self.tvOverlay, (0, 0))

        # Draw player's jokers above the shop surface (drawn after overlay so they are not affected)
        if self.game_state is not None:
            jc = self.game_state.jokerContainer
            if jc:
                # Draw outer rectangle exactly matching jokerContainer
                outer = jc.copy()
                pygame.draw.rect(self.screen, (0, 0, 0), outer)

                # Inner rectangle inset by 2px on all sides (keep minimum size)
                inner_x = jc.x + 2
                inner_y = jc.y + 2
                inner_w = jc.width - 4
                inner_h = jc.height - 4
                if inner_w < 0:
                    inner_w = 0
                if inner_h < 0:
                    inner_h = 0
                inner = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
                pygame.draw.rect(self.screen, (70, 70, 70), inner)
            # draw jokers on top so they remain unaffected by the overlay
            self.game_state.drawJokers()

        # Draw sell confirmation (if any)
        self.drawSell()

    # ---------- Draw cards ----------
    def drawRandomJokers(self):
        pos_y = 80
        start_x = 260
        spacing = 180
        self.shop_random_joker_rects = []

        display_cards = list(self.shop_random_jokers)
        for i, card in enumerate(display_cards):
            # card can be a tuple (name, image), a PlanetCard, or a Jokers instance
            img = None
            if isinstance(card, tuple):
                img = card[1]
            elif isinstance(card, PlanetCard) or isinstance(card, Jokers):
                img = card.image
            else:
                # unknown type; skip
                continue
            if img is None:
                continue

            h = 140
            w = int(img.get_width() * (h / img.get_height()))
            scaled = pygame.transform.scale(img, (w, h))
            pos_x = start_x + i * spacing
            self.shopSurface.blit(scaled, (pos_x, pos_y))

            rect = pygame.Rect(self.shopPos[0] + pos_x, self.shopPos[1] + pos_y, w, h)
            self.shop_random_joker_rects.append(rect)
    #---- Sell button -----
    def drawSell(self):
        if not self.joker_for_sell:
            self.sell_rect = None
            return

        joker_obj, joker_rect = self.joker_for_sell
        text = f"Sell : {joker_obj.sellPrice()}$"
        txt_surf = self.smallFont.render(text, True, (255, 255, 255))
        pad_x, pad_y = 10, 6
        box_w = txt_surf.get_width() + pad_x * 2
        box_h = txt_surf.get_height() + pad_y * 2
        box_x = joker_rect.centerx - box_w // 2
        box_y = joker_rect.bottom + 6
        self.sell_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 200, 30), self.sell_rect, border_radius=6)
        self.screen.blit(txt_surf, (box_x + pad_x, box_y + pad_y))

    # ---------- Pick random Jokers ----------
    def pickTwoRandomJokers(self):
        # If no valid game_state, only offer the planet
        if self.game_state is None:
            p = self.selected_planet
            if p:
                self.shop_random_jokers = [p]
            else:
                self.shop_random_jokers = []
            return

        candidates = []
        for j in self.game_state.jokerDeck:
            if j.name in self.game_state.playerJokers:
                continue
            if j.name == "_":
                continue
            if j.name in self.removed_offers:
                continue
            candidates.append(j)
        p = self.selected_planet
        picks = []
        if len(candidates) >= 2:
            picks = random.sample(candidates, 2)
        elif len(candidates) == 1:
            picks = [candidates[0]]
        else:
            picks = []

        # append planet if available
        if p:
            self.shop_random_jokers = picks + [p]
        else:
            self.shop_random_jokers = picks

    # ---------- Input ----------
    def userInput(self, events):
        if events.type == pygame.MOUSEBUTTONDOWN and events.button == 1:
            mousePos = pygame.mouse.get_pos()
            shopSurfacePos = mousePos[0] - self.shopPos[0], mousePos[1] - self.shopPos[1]

            # Next Round
            if self.skipbuttondisp_rect.collidepoint(shopSurfacePos):
                self.nextState = "LevelSelectState"
                self.isFinished = True
                return

            # Reroll
            if self.rerollbuttondisp_rect.collidepoint(shopSurfacePos):
                if self.playerInfo.playerMoney >= 3:
                    self.playerInfo.playerMoney -= 3
                    self.pickTwoRandomJokers()
                    if self.planet_cards:
                        self.selected_planet = random.choice(self.planet_cards)
                    else:
                        self.selected_planet = None
                    print("[SHOP] Rerolled new Jokers and Planet.")
                else:
                    print("[SHOP] Not enough money to reroll.")
                return

            # Buy / Sell
            if self.sell_rect and self.sell_rect.collidepoint(mousePos):
                if not self.joker_for_sell or not isinstance(self.joker_for_sell, tuple) or len(self.joker_for_sell) < 1:
                    print("[SHOP] sell clicked but no joker selected")
                    self.sell_rect = None
                    self.selected_info = None
                    return
                joker_obj, _ = self.joker_for_sell
                if joker_obj.name in self.game_state.playerJokers:
                    self.game_state.playerJokers.remove(joker_obj.name)
                else:
                    print(f"[SHOP] sell: {joker_obj.name} not in playerJokers")
                self.playerInfo.playerMoney += joker_obj.sellPrice()
                self.buy_sound.play()
                if joker_obj is not None and joker_obj.name in self.removed_offers:
                    self.removed_offers.discard(joker_obj.name)
                self.joker_for_sell = None
                self.selected_info = None
                return

            if self.buy_rect and self.buy_rect.collidepoint(mousePos):
                print("[SHOP] Attempting to buy selected card...")
                # If selection object is missing or stale, try to recover from selected_info
                if not self.joker_for_buy or not isinstance(self.joker_for_buy, tuple) or len(self.joker_for_buy) < 1:
                    recovered = None
                    if self.selected_info and self.selected_info.get('can_buy'):
                        target_name = self.selected_info.get('name')
                        # search current offers for a matching name
                        for i, offer in enumerate(self.shop_random_jokers):
                            if isinstance(offer, PlanetCard) or isinstance(offer, Jokers):
                                if offer.name == target_name:
                                    rect = self.shop_random_joker_rects[i] if i < len(self.shop_random_joker_rects) else None
                                    recovered = (offer, rect)
                                    break
                            elif isinstance(offer, tuple):
                                # tuple form (name, image)
                                if offer[0] == target_name:
                                    rect = self.shop_random_joker_rects[i] if i < len(self.shop_random_joker_rects) else None
                                    recovered = (offer, rect)
                                    break
                    if recovered is None:
                        print("[SHOP] buy clicked but no offer selected (stale state)")
                        self.buy_rect = None
                        self.selected_info = None
                        return
                    self.joker_for_buy = recovered
                joker_obj, _ = self.joker_for_buy
                if joker_obj is not None:
                    price = joker_obj.price
                else:
                    price = None
                if price is None or price < 4 or price == 12:
                    if price:
                        self.playerInfo.playerMoney -= price
                        self.buy_sound.play()
                    if joker_obj in self.shop_random_jokers:
                        self.shop_random_jokers.remove(joker_obj)
                    else:
                        print(f"[SHOP] buy: {joker_obj.name} not present when activating")
                    self.activatePlanet(joker_obj)
                    if joker_obj is not None and joker_obj.name:
                        self.removed_offers.add(joker_obj.name)
                    
                else:
                    if self.playerInfo.playerMoney >= price and len(self.game_state.playerJokers) < 2:
                        self.game_state.playerJokers.append(joker_obj.name)
                        self.playerInfo.playerMoney -= price
                        if joker_obj in self.shop_random_jokers:
                            self.shop_random_jokers.remove(joker_obj)
                        else:
                            print(f"[SHOP] buy: purchased {joker_obj.name} not found in offers")
                            self.buy_sound.play()
                        # play buy sound for successful joker purchase
                        self.buy_sound.play()
                        # prevent this joker from being re-offered this session
                        if joker_obj is not None and joker_obj.name:
                            self.removed_offers.add(joker_obj.name)
                        # Do not refill offers immediately after purchase.
                    else:
                        print(f"[SHOP] buy: cannot afford or inventory full: price={price}, money={self.playerInfo.playerMoney}, owned={len(self.game_state.playerJokers)}")
                self.joker_for_buy = None
                self.buy_rect = None
                self.selected_info = None
                return

            # Clear temporary selections; we'll set a new selection below
            self.joker_for_sell = None
            self.joker_for_buy = None

            # Owned jokers: check positions rendered by GameState
            if self.game_state is not None:
                if not self.game_state.jokers:
                    self.game_state.drawJokers()
                for joker_obj, joker_rect in self.game_state.jokers.items():
                    if joker_rect.collidepoint(mousePos):
                        desc_text = self._pretty_joker_description(joker_obj)
                        if joker_obj is not None:
                            price = joker_obj.price
                        else:
                            price = None
                        self.joker_for_sell = (joker_obj, joker_rect)
                        self.selected_info = {'name': joker_obj.name, 'desc': desc_text, 'price': price, 'can_buy': False}
                        return

            # Shop offers
            for idx, rect in enumerate(self.shop_random_joker_rects):
                if rect.collidepoint(mousePos):
                    if idx >= len(self.shop_random_jokers):
                        print(f"[SHOP] click: rect index {idx} out of bounds for offers")
                        return
                    joker_obj = self.shop_random_jokers[idx]
                    # If the clicked offer is a PlanetCard, use its own description
                    if isinstance(joker_obj, PlanetCard):
                        desc_text = joker_obj.description
                        price = joker_obj.price
                        name = joker_obj.name
                    else:
                        desc_text = self._pretty_joker_description(joker_obj)
                        if joker_obj is not None:
                            price = joker_obj.price
                        else:
                            price = None
                        if joker_obj is not None:
                            name = joker_obj.name
                        else:
                            name = ''

                    self.joker_for_buy = (joker_obj, rect)
                    self.selected_info = {'name': name, 'desc': desc_text, 'price': price, 'can_buy': True}
                    return
