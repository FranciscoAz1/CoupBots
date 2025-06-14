from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag
from .game.core import *
from .player import InformedPlayer
import random
from loguru import logger


# This class is used to implement your bot.
# You are free to edit and delete this class.
class CoupBot(InformedPlayer):
    """
    CoopBot player class.
    
    Attributes:
        alive (bool): Flag for whether the player is alive or not.
        checkout (SimpleQueue): Queue used to send messages to the server. The queue is thread-safe and can be used by multiple threads.
        coins (int): Number of coins the player has.
        deck (list[str]): List of cards in the player's deck.
        exchange_cards (list[str]): List of cards to exchange with the deck.
        id (str): Player ID.
        is_root (bool): Flag for whether the player is the root player or not.
        msg (GameMessage): Message to be sent to the server.
        players (dict[str, PlayerSim]): Dictionary of players in the game.
        possible_messages (list[str]): List of possible messages the player can send.
        history (list[GameMessage]): History of received messages.
        ready (bool): Flag for whether the player is ready or not.
        replied (bool): Flag for whether the player has replied to the last message or not.
        state (PlayerState): State of the player.
        tag (Tag): Tag for the player. Used to identify the player in the game.
        term (Terminal): Terminal used to write messages manually.
        terminate_after_death (bool): Flag for whether the player should terminate after its own death.
        turn (bool): Flag for whether it is the player's turn or not.
    
    Methods:
        choose_message(): Choose a message to send to the server based on the current state of the game.
        
    """

    def __init__(self):
        super().__init__()

    def choose_message(self) -> None:
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        # Implement your bot here
        # Example: choose a random message from possible messages
        self.msg = GameMessage(random.choice(self.possible_messages))

class RandomBot(InformedPlayer):
    """RandomBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random

class HonestBot(InformedPlayer):
    """HonestBot player class."""

    def __init__(self):
        super().__init__()

    def pick_random(self, possible_messages: list[str]):
        """Pick a random message from the possible messages."""
        if len(possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        self.msg = GameMessage(random.choice(possible_messages))

    def choose_message(self):
        current_msg = self.history[-1]
        previous_msg = self.history[-2]
        if current_msg.ID1 is None or len(self.players) == 0:
            self.pick_random(self.possible_messages)
            return
        
        choices: list[str] = []
        
        # Update previous player deck in case of a change in their deck
        if self.state == PlayerState.R_MY_TURN or self.state == PlayerState.R_OTHER_TURN:
            if previous_msg.command == ACT and previous_msg.action == EXCHANGE:
                # the player has exchanged cards successfully
                if previous_msg.ID1 in self.players:
                    self.players[previous_msg.ID1].deck = []
                else:
                    logger.warning(f"Player {previous_msg.ID1} not found in players list.")
                    
        elif self.state == PlayerState.R_LOSE or self.state == PlayerState.R_SHOW:
            if previous_msg.command == SHOW or previous_msg.command == LOSE:
                # the card that was shown or lost is no longer in the player's deck
                if previous_msg.ID1 in self.players:
                    if previous_msg.card1 in self.players[previous_msg.ID1].deck:
                        self.players[previous_msg.ID1].deck.remove(previous_msg.card1)
                else:
                    logger.warning(f"Player {previous_msg.ID1} not found in players list.")
        
        # Believe any player that claims to have a card, 
        # if at least one of their cards is unknown
        if self.state == PlayerState.R_MY_TURN:
            if self.coins < COUP_COINS_THRESHOLD:
                
                choices.append(game_proto.ACT(self.id, INCOME))
                choices.append(game_proto.ACT(self.id, FOREIGN_AID))
                if DUKE in self.deck:
                    choices.append(game_proto.ACT(self.id, TAX))
                if AMBASSADOR in self.deck:
                    choices.append(game_proto.ACT(self.id, EXCHANGE))
                
                if CAPTAIN in self.deck:
                    for target in self.players.values():
                        if target != self and target.alive:
                            choices.append(game_proto.ACT(self.id, STEAL, target.id))
                
                if ASSASSIN in self.deck and self.coins >= ASSASSINATION_COST:
                    for target in self.players.values():
                        if target != self and target.alive:
                            choices.append(game_proto.ACT(self.id, ASSASSINATE, target.id))
            
            if self.coins >= COUP_COST:
                for target in self.players.values():
                    if target != self and target.alive:
                        choices.append(game_proto.ACT(self.id, COUP, target.id))
                            
        elif self.state == PlayerState.R_FAID:
            choices.append(game_proto.OK())
            if DUKE in self.deck:
                choices.append(game_proto.BLOCK(self.id, DUKE))

        elif self.state == PlayerState.R_EXCHANGE:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(AMBASSADOR)
            elif AMBASSADOR not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
            
        elif self.state == PlayerState.R_TAX:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(DUKE)
            elif DUKE not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_ASSASS_ME:
            choices.append(game_proto.OK())
            if CONTESSA in self.deck:
                choices.append(game_proto.BLOCK(self.id, CONTESSA))
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(ASSASSIN)
            elif ASSASSIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_ASSASS:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(ASSASSIN)
            elif ASSASSIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_STEAL_ME:
            choices.append(game_proto.OK())
            if CAPTAIN in self.deck:
                choices.append(game_proto.BLOCK(self.id, CAPTAIN))
            if AMBASSADOR in self.deck:
                choices.append(game_proto.BLOCK(self.id, AMBASSADOR))
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CAPTAIN)
            elif CAPTAIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_STEAL:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CAPTAIN)
            elif CAPTAIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))

        elif self.state == PlayerState.R_BLOCK_FAID:
            choices.append(game_proto.OK())
            if DUKE in self.deck:
                choices.append(game_proto.BLOCK(self.id, DUKE))
                
        elif self.state == PlayerState.R_BLOCK_ASSASS:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CONTESSA)
            elif CONTESSA not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_STEAL_B:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(AMBASSADOR)
            elif AMBASSADOR not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_STEAL_C:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CAPTAIN)
            elif CAPTAIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
        
        else:
            self.pick_random(self.possible_messages)
            return
        
        self.pick_random(choices)
        
class TestBot(InformedPlayer):    
    """TestBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random
        # self.msg = GameMessage(self.possible_messages[-1]) # choose last
        
        # test with priority choices
        msgs: list[GameMessage] = []
        for m in self.possible_messages:
            msgs.append(GameMessage(m))
        for m in msgs:
            if m.command == ACT and m.action == ASSASSINATE:
                self.msg = m
                return
        for m in msgs:
            if m.command == ACT and m.action == INCOME:
                self.msg = m
                return
        for m in msgs:
            if m.command == BLOCK and len(self.deck) == 1:
                self.msg = m
                return

import ollama
class AICoupBot(InformedPlayer):
    """TestBot player class."""

    def __init__(self):
        super().__init__()
        try:
            self.ollama_client = ollama.Client(host="http://localhost:11434")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server: {str(e)}")
            raise RuntimeError("Ollama server is not running or not reachable.")

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        # TODO: Implement a AI BOT here
        # The AI bot should get context from the game history and choose a message, from the self.possible_messages
        # Use ollama that is running on a ollama server
        ollama_client = self.ollama_client
        if not ollama_client:
            logger.error("Ollama client is not initialized.")
            return
        # Get messages from game history
        messages = []
        # TODO: create a system prompt signaling this is an AI bot playing the game coup
        system_prompt = f"""You are an AI bot playing the card game Coup, your are Player {self.id} in this game.

Game rules:
- Each player starts with 2 character cards and 2 coins
- The game is about deception, bluffing, and strategy
- Actions include: Income (1 coin), Foreign Aid (2 coins), Coup (7 coins, eliminate opponent's card), Tax (3 coins, requires Duke), Steal (2 coins from opponent, requires Captain), Assassinate (3 coins, eliminate opponent's card, requires Assassin), Exchange (swap cards, requires Ambassador)
- Players can block or challenge actions
- Characters: Duke (blocks Foreign Aid, takes Tax), Assassin (Assassinate), Captain (Steal, blocks Steal), Ambassador (Exchange, blocks Steal), Contessa (blocks Assassination)

Your task:
1. Analyze the game state and history
2. Choose ONE message from the possible_messages list
3. Return ONLY the exact message text from the possible_messages list
4. Consider your cards, coins, and opponent actions when deciding

DO NOT create new messages or modify the existing ones. ONLY select from the provided list."""
        messages.append({"role": "system", "content": system_prompt})
        
        if self.history:
            messages.append({"role": "system", "content": f"The following is the game history, use it to predict the best decision, where  Player {self.id} wins the game."})

        # Convert game history to chat format - filter out OK messages first, then take the most recent 20 messages
        filtered_history = [msg for msg in self.history if msg.command != OK]
        recent_history = filtered_history[-20:] if len(filtered_history) > 20 else filtered_history
        
        for game_msg in recent_history:
            # Humanize the game message for better understanding
            if game_msg.command == ACT:
                content = f"{game_msg.ID1} performed action: {game_msg.action}"
            elif game_msg.command == BLOCK:
                content = f"{game_msg.ID1} blocked action: {game_msg.action}"
            elif game_msg.command == CHAL:
                content = f"{game_msg.ID1} challenged action: {game_msg.action}"
            elif game_msg.command == SHOW:
                content = f"{game_msg.ID1} showed card: {game_msg.card1}"
            elif game_msg.command == LOSE:
                content = f"{game_msg.ID1} lost card: {game_msg.card1}"
            else:
                content = str(game_msg)
            messages.append({"role": "system", "content": content})

        # Humanize possible messages for better AI understanding
        def humanize_message(msg_str):
            """Convert raw message strings to human-readable format"""
            try:
                parts = msg_str.split(',')
                msg_type = parts[0]
                
                if msg_type == ACT:
                    action = parts[2] if len(parts) > 2 else parts[1]
                    target = f" targeting player {parts[3]}" if len(parts) > 3 and parts[3] else ""
                    action_names = {
                        "I": "Income (gain 1 coin)",
                        "F": "Foreign Aid (gain 2 coins)",
                        "C": "Coup (pay 7 coins to eliminate opponent's card)",
                        "T": "Tax (gain 3 coins, requires Duke)",
                        "A": "Assassinate (pay 3 coins to eliminate opponent's card, requires Assassin)",
                        "S": "Steal (take 2 coins from opponent, requires Captain)",
                        "X": "Exchange (swap cards with deck, requires Ambassador)"
                    }
                    return f"Perform {action_names.get(action, action)}{target}"
                elif msg_type == BLOCK:
                    card = parts[2] if len(parts) > 2 else "card"
                    card_names = {
                        "A": "Assassin",
                        "B": "Ambassador", 
                        "C": "Captain",
                        "D": "Duke",
                        "E": "Contessa"
                    }
                    return f"Block using {card_names.get(card, card)}"
                elif msg_type == CHAL:
                    return "Challenge the current action"
                elif msg_type == OK:
                    return "Accept/Allow the action"
                elif msg_type == SHOW:
                    card = parts[2] if len(parts) > 2 else parts[1] if len(parts) > 1 else "card"
                    card_names = {"A": "Assassin", "B": "Ambassador", "C": "Captain", "D": "Duke", "E": "Contessa"}
                    return f"Show {card_names.get(card, card)} card"
                elif msg_type == LOSE:
                    card = parts[2] if len(parts) > 2 else parts[1] if len(parts) > 1 else "card"
                    card_names = {"A": "Assassin", "B": "Ambassador", "C": "Captain", "D": "Duke", "E": "Contessa"}
                    return f"Lose {card_names.get(card, card)} card"
                elif msg_type == CHOOSE:
                    return "Choose cards to keep"
                elif msg_type == KEEP:
                    return "Keep selected cards"
                else:
                    return msg_str
            except:
                return msg_str

        humanized_messages = [f"'{msg}' = {humanize_message(msg)}" for msg in self.possible_messages]
        humanized_text = "\n".join(humanized_messages)
        
        # prepare a better prompt with the possible messages, explain why each of the messages would be useful in the game of coup
        messages.append({"role": "user", "content": f"""Find the best action for you Player {self.id} to win coup from the following possible actions:

{humanized_text}

Choose the raw message (the part in quotes) that gives you the best strategic advantage. Consider:
- Your current cards: {self.deck if hasattr(self, 'deck') else 'Unknown'}
- Your coins: {self.coins if hasattr(self, 'coins') else 'Unknown'}
- The game history above
- What would help you win or eliminate opponents

Return ONLY the exact raw message string (the part in quotes)."""})

        # get the response from the ollama server
        response = ollama_client.chat(model="qwen2.5:latest", messages=messages, stream=False)

        model_response = response["message"]["content"]

        # TODO: find possible messages in model_response, and return the first one,
        def find_message_in_response(response_text, possible_messages):
            """
            Find a valid message from the possible_messages list in the model's response text.
            Returns the first valid message found, or None if no valid message is found.
            """
            # First, try to find an exact match
            for message in possible_messages:
                if message in response_text:
                    logger.info(f"Found exact message match: {message}")
                    return message
            
            # If no exact match, look for message components (ACT, BLOCK, etc.)
            # This handles cases where the model might have formatted the message differently
            for message in possible_messages:
                message_parts = message.split()
                # Check if all parts of a message appear in the response in the correct order
                if all(part in response_text for part in message_parts):
                    logger.info(f"Found partial message match: {message}")
                    return message
            
            return None
        
        selected_message = find_message_in_response(model_response, self.possible_messages)
        
        if selected_message:
            self.msg = GameMessage(selected_message)
            logger.info(f"AI selected message: {selected_message}")
            return
                # TODO: If not rechat with the model to get a valid message, try gleaning times.
        # If no valid message was found, try one more time with a more specific prompt
        if not selected_message:
            logger.warning("No valid message found in model response. Trying again with more specific prompt.")
            def retry_llm():
                retry_prompt = f"""I need you to select ONE message from this list of possible actions. 
                
    Available messages:
    {', '.join(self.possible_messages)}

    IMPORTANT: Your response should contain ONLY ONE of these exact messages. Do not add any explanation, just return the message."""
                
                try:
                    # Retry with more specific prompt
                    retry_messages = [
                        {"role": "system", "content": "You are playing the game Coup. Select exactly one message from the provided options."},
                        {"role": "user", "content": retry_prompt}
                    ]
                    
                    retry_response = ollama_client.chat(model="qwen2.5:latest", messages=retry_messages, stream=False)
                    retry_model_response = retry_response["message"]["content"]
                    
                    selected_message = find_message_in_response(retry_model_response, self.possible_messages)
                    
                    if selected_message:
                        self.msg = GameMessage(selected_message)
                        logger.info(f"AI selected message after retry: {selected_message}")
                        return
                    else:
                        logger.warning("No valid message found after retry. Using fallback strategy.")
                except Exception as e:
                    logger.error(f"Error during retry: {str(e)}")
            retry_llm()
        # Fallback to a strategic selection if AI failed to provide a valid message
        msgs = [GameMessage(m) for m in self.possible_messages]
        
        # Strategic priority-based fallback
        def priority_based_fallback():
            # 1. If we have enough coins, coup is usually the best move
            for m in msgs:
                if m.command == ACT and m.action == COUP and self.coins >= 7:
                    self.msg = m
                    logger.info("Fallback: Using COUP action")
                    return
                    
            # 2. Assassinate is powerful if we have the card
            for m in msgs:
                if m.command == ACT and m.action == ASSASSINATE and "ASSASSIN" in self.deck:
                    self.msg = m
                    logger.info("Fallback: Using ASSASSINATE action")
                    return
                    
            # 3. Block assassination if we have contessa
            for m in msgs:
                if m.command == BLOCK and "CONTESSA" in self.deck:
                    self.msg = m
                    logger.info("Fallback: Blocking with CONTESSA")
                    return
            
            # 4. Tax is good for getting coins if we have duke
            for m in msgs:
                if m.command == ACT and m.action == TAX and "DUKE" in self.deck:
                    self.msg = m
                    logger.info("Fallback: Using TAX action")
                    return
                    
            # 5. Income is a safe choice
            for m in msgs:
                if m.command == ACT and m.action == INCOME:
                    self.msg = m
                    logger.info("Fallback: Using INCOME action")
                    return
        
        priority_based_fallback()
        # Last resort: random choice
        self.msg = GameMessage(random.choice(self.possible_messages))
        logger.info(f"Fallback: Using random message: {self.msg}")
        return

