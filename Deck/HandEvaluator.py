from Cards.Card import Card, Rank

# TODO (TASK 3): Implement a function that evaluates a player's poker hand.
#   Loop through all cards in the given 'hand' list and collect their ranks and suits.
#   Use a dictionary to count how many times each rank appears to detect pairs, three of a kind, or four of a kind.
#   Sort these counts from largest to smallest. Use another dictionary to count how many times each suit appears to check
#   for a flush (5 or more cards of the same suit). Remove duplicate ranks and sort them to detect a
#   straight (5 cards in a row). Remember that the Ace (rank 14) can also count as 1 when checking for a straight.
#   If both a straight and a flush occur in the same suit, return "Straight Flush". Otherwise, use the rank counts
#   and flags to determine if the hand is: "Four of a Kind", "Full House", "Flush", "Straight", "Three of a Kind",
#   "Two Pair", "One Pair", or "High Card". Return a string with the correct hand type at the end.
def evaluate_hand(hand: list[Card]):
    if not hand:
        return "High Card"

    # Collect ranks and suits
    ranks = []
    suits = []
    for card in hand:
        # Rank is likely an Enum; use .value for numeric comparisons
        ranks.append(card.rank.value if hasattr(card.rank, "value") else int(card.rank))
        suits.append(card.suit)

    # Count ranks
    rankCounts = {}
    for r in ranks:
        rankCounts[r] = rankCounts.get(r, 0) + 1

    counts_sorted = sorted(rankCounts.values(), reverse=True)

    # Count suits (flush check)
    suitCounts = {}
    for s in suits:
        suitCounts[s] = suitCounts.get(s, 0) + 1

    is_flush = False
    flush_suit = None
    for s, c in suitCounts.items():
        if c >= 5:
            is_flush = True
            flush_suit = s
            break

    # Helper to detect straight in a list of rank values
    def has_straight(rank_list):
        unique = sorted(set(rank_list))
        # Ace-low support
        if 14 in unique:
            unique = sorted(set(unique + [1]))

        consec = 1
        for i in range(1, len(unique)):
            if unique[i] == unique[i - 1] + 1:
                consec += 1
                if consec >= 5:
                    return True
            else:
                consec = 1
        return False

    # Straight check (general)
    is_straight = has_straight(ranks)

    # Straight Flush check (must be same suit)
    is_straight_flush = False
    if is_flush:
        # gather ranks only of the flush suit
        flush_ranks = []
        for card in hand:
            if card.suit == flush_suit:
                flush_ranks.append(card.rank.value if hasattr(card.rank, "value") else int(card.rank))
        if has_straight(flush_ranks):
            is_straight_flush = True

    # Determine hand type in priority order
    if is_straight_flush:
        return "Straight Flush"

    # Four of a Kind
    if 4 in counts_sorted:
        return "Four of a Kind"

    # Full House
    has_three = 3 in counts_sorted
    pair_count = 0
    for c in counts_sorted:
        if c >= 2:
            pair_count += 1

    # Full house if we have a 3 and another 2+, or two triplets
    if has_three and (2 in counts_sorted or counts_sorted.count(3) >= 2):
        return "Full House"

    # Flush
    if is_flush:
        return "Flush"

    # Straight
    if is_straight:
        return "Straight"

    # Three of a Kind
    if has_three:
        return "Three of a Kind"

    # Two Pair
    if pair_count >= 2:
        return "Two Pair"

    # One Pair
    if 2 in counts_sorted:
        return "One Pair"

    return "High Card"
